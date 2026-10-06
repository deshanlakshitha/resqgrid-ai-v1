"""AI Triage Service — hybrid ensemble: local deterministic engine + LLM.

The local engine always runs (fully offline). When a real AI adapter is
configured, its output is merged via the safety-first ensemble. When no
adapter is available the local result stands alone — the system never
blocks on an external API.
"""

import structlog

from app.adapters.ai_adapter import MockAIAdapter, get_ai_adapter
from app.ai.triage import ensemble, local_engine
from app.models.incident import Incident

logger = structlog.get_logger()

TRIAGE_PROMPT = """You are an emergency triage AI. Analyze the following incident report and return a JSON object
with exactly these fields: incident_type, severity (low/medium/high/critical), people_at_risk (integer or null),
vulnerable_people (integer or null), medical_need (boolean), immediate_needs (array of strings),
evidence_quality (float 0-1), confidence (float 0-1), reason_codes (array of short strings).

Rules:
- If information is missing, return null/unknown instead of inventing it.
- Return confidence separately from severity.
- Include short reason_codes that map to deterministic UI explanations.
- Treat citizen claims as reports, not verified facts.
- Never infer exact medical diagnoses.

Incident Report:
Title: {title}
Description: {description}
Reported Type: {incident_type}
Location: ({latitude}, {longitude})
People at risk (reported): {people_at_risk}
Vulnerable people (reported): {vulnerable_people}
Injuries reported: {injuries_reported}
Medical need reported: {medical_need}
"""


async def run_ai_triage(incident: Incident) -> dict:
    """
    Run hybrid AI triage on an incident.
    Returns a TriageOutput-compatible dict plus an `ensemble` diagnostics
    block. All output is validated by the caller before use.
    """
    local_result = local_engine.analyze_incident(incident)

    llm_result: dict | None = None
    adapter = get_ai_adapter()
    if not isinstance(adapter, MockAIAdapter):
        prompt = TRIAGE_PROMPT.format(
            title=incident.title,
            description=incident.description,
            incident_type=incident.incident_type.value,
            latitude=incident.latitude,
            longitude=incident.longitude,
            people_at_risk=incident.people_at_risk,
            vulnerable_people=incident.vulnerable_people,
            injuries_reported=incident.injuries_reported,
            medical_need=incident.medical_need,
        )
        try:
            raw = await adapter.complete(prompt, response_format="json")
            if isinstance(raw, dict) and "error" not in raw:
                llm_result = raw
        except Exception as exc:  # adapter failures must never block triage
            logger.warning("llm_triage_failed", error=str(exc), incident_id=str(incident.id))

    merged = ensemble.merge_ensemble(local_result, llm_result)
    logger.info(
        "triage_ensemble_complete",
        incident_id=str(incident.id),
        mode=merged["ensemble"]["mode"],
        severity=merged["severity"],
        confidence=merged["confidence"],
        agreement=merged["ensemble"]["agreement"],
        disagreement=merged["ensemble"]["disagreement_flag"],
    )
    return merged
