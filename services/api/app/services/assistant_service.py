"""AI Command Assistant Service."""

from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.ai_adapter import get_ai_adapter
from app.models.incident import Incident, IncidentStatus, IncidentSeverity
from app.models.resource import Resource, ResourceStatus
from app.models.entities import Hazard, HazardStatus
from app.schemas.schemas import AssistantQuery, AssistantResponse
from app.models.user import User


async def process_assistant_query(
    db: AsyncSession, query: AssistantQuery, current_user: User
) -> AssistantResponse:
    """Process a natural-language query about the current emergency situation."""
    # Gather context
    active_incidents = (await db.execute(
        select(Incident).where(
            Incident.is_deleted == False,
            Incident.status.notin_([IncidentStatus.RESOLVED, IncidentStatus.CLOSED]),
        ).order_by(Incident.priority_score.desc().nullslast()).limit(10)
    )).scalars().all()

    active_hazards = (await db.execute(
        select(Hazard).where(Hazard.is_deleted == False, Hazard.status == HazardStatus.ACTIVE)
    )).scalars().all()

    available_resources = await db.scalar(
        select(func.count(Resource.id)).where(
            Resource.is_deleted == False, Resource.status == ResourceStatus.AVAILABLE
        )
    )

    # Build context for the AI
    incident_summaries = []
    for inc in active_incidents:
        incident_summaries.append(
            f"- [{inc.severity.value}] {inc.title} (Score: {inc.priority_score or 'N/A'}, "
            f"Type: {inc.incident_type.value}, People at risk: {inc.people_at_risk or 'unknown'})"
        )

    hazard_summaries = [f"- [{h.severity}] {h.title} ({h.hazard_type.value})" for h in active_hazards]

    context = f"""Current Situation Summary:
Active Incidents ({len(active_incidents)}):
{chr(10).join(incident_summaries) if incident_summaries else 'None'}

Active Hazards ({len(active_hazards)}):
{chr(10).join(hazard_summaries) if hazard_summaries else 'None'}

Available Resources: {available_resources or 0}
"""

    adapter = get_ai_adapter()
    prompt = f"""You are the ResQGrid AI Command Assistant. Answer the operator's question based on the current situation.
Be concise, factual, and clear. If you are uncertain, say so. Never expose restricted personal data.

{context}

Operator Question: {query.question}

Answer:"""

    result = await adapter.complete(prompt)
    answer = result if isinstance(result, str) else str(result)

    return AssistantResponse(
        answer=answer,
        sources=["incident_database", "hazard_registry", "resource_registry"],
        confidence=0.85,
        timestamp=datetime.now(timezone.utc),
    )
