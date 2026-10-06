"""Assignment routes: create and update resource assignments, and AI optimization."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.allocation.optimizer import optimize_assignments
from app.core.database import get_db
from app.core.deps import require_role, responder_assignment_scope
from app.models.entities import Hazard, HazardStatus
from app.models.incident import Incident, IncidentStatus
from app.models.user import User, UserRole
from app.models.entities import Assignment, AssignmentStatus, Recommendation, RecommendationStatus
from app.models.resource import Resource, ResourceStatus
from app.schemas.schemas import AssignmentCreate, AssignmentPlan, AssignmentResponse, AssignmentUpdate

router = APIRouter()


class OptimizeRequest(BaseModel):
    """Optional filter: restrict optimization to specific incidents."""
    incident_ids: list[uuid.UUID] | None = None


@router.post("/optimize", response_model=AssignmentPlan)
async def optimize_assignments_endpoint(
    data: OptimizeRequest | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.DISPATCHER, UserRole.ADMIN)),
):
    """Compute the globally optimal incident->resource assignment plan.

    Uses the Hungarian (Kuhn-Munkres) algorithm over travel distance, active
    hazard penalties, and type compatibility. Advisory only — dispatchers
    approve every actual assignment.
    """
    query = select(Incident).where(
        Incident.is_deleted == False,
        Incident.status.notin_([IncidentStatus.RESOLVED, IncidentStatus.CLOSED]),
    )
    if data and data.incident_ids:
        query = query.where(Incident.id.in_(data.incident_ids))
    incidents = (await db.execute(query)).scalars().all()

    resources = (await db.execute(
        select(Resource).where(Resource.is_deleted == False, Resource.status == ResourceStatus.AVAILABLE)
    )).scalars().all()

    hazards = (await db.execute(
        select(Hazard).where(Hazard.is_deleted == False, Hazard.status == HazardStatus.ACTIVE)
    )).scalars().all()

    return optimize_assignments(list(incidents), list(resources), list(hazards))


@router.post("", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
async def create_assignment(
    data: AssignmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.DISPATCHER, UserRole.ADMIN)),
):
    """Create a new assignment from an approved recommendation."""
    incident = (await db.execute(select(Incident).where(
        Incident.id == data.incident_id, Incident.is_deleted == False,
    ))).scalar_one_or_none()
    if incident is None:
        raise HTTPException(404, "Incident not found")
    resource = (await db.execute(select(Resource).where(
        Resource.id == data.resource_id, Resource.is_deleted == False,
    ).with_for_update())).scalar_one_or_none()
    if resource is None:
        raise HTTPException(404, "Resource not found")
    if resource.status != ResourceStatus.AVAILABLE or resource.current_assignment_id is not None:
        raise HTTPException(409, "Resource already assigned or unavailable")
    if data.recommendation_id:
        rec = (await db.execute(select(Recommendation).where(
            Recommendation.id == data.recommendation_id, Recommendation.is_deleted == False,
        ))).scalar_one_or_none()
        if (rec is None or rec.status != RecommendationStatus.APPROVED
                or rec.incident_id != data.incident_id or rec.resource_id != data.resource_id):
            raise HTTPException(400, "An approved recommendation matching this incident and resource is required")
    if data.responder_id:
        responder = (await db.execute(select(User).where(
            User.id == data.responder_id, User.role == UserRole.RESPONDER,
            User.is_active == True, User.is_deleted == False,
        ))).scalar_one_or_none()
        if responder is None:
            raise HTTPException(400, "Responder must be an active responder account")
    assignment = Assignment(
        id=uuid.uuid4(),
        incident_id=data.incident_id,
        resource_id=data.resource_id,
        responder_id=data.responder_id,
        recommendation_id=data.recommendation_id,
        status=AssignmentStatus.ASSIGNED,
        dispatched_at=datetime.now(timezone.utc),
    )
    db.add(assignment)

    # Update resource status
    resource.status = ResourceStatus.DEPLOYED
    resource.current_assignment_id = assignment.id

    await db.flush()
    await db.refresh(assignment)
    return assignment


@router.patch("/{assignment_id}", response_model=AssignmentResponse)
async def update_assignment(
    assignment_id: uuid.UUID,
    data: AssignmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.DISPATCHER, UserRole.RESPONDER)),
):
    """Update assignment status (responder accepts, arrives, completes)."""
    result = await db.execute(
        select(Assignment).where(Assignment.id == assignment_id, Assignment.is_deleted == False).with_for_update()
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    if current_user.role == UserRole.RESPONDER and assignment.responder_id != current_user.id:
        if (assignment.responder_id is None and assignment.status == AssignmentStatus.ASSIGNED
                and data.status == AssignmentStatus.ACCEPTED):
            # The locked row makes claiming an unassigned dispatch atomic.
            assignment.responder_id = current_user.id
        else:
            raise HTTPException(403, "Only the assigned responder may update this assignment")

    next_status = AssignmentStatus(data.status)
    transitions = {
        AssignmentStatus.ASSIGNED: {AssignmentStatus.ACCEPTED, AssignmentStatus.CANCELLED},
        AssignmentStatus.ACCEPTED: {AssignmentStatus.EN_ROUTE, AssignmentStatus.CANCELLED},
        AssignmentStatus.EN_ROUTE: {AssignmentStatus.ON_SCENE, AssignmentStatus.CANCELLED},
        AssignmentStatus.ON_SCENE: {AssignmentStatus.COMPLETED, AssignmentStatus.CANCELLED},
    }
    if next_status != assignment.status and next_status not in transitions.get(assignment.status, set()):
        raise HTTPException(409, "Invalid assignment status transition")
    if current_user.role == UserRole.RESPONDER and next_status == AssignmentStatus.CANCELLED:
        raise HTTPException(403, "Only a dispatcher or administrator may cancel a dispatch")
    if next_status == assignment.status:
        return assignment
    assignment.status = next_status
    if data.notes is not None:
        assignment.notes = data.notes

    now = datetime.now(timezone.utc)
    status_map = {
        AssignmentStatus.ACCEPTED: "accepted_at",
        AssignmentStatus.EN_ROUTE: "accepted_at",
        AssignmentStatus.ON_SCENE: "arrived_at",
        AssignmentStatus.COMPLETED: "completed_at",
    }
    timestamp_field = status_map.get(AssignmentStatus(data.status))
    if timestamp_field and getattr(assignment, timestamp_field) is None:
        setattr(assignment, timestamp_field, now)

    # If completed, free the resource
    if next_status in (AssignmentStatus.COMPLETED, AssignmentStatus.CANCELLED):
        res_result = await db.execute(select(Resource).where(Resource.id == assignment.resource_id).with_for_update())
        resource = res_result.scalar_one_or_none()
        if resource and resource.current_assignment_id == assignment.id:
            resource.status = ResourceStatus.AVAILABLE
            resource.current_assignment_id = None

    await db.flush()
    await db.refresh(assignment)
    return assignment


@router.get("", response_model=list[AssignmentResponse])
async def list_assignments(
    incident_id: uuid.UUID | None = None,
    status_filter: AssignmentStatus | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.DISPATCHER, UserRole.RESPONDER)),
):
    """List assignments with optional filtering."""
    query = select(Assignment).where(Assignment.is_deleted == False)
    if current_user.role == UserRole.RESPONDER:
        query = query.where(responder_assignment_scope(current_user))
    if incident_id:
        query = query.where(Assignment.incident_id == incident_id)
    if status_filter:
        query = query.where(Assignment.status == status_filter)

    result = await db.execute(query.order_by(Assignment.created_at.desc()))
    return result.scalars().all()
