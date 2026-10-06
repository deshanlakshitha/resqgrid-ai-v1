"""Incident model — the central entity of ResQGrid AI."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Integer, String, Text, Enum as SAEnum
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.models.base import BaseModel


class IncidentSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(str, enum.Enum):
    REPORTED = "reported"
    TRIAGED = "triaged"
    PRIORITIZED = "prioritized"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    FALSE_ALARM = "false_alarm"


class IncidentType(str, enum.Enum):
    FLOOD = "flood"
    FIRE = "fire"
    LANDSLIDE = "landslide"
    EARTHQUAKE = "earthquake"
    ACCIDENT = "accident"
    MEDICAL = "medical"
    HAZMAT = "hazmat"
    INFRASTRUCTURE = "infrastructure"
    OTHER = "other"


class Incident(BaseModel):
    """Emergency incident report."""

    __tablename__ = "incidents"

    # ---- Core fields ----
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    incident_type: Mapped[IncidentType] = mapped_column(
        SAEnum(IncidentType), default=IncidentType.OTHER, nullable=False
    )
    severity: Mapped[IncidentSeverity] = mapped_column(
        SAEnum(IncidentSeverity), default=IncidentSeverity.MEDIUM, nullable=False
    )
    status: Mapped[IncidentStatus] = mapped_column(
        SAEnum(IncidentStatus), default=IncidentStatus.REPORTED, nullable=False
    )

    # ---- Location ----
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # ---- Reporter ----
    reporter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    reporter_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    reporter_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # ---- People at risk ----
    people_at_risk: Mapped[int | None] = mapped_column(Integer, nullable=True)
    vulnerable_people: Mapped[int | None] = mapped_column(Integer, nullable=True)
    injuries_reported: Mapped[int | None] = mapped_column(Integer, nullable=True)
    medical_need: Mapped[bool] = mapped_column(Boolean, default=False)

    # ---- AI Triage output (JSON) ----
    triage_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    triage_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    triage_reason_codes: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    triaged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # ---- Priority score ----
    priority_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    priority_components: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    prioritized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # ---- Additional context ----
    immediate_needs: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    evidence_quality: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    reporter = relationship("User", back_populates="incidents_reported", foreign_keys=[reporter_id])
    evidence_items = relationship("Evidence", back_populates="incident")
    recommendations = relationship("Recommendation", back_populates="incident")
    assignments = relationship("Assignment", back_populates="incident")
