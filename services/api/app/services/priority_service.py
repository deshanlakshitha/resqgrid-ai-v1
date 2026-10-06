"""Deterministic Priority Engine — configurable, explainable scoring."""

from datetime import datetime, timezone

from app.core.config import settings
from app.models.incident import Incident, IncidentSeverity
from app.schemas.schemas import PriorityScore


def _normalize_severity(severity: str) -> float:
    """Convert severity to a 0-100 scale."""
    mapping = {"low": 25, "medium": 50, "high": 75, "critical": 100}
    return mapping.get(severity, 50)


def _normalize_count(count: int | None, max_expected: int = 100) -> float:
    """Normalize a count to 0-100 scale."""
    if count is None:
        return 0
    return min((count / max_expected) * 100, 100)


def _time_sensitivity_score(incident: Incident) -> float:
    """Calculate time sensitivity based on age and severity."""
    if not incident.created_at:
        return 50
    age_minutes = (datetime.now(timezone.utc) - incident.created_at.replace(tzinfo=timezone.utc)).total_seconds() / 60
    severity_multiplier = {"critical": 3, "high": 2, "medium": 1, "low": 0.5}.get(incident.severity.value, 1)
    urgency = min(age_minutes * severity_multiplier, 100)
    return urgency


def calculate_priority_score(incident: Incident) -> PriorityScore:
    """
    Calculate the deterministic priority score for an incident.

    Formula (default weights, configurable):
      Priority = 0.30 * LifeRisk + 0.20 * MedicalUrgency + 0.15 * PeopleAtRisk
               + 0.15 * EnvironmentalRisk + 0.10 * TimeSensitivity + 0.10 * EvidenceConfidence

    NOTE: These weights are configurable and NOT claimed to be scientifically validated.
    """
    # Factor 1: Life Risk (based on severity and injuries)
    life_risk = _normalize_severity(incident.severity.value)
    if incident.injuries_reported and incident.injuries_reported > 0:
        life_risk = min(life_risk + 20, 100)

    # Factor 2: Medical Urgency
    medical_urgency = 100 if incident.medical_need else 0
    if incident.triage_data and incident.triage_data.get("medical_need"):
        medical_urgency = max(medical_urgency, 80)

    # Factor 3: People at Risk
    people_at_risk = _normalize_count(incident.people_at_risk, max_expected=50)
    if incident.vulnerable_people:
        people_at_risk = min(people_at_risk + _normalize_count(incident.vulnerable_people, 20), 100)

    # Factor 4: Environmental Risk (based on incident type)
    env_risk_map = {
        "flood": 80, "fire": 90, "earthquake": 95, "landslide": 75,
        "hazmat": 85, "accident": 50, "medical": 40, "infrastructure": 60, "other": 50,
    }
    environmental_risk = env_risk_map.get(incident.incident_type.value, 50)

    # Factor 5: Time Sensitivity
    time_sensitivity = _time_sensitivity_score(incident)

    # Factor 6: Evidence Confidence
    evidence_confidence = (incident.triage_confidence or 0.5) * 100

    # Weighted sum
    weights = {
        "life_risk": settings.WEIGHT_LIFE_RISK,
        "medical_urgency": settings.WEIGHT_MEDICAL_URGENCY,
        "people_at_risk": settings.WEIGHT_PEOPLE_AT_RISK,
        "environmental_risk": settings.WEIGHT_ENVIRONMENTAL_RISK,
        "time_sensitivity": settings.WEIGHT_TIME_SENSITIVITY,
        "evidence_confidence": settings.WEIGHT_EVIDENCE_CONFIDENCE,
    }

    components = {
        "life_risk": round(life_risk, 2),
        "medical_urgency": round(medical_urgency, 2),
        "people_at_risk": round(people_at_risk, 2),
        "environmental_risk": round(environmental_risk, 2),
        "time_sensitivity": round(time_sensitivity, 2),
        "evidence_confidence": round(evidence_confidence, 2),
    }

    score = sum(components[k] * weights[k] for k in components)

    # Generate reason codes
    reason_codes = []
    if life_risk >= 75:
        reason_codes.append("high_life_risk")
    if medical_urgency >= 80:
        reason_codes.append("urgent_medical_need")
    if people_at_risk >= 60:
        reason_codes.append("large_population_at_risk")
    if environmental_risk >= 80:
        reason_codes.append("high_environmental_threat")
    if time_sensitivity >= 70:
        reason_codes.append("time_critical")
    if evidence_confidence >= 80:
        reason_codes.append("high_confidence_evidence")
    if incident.vulnerable_people and incident.vulnerable_people > 0:
        reason_codes.append("vulnerable_population")

    return PriorityScore(
        score=round(score, 2),
        components=components,
        weights=weights,
        reason_codes=reason_codes,
        calculated_at=datetime.now(timezone.utc),
    )
