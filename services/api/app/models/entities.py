"""Recommendation, Assignment, Evidence, Hazard, and AuditLog models."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.models.base import BaseModel


# ---- Recommendation ----

class RecommendationStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class Recommendation(BaseModel):
    """AI-generated resource recommendation requiring human approval."""

    __tablename__ = "recommendations"

    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=False
    )
    resource_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resources.id"), nullable=False
    )
    status: Mapped[RecommendationStatus] = mapped_column(
        SAEnum(RecommendationStatus), default=RecommendationStatus.PENDING, nullable=False
    )

    # ---- AI reasoning ----
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    estimated_eta_minutes: Mapped[float | None] = mapped_column(Float, nullable=True)
    compatibility_reasons: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    constraints: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    alternatives: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ---- Human approval ----
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    human_approval_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    incident = relationship("Incident", back_populates="recommendations")
    resource = relationship("Resource", back_populates="recommendations")
    approver = relationship("User")


# ---- Assignment ----

class AssignmentStatus(str, enum.Enum):
    ASSIGNED = "assigned"
    ACCEPTED = "accepted"
    EN_ROUTE = "en_route"
    ON_SCENE = "on_scene"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Assignment(BaseModel):
    """Resource assignment to an incident."""

    __tablename__ = "assignments"

    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=False
    )
    resource_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resources.id"), nullable=False
    )
    responder_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    recommendation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recommendations.id"), nullable=True
    )
    status: Mapped[AssignmentStatus] = mapped_column(
        SAEnum(AssignmentStatus), default=AssignmentStatus.ASSIGNED, nullable=False
    )

    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    arrived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    incident = relationship("Incident", back_populates="assignments")
    resource = relationship("Resource", back_populates="assignments")
    responder = relationship("User", back_populates="assignments")


# ---- Evidence ----

class EvidenceType(str, enum.Enum):
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"
    AUDIO = "audio"


class Evidence(BaseModel):
    """Evidence (images, files) attached to incidents."""

    __tablename__ = "evidence"

    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=False
    )
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    evidence_type: Mapped[EvidenceType] = mapped_column(
        SAEnum(EvidenceType), default=EvidenceType.IMAGE, nullable=False
    )
    file_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_analysis: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    incident = relationship("Incident", back_populates="evidence_items")
    uploader = relationship("User")


# ---- Hazard ----

class HazardType(str, enum.Enum):
    FLOOD = "flood"
    FIRE = "fire"
    LANDSLIDE = "landslide"
    ROAD_BLOCKED = "road_blocked"
    CHEMICAL_SPILL = "chemical_spill"
    STRUCTURAL_COLLAPSE = "structural_collapse"
    POWER_OUTAGE = "power_outage"
    OTHER = "other"


class HazardStatus(str, enum.Enum):
    ACTIVE = "active"
    MONITORING = "monitoring"
    CLEARED = "cleared"


class Hazard(BaseModel):
    """Hazard or obstacle affecting response operations."""

    __tablename__ = "hazards"

    hazard_type: Mapped[HazardType] = mapped_column(
        SAEnum(HazardType), nullable=False
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[HazardStatus] = mapped_column(
        SAEnum(HazardStatus), default=HazardStatus.ACTIVE, nullable=False
    )

    # ---- Location ----
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    radius_meters: Mapped[float | None] = mapped_column(Float, nullable=True)
    affected_routes: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # ---- Reporting ----
    reported_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    severity: Mapped[str] = mapped_column(String(20), default="medium")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cleared_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    reporter = relationship("User")


# ---- Audit Log ----

class AuditAction(str, enum.Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    TRIAGE = "triage"
    PRIORITIZE = "prioritize"
    RECOMMEND = "recommend"
    APPROVE = "approve"
    REJECT = "reject"
    ASSIGN = "assign"
    STATUS_CHANGE = "status_change"
    LOGIN = "login"
    LOGOUT = "logout"


class AuditLog(BaseModel):
    """Immutable audit trail for all significant actions."""

    __tablename__ = "audit_logs"

    action: Mapped[AuditAction] = mapped_column(
        SAEnum(AuditAction), nullable=False
    )
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    request_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # ---- Details ----
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    old_values: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    new_values: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    user = relationship("User", back_populates="audit_events")
    incident = relationship("Incident", back_populates="audit_logs", foreign_keys="AuditLog.entity_id")
