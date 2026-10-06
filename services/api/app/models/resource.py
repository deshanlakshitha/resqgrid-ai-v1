"""Resource model — emergency response resources (vehicles, teams, equipment)."""

import uuid
from decimal import Decimal

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.models.base import BaseModel


class ResourceType(str, enum.Enum):
    AMBULANCE = "ambulance"
    FIRE_TRUCK = "fire_truck"
    RESCUE_BOAT = "rescue_boat"
    HELICOPTER = "helicopter"
    RESCUE_TEAM = "rescue_team"
    MEDICAL_TEAM = "medical_team"
    SHELTER = "shelter"
    GENERATOR = "generator"
    SUPPLY_TRUCK = "supply_truck"
    DRONE = "drone"
    OTHER = "other"


class ResourceStatus(str, enum.Enum):
    AVAILABLE = "available"
    DEPLOYED = "deployed"
    IN_TRANSIT = "in_transit"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"


class Resource(BaseModel):
    """Emergency response resource."""

    __tablename__ = "resources"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    resource_type: Mapped[ResourceType] = mapped_column(
        SAEnum(ResourceType), nullable=False
    )
    status: Mapped[ResourceStatus] = mapped_column(
        SAEnum(ResourceStatus), default=ResourceStatus.AVAILABLE, nullable=False
    )

    # ---- Location ----
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    base_address: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # ---- Capacity & capabilities ----
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    capabilities: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    equipment: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # ---- Organization ----
    organization: Mapped[str | None] = mapped_column(String(200), nullable=True)
    contact_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # ---- Constraints ----
    operating_hours: Mapped[str | None] = mapped_column(String(100), nullable=True)
    max_range_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    constraints: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # ---- Current assignment ----
    current_assignment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    # Relationships
    assignments = relationship("Assignment", back_populates="resource")
    recommendations = relationship("Recommendation", back_populates="resource")
