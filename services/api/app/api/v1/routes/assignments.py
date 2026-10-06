"""Assignment routes: create and update resource assignments."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.entities import Assignment, AssignmentStatus
from app.models.resource import Resource, ResourceStatus
from app.schemas.schemas import AssignmentResponse, AssignmentUpdate

router = APIRouter()


@router.post("", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
async def create_assignment(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.DISPATCHER, UserRole.ADMIN)),
):
    """Create a new assignment from an approved recommendation."""
    assignment = Assignment(
        incident_id=uuid.UUID(data["incident_id"]),
        resource_id=uuid.UUID(data["resource_id"]),
        responder_id=uuid.UUID(data["responder_id"]) if data.get("responder_id") else None,
        recommendation_id=uuid.UUID(data["recommendation_id"]) if data.get("recommendation_id") else None,
        status=AssignmentStatus.ASSIGNED,
        dispatched_at=datetime.now(timezone.utc),
    )
    db.add(assignment)

    # Update resource status
    result = await db.execute(select(Resource).where(Resource.id == assignment.resource_id))
    resource = result.scalar_one_or_none()
    if resource:
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
    current_user: User = Depends(get_current_user),
):
    """Update assignment status (responder accepts, arrives, completes)."""
    result = await db.execute(
        select(Assignment).where(Assignment.id == assignment_id, Assignment.is_deleted == False)
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    assignment.status = data.status
    if data.notes:
        assignment.notes = data.notes

    now = datetime.now(timezone.utc)
    status_map = {
        AssignmentStatus.ACCEPTED: "accepted_at",
        AssignmentStatus.EN_ROUTE: "accepted_at",
        AssignmentStatus.ON_SCENE: "arrived_at",
        AssignmentStatus.COMPLETED: "completed_at",
    }
    timestamp_field = status_map.get(AssignmentStatus(data.status))
    if timestamp_field:
        setattr(assignment, timestamp_field, now)

    # If completed, free the resource
    if data.status == AssignmentStatus.COMPLETED:
        res_result = await db.execute(select(Resource).where(Resource.id == assignment.resource_id))
        resource = res_result.scalar_one_or_none()
        if resource:
            resource.status = ResourceStatus.AVAILABLE
            resource.current_assignment_id = None

    await db.flush()
    await db.refresh(assignment)
    return assignment


@router.get("", response_model=list[AssignmentResponse])
async def list_assignments(
    incident_id: uuid.UUID | None = None,
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List assignments with optional filtering."""
    query = select(Assignment).where(Assignment.is_deleted == False)
    if incident_id:
        query = query.where(Assignment.incident_id == incident_id)
    if status_filter:
        query = query.where(Assignment.status == status_filter)

    result = await db.execute(query.order_by(Assignment.created_at.desc()))
    return result.scalars().all()
