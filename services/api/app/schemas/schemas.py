"""Pydantic schemas for request/response validation."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# Auth Schemas
# ============================================================================

class UserRegister(BaseModel):
    email: str = Field(..., max_length=255)
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    role: str = Field("citizen", pattern="^(citizen|responder|dispatcher|admin)$")
    organization: Optional[str] = Field(None, max_length=200)


class UserLogin(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    username: str
    full_name: str
    phone: Optional[str]
    role: str
    organization: Optional[str]
    is_active: bool
    created_at: datetime


# ============================================================================
# Incident Schemas
# ============================================================================

class IncidentCreate(BaseModel):
    title: str = Field(..., max_length=500)
    description: str
    incident_type: str = Field("other")
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    address: Optional[str] = Field(None, max_length=500)
    people_at_risk: Optional[int] = Field(None, ge=0)
    vulnerable_people: Optional[int] = Field(None, ge=0)
    injuries_reported: Optional[int] = Field(None, ge=0)
    medical_need: bool = False
    reporter_name: Optional[str] = Field(None, max_length=200)
    reporter_phone: Optional[str] = Field(None, max_length=20)


class IncidentUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    status: Optional[str] = None
    severity: Optional[str] = None
    notes: Optional[str] = None


class IncidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str
    incident_type: str
    severity: str
    status: str
    latitude: float
    longitude: float
    address: Optional[str]
    people_at_risk: Optional[int]
    vulnerable_people: Optional[int]
    injuries_reported: Optional[int]
    medical_need: bool
    triage_data: Optional[dict]
    triage_confidence: Optional[float]
    priority_score: Optional[float]
    priority_components: Optional[dict]
    immediate_needs: Optional[list]
    evidence_quality: Optional[float]
    reporter_name: Optional[str]
    created_at: datetime
    updated_at: datetime


# ============================================================================
# AI Triage Schemas
# ============================================================================

class TriageOutput(BaseModel):
    """Validated AI triage output — must match this schema exactly."""
    incident_type: Optional[str] = None
    severity: str = Field(..., pattern="^(low|medium|high|critical)$")
    people_at_risk: Optional[int] = Field(None, ge=0)
    vulnerable_people: Optional[int] = Field(None, ge=0)
    medical_need: bool = False
    immediate_needs: list[str] = Field(default_factory=list)
    evidence_quality: float = Field(0.0, ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    reason_codes: list[str] = Field(default_factory=list)


# ============================================================================
# Priority Schemas
# ============================================================================

class PriorityScore(BaseModel):
    """Deterministic priority calculation result."""
    score: float = Field(..., ge=0.0, le=100.0)
    components: dict
    weights: dict
    reason_codes: list[str]
    calculated_at: datetime


# ============================================================================
# Resource Schemas
# ============================================================================

class ResourceCreate(BaseModel):
    name: str = Field(..., max_length=200)
    resource_type: str
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    base_address: Optional[str] = None
    capacity: Optional[int] = Field(None, ge=0)
    capabilities: Optional[list] = None
    equipment: Optional[list] = None
    organization: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    operating_hours: Optional[str] = None
    max_range_km: Optional[float] = None
    constraints: Optional[dict] = None


class ResourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    resource_type: str
    status: str
    latitude: float
    longitude: float
    base_address: Optional[str]
    capacity: Optional[int]
    capabilities: Optional[list]
    organization: Optional[str]
    contact_name: Optional[str]
    max_range_km: Optional[float]
    created_at: datetime


# ============================================================================
# Recommendation Schemas
# ============================================================================

class RecommendationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    incident_id: uuid.UUID
    resource_id: uuid.UUID
    status: str
    confidence: float
    estimated_eta_minutes: Optional[float]
    compatibility_reasons: Optional[list]
    constraints: Optional[list]
    alternatives: Optional[list]
    reasoning: Optional[str]
    human_approval_required: bool
    created_at: datetime


class ApprovalRequest(BaseModel):
    approved: bool
    reason: Optional[str] = None


# ============================================================================
# Assignment Schemas
# ============================================================================

class AssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    incident_id: uuid.UUID
    resource_id: uuid.UUID
    responder_id: Optional[uuid.UUID]
    status: str
    dispatched_at: Optional[datetime]
    accepted_at: Optional[datetime]
    arrived_at: Optional[datetime]
    completed_at: Optional[datetime]
    notes: Optional[str]
    created_at: datetime


class AssignmentUpdate(BaseModel):
    status: str
    notes: Optional[str] = None


# ============================================================================
# Dashboard Schemas
# ============================================================================

class DashboardSummary(BaseModel):
    total_incidents: int
    active_incidents: int
    critical_incidents: int
    available_resources: int
    deployed_resources: int
    pending_recommendations: int
    active_assignments: int
    active_hazards: int
    avg_response_time_minutes: Optional[float]


# ============================================================================
# Hazard Schemas
# ============================================================================

class HazardCreate(BaseModel):
    hazard_type: str
    title: str = Field(..., max_length=300)
    description: Optional[str] = None
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    radius_meters: Optional[float] = Field(None, ge=0)
    severity: str = "medium"
    affected_routes: Optional[list] = None


class HazardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    hazard_type: str
    title: str
    description: Optional[str]
    status: str
    latitude: float
    longitude: float
    radius_meters: Optional[float]
    severity: str
    affected_routes: Optional[list]
    created_at: datetime


# ============================================================================
# Assistant Schemas
# ============================================================================

class AssistantQuery(BaseModel):
    question: str = Field(..., max_length=2000)
    context_incident_ids: Optional[list[uuid.UUID]] = None


class AssistantResponse(BaseModel):
    answer: str
    sources: list[str]
    confidence: float
    timestamp: datetime


# ============================================================================
# Audit Schemas
# ============================================================================

class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    action: str
    entity_type: str
    entity_id: Optional[uuid.UUID]
    user_id: Optional[uuid.UUID]
    details: Optional[dict]
    created_at: datetime


# ============================================================================
# Common
# ============================================================================

class ErrorResponse(BaseModel):
    detail: str
    request_id: Optional[str] = None
    timestamp: datetime


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int
    total_pages: int
