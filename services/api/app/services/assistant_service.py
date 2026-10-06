"""AI Command Assistant Service."""

import time
from datetime import datetime, timezone

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.ai_adapter import MockAIAdapter, get_ai_adapter
from app.models.entities import Hazard, HazardStatus, Recommendation, RecommendationStatus
from app.models.incident import Incident, IncidentSeverity, IncidentStatus
from app.models.resource import Resource, ResourceStatus
from app.models.user import User
from app.schemas.schemas import AssistantQuery, AssistantResponse

logger = structlog.get_logger()

# Repeat-question cache and provider cooldown keep the assistant responsive
# under provider rate limits (free-tier keys cap requests per minute).
_CACHE_TTL_SECONDS = 120.0
_COOLDOWN_SECONDS = 60.0
_response_cache: dict[str, tuple[float, str]] = {}
_llm_cooldown_until: float = 0.0


async def _gather_context(db: AsyncSession):
    """Collect current situation data for the assistant."""
    active_incidents = (await db.execute(
        select(Incident).where(
            Incident.is_deleted == False,
            Incident.status.notin_([IncidentStatus.RESOLVED, IncidentStatus.CLOSED]),
        ).order_by(Incident.priority_score.desc().nullslast()).limit(10)
    )).scalars().all()

    active_hazards = (await db.execute(
        select(Hazard).where(Hazard.is_deleted == False, Hazard.status == HazardStatus.ACTIVE)
    )).scalars().all()

    available_resources = (await db.execute(
        select(Resource).where(
            Resource.is_deleted == False, Resource.status == ResourceStatus.AVAILABLE
        ).order_by(Resource.resource_type, Resource.name)
    )).scalars().all()

    pending_recs = await db.scalar(
        select(func.count(Recommendation.id)).where(
            Recommendation.status == RecommendationStatus.PENDING,
            Recommendation.human_approval_required == True,
        )
    )

    return active_incidents, active_hazards, available_resources, pending_recs or 0


def _answer_without_llm(
    question: str,
    active_incidents,
    active_hazards,
    available_resources,
    pending_recs: int,
    degraded: bool = False,
) -> str:
    """Generate a useful, factual answer from the database when no LLM answer is available.

    degraded=True when an LLM was configured but failed (rate limit/outage) —
    the wording then reflects a temporary outage instead of missing configuration.
    """
    q = question.lower().strip()

    # Greetings / small talk
    if q in {"hi", "hello", "hey", "hi there", "hello there", "greetings"}:
        return (
            "Hello! I'm the ResQGrid AI Command Assistant. I can help with:\n"
            "- Critical incidents and situation summary\n"
            "- Available rescue resources\n"
            "- Active hazards and blocked routes\n"
            "- Pending AI recommendations awaiting approval\n\n"
            "What would you like to know?"
        )

    # Critical incidents
    if any(k in q for k in ["critical incidents", "most critical", "urgent incidents", "highest priority"]):
        critical = [i for i in active_incidents if i.severity == IncidentSeverity.CRITICAL]
        if not critical:
            return "There are no critical incidents currently open."
        lines = [f"There {('is' if len(critical) == 1 else 'are')} {len(critical)} critical incident(s) open right now:"]
        for i in critical[:5]:
            lines.append(f"- {i.title} ({i.incident_type.value}, people at risk: {i.people_at_risk or 'unknown'})")
        if len(critical) > 5:
            lines.append(f"- ...and {len(critical) - 5} more critical incidents.")
        return "\n".join(lines)

    # Resources near Colombo / available resources
    if any(k in q for k in ["available resources", "rescue resources", "resources near", "what resources", "which resources"]):
        if not available_resources:
            return "No resources are currently marked as available."
        by_type: dict[str, list[str]] = {}
        for r in available_resources:
            by_type.setdefault(r.resource_type.value.replace("_", " "), []).append(r.name)
        lines = [f"There are {len(available_resources)} resource(s) currently available:"]
        for t, names in sorted(by_type.items()):
            lines.append(f"- {t.title()}: {', '.join(names[:5])}{'...' if len(names) > 5 else ''}")
        return "\n".join(lines)

    # Active hazards / blocked routes
    if any(k in q for k in ["hazards", "blocked routes", "active hazards", "summarize hazards", "what hazards"]):
        if not active_hazards:
            return "There are no active hazards recorded right now."
        lines = [f"There are {len(active_hazards)} active hazard(s):"]
        for h in active_hazards[:7]:
            lines.append(f"- [{h.severity}] {h.title} ({h.hazard_type.value})")
        if len(active_hazards) > 7:
            lines.append(f"- ...and {len(active_hazards) - 7} more.")
        return "\n".join(lines)

    # Pending approvals
    if any(k in q for k in ["approval", "pending", "need human approval", "awaiting approval", "need approval"]):
        if pending_recs == 0:
            return "There are no recommendations currently awaiting human approval."
        return f"There {('is' if pending_recs == 1 else 'are')} {pending_recs} AI recommendation(s) awaiting human approval. Open an incident in the detail panel to review and approve or reject them."

    # Incident count summary
    if any(k in q for k in ["how many incidents", "incident count", "total incidents", "situation summary", "what is happening", "what's happening"]):
        total = len(active_incidents)
        critical = len([i for i in active_incidents if i.severity == IncidentSeverity.CRITICAL])
        high = len([i for i in active_incidents if i.severity == IncidentSeverity.HIGH])
        medium = len([i for i in active_incidents if i.severity == IncidentSeverity.MEDIUM])
        low = len([i for i in active_incidents if i.severity == IncidentSeverity.LOW])
        lines = [
            f"Current situation summary:",
            f"- {total} active incident(s): {critical} critical, {high} high, {medium} medium, {low} low.",
            f"- {len(active_hazards)} active hazard(s).",
            f"- {len(available_resources)} resource(s) available.",
            f"- {pending_recs} recommendation(s) pending human approval.",
        ]
        if active_incidents:
            lines.append("\nTop incidents by priority:")
            for i in active_incidents[:5]:
                lines.append(f"- [{i.severity.value}] {i.title}")
        return "\n".join(lines)

    # Fallback: provide a concise summary; wording depends on why the LLM is absent
    total = len(active_incidents)
    critical = len([i for i in active_incidents if i.severity == IncidentSeverity.CRITICAL])
    if degraded:
        preamble = "The live AI backend is temporarily unavailable (rate limit or provider outage)."
    else:
        preamble = (
            "I can answer that more fully once an AI API key is configured "
            "(set GEMINI_API_KEY or DASHSCOPE_API_KEY in services/api/.env)."
        )
    return (
        f"{preamble} "
        f"For now, here is the current situation: {total} active incident(s) ({critical} critical), "
        f"{len(active_hazards)} active hazard(s), {len(available_resources)} resource(s) available, "
        f"and {pending_recs} recommendation(s) pending approval. "
        f"Try asking about critical incidents, available resources, active hazards, or pending approvals."
    )


async def process_assistant_query(
    db: AsyncSession, query: AssistantQuery, current_user: User
) -> AssistantResponse:
    """Process a natural-language query about the current emergency situation."""
    global _llm_cooldown_until

    active_incidents, active_hazards, available_resources, pending_recs = await _gather_context(db)

    adapter = get_ai_adapter()

    # When no AI key is configured, return useful database-driven answers immediately
    if isinstance(adapter, MockAIAdapter):
        answer = _answer_without_llm(
            query.question, active_incidents, active_hazards, available_resources, pending_recs
        )
        return AssistantResponse(
            answer=answer,
            sources=["incident_database", "hazard_registry", "resource_registry", "recommendation_registry"],
            confidence=0.92,
            timestamp=datetime.now(timezone.utc),
        )

    # Build context for the real AI
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

Available Resources: {len(available_resources)}
Pending Recommendations: {pending_recs}
"""

    prompt = f"""You are the ResQGrid AI Command Assistant. Answer the operator's question based on the current situation.
Be concise, factual, and clear. If you are uncertain, say so. Never expose restricted personal data.

{context}

Operator Question: {query.question}

Answer:"""

    now = time.monotonic()
    cache_key = query.question.strip().lower()

    # Serve recent repeat questions from cache to stay under provider rate limits
    cached = _response_cache.get(cache_key)
    if cached is not None and now - cached[0] < _CACHE_TTL_SECONDS:
        return AssistantResponse(
            answer=cached[1],
            sources=["incident_database", "hazard_registry", "resource_registry", "recommendation_registry"],
            confidence=0.85,
            timestamp=datetime.now(timezone.utc),  # noqa: UP017
        )

    # During a provider cooldown (recent rate limit/outage), skip the call entirely
    if now < _llm_cooldown_until:
        answer = _answer_without_llm(
            query.question, active_incidents, active_hazards, available_resources, pending_recs,
            degraded=True,
        )
        return AssistantResponse(
            answer=(
                "Live AI backend is cooling down after a rate limit — "
                "answering from the operations database instead.\n\n" + answer
            ),
            sources=["incident_database", "hazard_registry", "resource_registry", "recommendation_registry"],
            confidence=0.6,
            timestamp=datetime.now(timezone.utc),  # noqa: UP017
        )

    try:
        result = await adapter.complete(prompt)
    except Exception as exc:
        # Degraded mode: any provider failure (quota, timeout, safety block,
        # model error) falls back to deterministic database-driven answers so
        # the assistant keeps working during a crisis.
        _llm_cooldown_until = time.monotonic() + _COOLDOWN_SECONDS
        logger.warning("assistant_llm_unavailable", error=str(exc), question=query.question)
        answer = _answer_without_llm(
            query.question, active_incidents, active_hazards, available_resources, pending_recs,
            degraded=True,
        )
        return AssistantResponse(
            answer=(
                "Live AI backend is unreachable right now — "
                "answering from the operations database instead.\n\n" + answer
            ),
            sources=["incident_database", "hazard_registry", "resource_registry", "recommendation_registry"],
            confidence=0.6,
            timestamp=datetime.now(timezone.utc),
        )

    answer = result if isinstance(result, str) else str(result)
    _response_cache[cache_key] = (time.monotonic(), answer)

    return AssistantResponse(
        answer=answer,
        sources=["incident_database", "hazard_registry", "resource_registry", "recommendation_registry"],
        confidence=0.85,
        timestamp=datetime.now(timezone.utc),
    )
