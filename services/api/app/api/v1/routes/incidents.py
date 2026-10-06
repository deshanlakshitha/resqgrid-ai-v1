"""Incident routes: CRUD, triage, priority, recommendations."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_role, incident_scope, require_incident_access
from app.core.rate_limit import enforce_rate_limit
from app.models.user import User, UserRole
from app.models.incident import Incident
from app.models.entities import AuditAction
from app.schemas.schemas import IncidentCreate, IncidentUpdate, IncidentResponse, TriageOutput, PriorityScore
from app.services.audit_service import log_action

router = APIRouter()


@router.post("", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
async def create_incident(
    data: IncidentCreate,
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new incident report (citizen, dispatcher, or admin).

    Idempotent: clients may supply their own UUID (``data.id``) so that a
    retry after a network failure replays the same request instead of
    creating a duplicate. A replayed id returns the original incident
    with HTTP 200; an id owned by another user is rejected with 409.
    """
    await enforce_rate_limit("incident-create", str(current_user.id), 30, 60)
    incident_id = data.id or uuid.uuid4()
    # Capture identity values up front: db.rollback() below expires all ORM
    # objects in the session, so attributes must not be read after it.
    reporter_id = current_user.id
    incident = Incident(
        id=incident_id,
        title=data.title,
        description=data.description,
        incident_type=data.incident_type,
        latitude=data.latitude,
        longitude=data.longitude,
        address=data.address,
        people_at_risk=data.people_at_risk,
        vulnerable_people=data.vulnerable_people,
        injuries_reported=data.injuries_reported,
        medical_need=data.medical_need,
        reporter_id=reporter_id,
        reporter_name=data.reporter_name or current_user.full_name,
        reporter_phone=data.reporter_phone or current_user.phone,
    )
    db.add(incident)
    try:
        await db.flush()
    except IntegrityError:
        # Same client id replayed (offline retry). Return the original record.
        await db.rollback()
        existing_reporter_id = (
            await db.execute(select(Incident.reporter_id).where(Incident.id == incident_id))
        ).scalar_one_or_none()
        if existing_reporter_id is None or existing_reporter_id != reporter_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Incident id already exists")
        result = await db.execute(select(Incident).where(Incident.id == incident_id))
        response.status_code = status.HTTP_200_OK
        return result.scalar_one()
    await log_action(
        db,
        action=AuditAction.CREATE,
        entity_type="incident",
        entity_id=incident.id,
        user_id=current_user.id,
        details={"title": incident.title, "incident_type": incident.incident_type},
    )
    await db.refresh(incident)
    return incident


@router.get("", response_model=list[IncidentResponse])
async def list_incidents(
    status_filter: str | None = Query(None, alias="status"),
    severity: str | None = None,
    incident_type: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List incidents with optional filtering and pagination."""
    query = select(Incident).where(Incident.is_deleted == False, incident_scope(current_user))

    if status_filter:
        query = query.where(Incident.status == status_filter)
    if severity:
        query = query.where(Incident.severity == severity)
    if incident_type:
        query = query.where(Incident.incident_type == incident_type)

    query = query.order_by(Incident.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single incident by ID."""
    return await require_incident_access(db, incident_id, current_user)


@router.patch("/{incident_id}", response_model=IncidentResponse)
async def update_incident(
    incident_id: uuid.UUID,
    data: IncidentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.DISPATCHER, UserRole.ADMIN)),
):
    """Update an incident (dispatcher/admin only)."""
    result = await db.execute(select(Incident).where(Incident.id == incident_id, Incident.is_deleted == False))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(incident, field, value)

    await db.flush()
    await db.refresh(incident)
    return incident


@router.post("/{incident_id}/triage", response_model=TriageOutput)
async def run_triage(
    incident_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.DISPATCHER, UserRole.ADMIN)),
):
    """Run AI triage on an incident. Returns validated structured JSON."""
    from app.services.triage_service import run_ai_triage

    result = await db.execute(select(Incident).where(Incident.id == incident_id, Incident.is_deleted == False))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    triage_result = await run_ai_triage(incident)
    # Validate against schema
    ensemble_block = triage_result.pop("ensemble", None)
    validated = TriageOutput(**triage_result)

    # Update incident with triage data (including ensemble diagnostics)
    incident.triage_data = validated.model_dump()
    if ensemble_block:
        incident.triage_data["ensemble"] = ensemble_block
    incident.triage_confidence = validated.confidence
    incident.triage_reason_codes = validated.reason_codes
    incident.severity = validated.severity
    incident.people_at_risk = validated.people_at_risk or incident.people_at_risk
    incident.vulnerable_people = validated.vulnerable_people or incident.vulnerable_people
    incident.medical_need = validated.medical_need or incident.medical_need
    incident.immediate_needs = validated.immediate_needs
    incident.evidence_quality = validated.evidence_quality
    incident.triaged_at = datetime.now(timezone.utc)
    incident.status = "triaged"

    await log_action(
        db,
        action=AuditAction.TRIAGE,
        entity_type="incident",
        entity_id=incident.id,
        user_id=current_user.id,
        details={"severity": validated.severity, "confidence": validated.confidence},
    )
    await db.flush()
    return validated


@router.post("/{incident_id}/priority", response_model=PriorityScore)
async def calculate_priority(
    incident_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.DISPATCHER, UserRole.ADMIN)),
):
    """Calculate the deterministic priority score for an incident."""
    from app.services.priority_service import calculate_priority_score

    result = await db.execute(select(Incident).where(Incident.id == incident_id, Incident.is_deleted == False))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    priority = calculate_priority_score(incident)

    incident.priority_score = priority.score
    incident.priority_components = priority.components
    incident.prioritized_at = priority.calculated_at
    incident.status = "prioritized"

    await log_action(
        db,
        action=AuditAction.PRIORITIZE,
        entity_type="incident",
        entity_id=incident.id,
        user_id=current_user.id,
        details={"score": priority.score},
    )
    await db.flush()
    return priority


@router.post("/{incident_id}/recommendations")
async def generate_recommendations(
    incident_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.DISPATCHER, UserRole.ADMIN)),
):
    """Generate resource recommendations for an incident."""
    from app.services.recommendation_service import generate_resource_recommendations

    result = await db.execute(select(Incident).where(Incident.id == incident_id, Incident.is_deleted == False))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    recommendations = await generate_resource_recommendations(db, incident)
    await log_action(
        db,
        action=AuditAction.RECOMMEND,
        entity_type="incident",
        entity_id=incident.id,
        user_id=current_user.id,
        details={"count": len(recommendations)},
    )
    return recommendations
