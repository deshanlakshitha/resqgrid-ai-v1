"""Resource routes: CRUD and availability queries."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.resource import Resource, ResourceStatus
from app.schemas.schemas import ResourceCreate, ResourceResponse

router = APIRouter()


@router.post("", response_model=ResourceResponse, status_code=status.HTTP_201_CREATED)
async def create_resource(
    data: ResourceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.DISPATCHER, UserRole.ADMIN)),
):
    """Register a new resource (dispatcher/admin only)."""
    resource = Resource(
        name=data.name,
        resource_type=data.resource_type,
        latitude=data.latitude,
        longitude=data.longitude,
        base_address=data.base_address,
        capacity=data.capacity,
        capabilities=data.capabilities,
        equipment=data.equipment,
        organization=data.organization,
        contact_name=data.contact_name,
        contact_phone=data.contact_phone,
        operating_hours=data.operating_hours,
        max_range_km=data.max_range_km,
        constraints=data.constraints,
    )
    db.add(resource)
    await db.flush()
    await db.refresh(resource)
    return resource


@router.get("", response_model=list[ResourceResponse])
async def list_resources(
    resource_type: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all resources with optional filtering."""
    query = select(Resource).where(Resource.is_deleted == False)

    if resource_type:
        query = query.where(Resource.resource_type == resource_type)
    if status_filter:
        query = query.where(Resource.status == status_filter)

    query = query.order_by(Resource.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/available", response_model=list[ResourceResponse])
async def list_available_resources(
    resource_type: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List resources currently available for assignment."""
    query = select(Resource).where(
        Resource.is_deleted == False,
        Resource.status == ResourceStatus.AVAILABLE,
    )
    if resource_type:
        query = query.where(Resource.resource_type == resource_type)

    result = await db.execute(query.order_by(Resource.name))
    return result.scalars().all()


@router.get("/{resource_id}", response_model=ResourceResponse)
async def get_resource(
    resource_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single resource by ID."""
    result = await db.execute(select(Resource).where(Resource.id == resource_id, Resource.is_deleted == False))
    resource = result.scalar_one_or_none()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    return resource


@router.patch("/{resource_id}", response_model=ResourceResponse)
async def update_resource(
    resource_id: uuid.UUID,
    data: ResourceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.DISPATCHER, UserRole.ADMIN)),
):
    """Update a resource (dispatcher/admin only)."""
    result = await db.execute(select(Resource).where(Resource.id == resource_id, Resource.is_deleted == False))
    resource = result.scalar_one_or_none()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(resource, field, value)

    await db.flush()
    await db.refresh(resource)
    return resource
