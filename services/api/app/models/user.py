"""User model with RBAC roles."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.models.base import BaseModel


class UserRole(str, enum.Enum):
    """User roles for RBAC."""
    CITIZEN = "citizen"
    RESPONDER = "responder"
    DISPATCHER = "dispatcher"
    ADMIN = "admin"


class User(BaseModel):
    """User account with role-based access control."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole), default=UserRole.CITIZEN, nullable=False
    )
    organization: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    incidents_reported = relationship("Incident", back_populates="reporter", foreign_keys="Incident.reporter_id")
    assignments = relationship("Assignment", back_populates="responder")
    audit_events = relationship("AuditLog", back_populates="user")
