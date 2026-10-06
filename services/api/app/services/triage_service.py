"""AI Triage Service — runs AI triage on incidents via the model adapter."""

from app.adapters.ai_adapter import get_ai_adapter
from app.models.incident import Incident


async def run_ai_triage(incident: Incident) -> dict:
    """
    Run AI triage on an incident.
    Returns a dict matching the TriageOutput schema.
    All AI output is validated by the caller before use.
    """
    adapter = get_ai_adapter()

    prompt = f"""You are an emergency triage AI. Analyze the following incident report and return a JSON object
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
Title: {incident.title}
Description: {incident.description}
Reported Type: {incident.incident_type}
Location: ({incident.latitude}, {incident.longitude})
People at risk (reported): {incident.people_at_risk}
Vulnerable people (reported): {incident.vulnerable_people}
Injuries reported: {incident.injuries_reported}
Medical need reported: {incident.medical_need}
"""

    result = await adapter.complete(prompt, response_format="json")
    return result
