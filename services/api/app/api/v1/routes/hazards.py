"""Hazard routes: report and manage hazards and blocked roads."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.entities import Hazard
from app.schemas.schemas import HazardCreate, HazardResponse

router = APIRouter()


@router.post("", response_model=HazardResponse, status_code=status.HTTP_201_CREATED)
async def create_hazard(
    data: HazardCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Report a new hazard or blocked road."""
    hazard = Hazard(
        hazard_type=data.hazard_type,
        title=data.title,
        description=data.description,
        latitude=data.latitude,
        longitude=data.longitude,
        radius_meters=data.radius_meters,
        severity=data.severity,
        affected_routes=data.affected_routes,
        reported_by=current_user.id,
    )
    db.add(hazard)
    await db.flush()
    await db.refresh(hazard)
    return hazard


@router.get("", response_model=list[HazardResponse])
async def list_hazards(
    status_filter: str | None = Query(None, alias="status"),
    hazard_type: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List active hazards."""
    query = select(Hazard).where(Hazard.is_deleted == False)
    if status_filter:
        query = query.where(Hazard.status == status_filter)
    if hazard_type:
        query = query.where(Hazard.hazard_type == hazard_type)
    result = await db.execute(query.order_by(Hazard.created_at.desc()))
    return result.scalars().all()


@router.patch("/{hazard_id}", response_model=HazardResponse)
async def update_hazard(
    hazard_id: uuid.UUID,
    data: HazardCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.DISPATCHER, UserRole.ADMIN)),
):
    """Update a hazard (dispatcher/admin only)."""
    result = await db.execute(select(Hazard).where(Hazard.id == hazard_id, Hazard.is_deleted == False))
    hazard = result.scalar_one_or_none()
    if not hazard:
        raise HTTPException(status_code=404, detail="Hazard not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(hazard, field, value)
    await db.flush()
    await db.refresh(hazard)
    return hazard
