"""Dashboard routes: KPI summary for the command center."""

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.incident import Incident, IncidentStatus, IncidentSeverity
from app.models.resource import Resource, ResourceStatus
from app.models.entities import Recommendation, RecommendationStatus, Assignment, AssignmentStatus, Hazard, HazardStatus
from app.schemas.schemas import DashboardSummary

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a KPI summary for the command dashboard."""
    # Incident counts
    total = await db.scalar(select(func.count(Incident.id)).where(Incident.is_deleted == False))
    active_statuses = [IncidentStatus.REPORTED, IncidentStatus.TRIAGED, IncidentStatus.PRIORITIZED,
                       IncidentStatus.ASSIGNED, IncidentStatus.IN_PROGRESS]
    active = await db.scalar(select(func.count(Incident.id)).where(
        Incident.is_deleted == False, Incident.status.in_(active_statuses)))
    critical = await db.scalar(select(func.count(Incident.id)).where(
        Incident.is_deleted == False, Incident.severity == IncidentSeverity.CRITICAL,
        Incident.status.in_(active_statuses)))

    # Resource counts
    available = await db.scalar(select(func.count(Resource.id)).where(
        Resource.is_deleted == False, Resource.status == ResourceStatus.AVAILABLE))
    deployed = await db.scalar(select(func.count(Resource.id)).where(
        Resource.is_deleted == False, Resource.status == ResourceStatus.DEPLOYED))

    # Recommendations
    pending_recs = await db.scalar(select(func.count(Recommendation.id)).where(
        Recommendation.is_deleted == False, Recommendation.status == RecommendationStatus.PENDING))

    # Assignments
    active_assignments = await db.scalar(select(func.count(Assignment.id)).where(
        Assignment.is_deleted == False, Assignment.status.in_([
            AssignmentStatus.ASSIGNED, AssignmentStatus.ACCEPTED,
            AssignmentStatus.EN_ROUTE, AssignmentStatus.ON_SCENE])))

    # Hazards
    active_hazards = await db.scalar(select(func.count(Hazard.id)).where(
        Hazard.is_deleted == False, Hazard.status == HazardStatus.ACTIVE))

    return DashboardSummary(
        total_incidents=total or 0,
        active_incidents=active or 0,
        critical_incidents=critical or 0,
        available_resources=available or 0,
        deployed_resources=deployed or 0,
        pending_recommendations=pending_recs or 0,
        active_assignments=active_assignments or 0,
        active_hazards=active_hazards or 0,
        avg_response_time_minutes=None,
    )
