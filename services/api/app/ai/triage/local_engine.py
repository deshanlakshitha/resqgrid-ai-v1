"""Local deterministic triage engine — pure-Python NLP over incident reports.

Runs entirely offline: lexicon matching with negation handling, numeric
extraction for people counts, severity escalation signals, and a calibrated
confidence score. Output schema matches TriageOutput so it can stand alone
or ensemble with an LLM.
"""

import re
from typing import Any

# A single weak lexicon signal is not enough to override the reported type.
OVERRIDE_MARGIN = 1.5

# Incident type -> list of (keyword/phrase, signal_code, weight).
TYPE_LEXICONS: dict[str, list[tuple[str, str, float]]] = {
    "flood": [
        ("flood", "flood_signal", 2.0), ("flooding", "flood_signal", 2.0),
        ("water rising", "water_rising", 2.0), ("water is rising", "water_rising", 2.0),
        ("submerged", "submerged", 2.0), ("standing water", "standing_water", 1.5),
        ("overflow", "overflow", 1.5), ("river bank", "river_breach", 1.5),
        ("dam", "dam_failure", 2.5), ("heavy rain", "heavy_rain", 1.0),
    ],
    "fire": [
        ("fire", "fire_signal", 2.0), ("burning", "active_fire", 2.0),
        ("smoke", "smoke", 1.5), ("flames", "active_fire", 2.0),
        ("explosion", "explosion", 2.5), ("wildfire", "wildfire", 2.0),
        ("bushfire", "wildfire", 2.0), ("electrical fire", "electrical_fire", 2.0),
    ],
    "earthquake": [
        ("earthquake", "earthquake_signal", 2.5), ("tremor", "tremor", 1.5),
        ("aftershock", "aftershock", 2.0), ("collapsed building", "collapse", 2.5),
        ("building collapsed", "collapse", 2.5), ("rubble", "rubble", 1.5),
    ],
    "landslide": [
        ("landslide", "landslide_signal", 2.5), ("mudslide", "landslide_signal", 2.5),
        ("rockfall", "rockfall", 2.0), ("slope failure", "slope_failure", 2.0),
        ("debris flow", "debris_flow", 2.0),
    ],
    "accident": [
        ("car crash", "vehicle_accident", 2.0), ("collision", "vehicle_accident", 2.0),
        ("vehicle accident", "vehicle_accident", 2.0), ("overturned", "overturned_vehicle", 2.0),
        ("pileup", "multi_vehicle", 2.5), ("motorcycle", "vehicle_accident", 1.5),
    ],
    "medical": [
        ("heart attack", "cardiac", 2.5), ("cardiac", "cardiac", 2.5),
        ("unconscious", "unconscious", 2.5), ("not breathing", "not_breathing", 3.0),
        ("severe bleeding", "severe_bleeding", 2.5), ("stroke", "stroke", 2.5),
        ("overdose", "overdose", 2.5), ("anaphylaxis", "anaphylaxis", 2.5),
        ("injured", "injuries", 1.5), ("casualties", "mass_casualty", 2.5),
    ],
    "hazmat": [
        ("chemical spill", "chemical_spill", 2.5), ("gas leak", "gas_leak", 2.5),
        ("toxic", "toxic_release", 2.5), ("radioactive", "radiological", 3.0),
        ("hazmat", "hazmat_signal", 2.5), ("oil spill", "oil_spill", 2.0),
    ],
    "infrastructure": [
        ("bridge collapse", "bridge_collapse", 2.5), ("power line", "downed_power", 2.0),
        ("power outage", "power_outage", 1.5), ("road blocked", "blocked_road", 1.5),
        ("collapsed", "collapse", 1.5), ("water main", "water_main", 1.5),
    ],
}

# Severity escalators: weight added to the severity score when present.
ESCALATORS: list[tuple[str, float]] = [
    ("trapped", 2.0), ("stranded", 1.5), ("collapsed", 2.0), ("collapse", 2.0),
    ("multiple", 1.5), ("spreading", 1.5), ("drowning", 2.5), ("unconscious", 2.0),
    ("explosion", 2.0), ("fire spreading", 2.5), ("rapidly", 1.0), ("critical", 1.0),
]

# De-escalators: evidence the situation is under control.
DEESCALATORS: list[tuple[str, float]] = [
    ("minor", -1.0), ("small", -0.5), ("contained", -1.5), ("no injuries", -1.5),
    ("no fire", -2.0), ("under control", -1.5), ("false alarm", -3.0),
]

VULNERABLE_KEYWORDS = [
    "elderly", "senior", "child", "children", "baby", "infant", "toddler",
    "disabled", "wheelchair", "pregnant", "hospitalized",
]

MEDICAL_KEYWORDS = [
    "medical", "hospital", "ambulance", "medicine", "insulin", "dialysis",
    "oxygen", "prescription", "pharmacy",
]

NEEDS_MAP: list[tuple[str, str]] = [
    ("evacuat", "evacuation"), ("trapped", "rescue_extraction"), ("stranded", "rescue_extraction"),
    ("shelter", "shelter"), ("medical", "medical"), ("hospital", "medical"),
    ("bleeding", "medical"), ("water", "water_supply"), ("food", "food_supply"),
    ("power", "power_restoration"), ("blocked", "road_clearance"), ("debris", "debris_removal"),
]

NEGATION_PATTERN = re.compile(r"\b(no|not|without|n't)\s+[\w\s]{0,20}$", re.IGNORECASE)
PEOPLE_COUNT_PATTERN = re.compile(
    r"\b(\d+)\s*(people|persons|victims|residents|occupants|passengers|families|homes|houses|workers)\b",
    re.IGNORECASE,
)
SINGLE_PERSON_PATTERN = re.compile(
    r"\b(a person|one person|single person|a man|a woman|a child|an elderly)\b", re.IGNORECASE
)

SEVERITY_LEVELS = ("low", "medium", "high", "critical")


def _is_negated(text: str, position: int) -> bool:
    """Check whether the keyword at `position` is preceded by a negation."""
    window = text[max(0, position - 24):position]
    return bool(NEGATION_PATTERN.search(window))


def analyze_text(title: str, description: str, reported_type: str) -> dict[str, Any]:
    """Analyze a free-text report. Returns a TriageOutput-compatible dict."""
    text = f"{title}. {description}".lower()
    matched: list[tuple[str, str, float]] = []  # (type, signal, weight)

    for itype, lexicon in TYPE_LEXICONS.items():
        for keyword, signal, weight in lexicon:
            start = 0
            while True:
                pos = text.find(keyword, start)
                if pos < 0:
                    break
                if not _is_negated(text, pos):
                    matched.append((itype, signal, weight))
                start = pos + len(keyword)

    # Incident type: strongest lexicon evidence wins, but the reported type
    # gets a prior and a single weak signal is not enough to override it.
    type_scores: dict[str, float] = {}
    for itype, _, weight in matched:
        type_scores[itype] = type_scores.get(itype, 0.0) + weight
    type_scores[reported_type] = type_scores.get(reported_type, 0.0) + 1.0
    best_type = max(type_scores, key=lambda t: type_scores[t])
    if best_type != reported_type and type_scores[best_type] < type_scores[reported_type] + OVERRIDE_MARGIN:
        best_type = reported_type
    type_changed = best_type != reported_type

    # Severity score from escalators / de-escalators + matched signal mass.
    severity_score = sum(w for _, _, w in matched) * 0.5
    active_escalators: list[str] = []
    for word, delta in ESCALATORS:
        pos = text.find(word)
        if pos >= 0 and not _is_negated(text, pos):
            severity_score += delta
            active_escalators.append(word)
    for word, delta in DEESCALATORS:
        pos = text.find(word)
        if pos >= 0:
            severity_score += delta

    if severity_score >= 3.0:
        severity = "critical"
    elif severity_score >= 2.0:
        severity = "high"
    elif severity_score >= 0.8:
        severity = "medium"
    else:
        severity = "low"

    # People counts.
    people_at_risk = None
    count_match = PEOPLE_COUNT_PATTERN.search(text)
    if count_match:
        people_at_risk = int(count_match.group(1))
    elif SINGLE_PERSON_PATTERN.search(text):
        people_at_risk = 1

    vulnerable_people = sum(text.count(k) for k in VULNERABLE_KEYWORDS) or None
    if vulnerable_people and people_at_risk:
        vulnerable_people = min(vulnerable_people, people_at_risk)

    medical_need = any(k in text for k in MEDICAL_KEYWORDS) or bool(
        active_escalators and "unconscious" in active_escalators
    )

    immediate_needs = sorted({need for prefix, need in NEEDS_MAP if prefix in text})

    signals = sorted({signal for _, signal, _ in matched})
    reason_codes = signals + [f"escalator:{w}" for w in active_escalators]
    if type_changed:
        reason_codes.append(f"type_refined_from_{reported_type}")
    if not signals:
        reason_codes.append("no_local_signals")

    # Confidence: signal mass, bounded; sparse evidence -> low confidence.
    confidence = min(0.35 + 0.12 * len(signals) + 0.04 * len(active_escalators), 0.95)
    if not signals:
        confidence = 0.3

    return {
        "incident_type": best_type,
        "severity": severity,
        "people_at_risk": people_at_risk,
        "vulnerable_people": vulnerable_people,
        "medical_need": medical_need,
        "immediate_needs": immediate_needs,
        "evidence_quality": round(min(0.5 + 0.1 * len(signals), 0.95), 2),
        "confidence": round(confidence, 2),
        "reason_codes": reason_codes,
        "engine": "local_lexicon_v1",
    }


def analyze_incident(incident: Any) -> dict[str, Any]:
    """Analyze an Incident ORM object (duck-typed) with its reported fields."""
    result = analyze_text(
        title=getattr(incident, "title", "") or "",
        description=getattr(incident, "description", "") or "",
        reported_type=(
            incident.incident_type.value if hasattr(incident.incident_type, "value") else str(incident.incident_type)
        ),
    )
    # Reporter-provided structured fields are stronger evidence than text alone.
    if getattr(incident, "people_at_risk", None):
        result["people_at_risk"] = incident.people_at_risk
    if getattr(incident, "vulnerable_people", None):
        result["vulnerable_people"] = incident.vulnerable_people
    if getattr(incident, "medical_need", None):
        result["medical_need"] = True
    if getattr(incident, "injuries_reported", None):
        result["medical_need"] = True
        if "injuries" not in result["reason_codes"]:
            result["reason_codes"].append("reported_injuries")
        if result["severity"] in ("low", "medium"):
            result["severity"] = "high"
    return result
