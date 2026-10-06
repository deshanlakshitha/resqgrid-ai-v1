"""Ensemble merger — combines the local deterministic engine with LLM triage.

Safety-first merge policy:
- Severity agreement reinforces confidence (noisy-or combination).
- Severity disagreement escalates to the higher level and flags the incident
  for human review with dampened confidence.
- When no LLM is available (offline / adapter failure) the local engine
  result stands alone.
"""

from typing import Any

from app.ai.triage.local_engine import SEVERITY_LEVELS

_SEVERITY_INDEX = {level: i for i, level in enumerate(SEVERITY_LEVELS)}


def _severity_distance(a: str, b: str) -> int:
    return abs(_SEVERITY_INDEX.get(a, 1) - _SEVERITY_INDEX.get(b, 1))


def agreement_score(local: dict[str, Any], llm: dict[str, Any]) -> float:
    """Weighted agreement between the two engines (0..1)."""
    sev = local.get("severity")
    llm_sev = llm.get("severity")
    if sev and llm_sev:
        d = _severity_distance(sev, llm_sev)
        severity_agree = 1.0 if d == 0 else (0.6 if d == 1 else 0.15)
    else:
        severity_agree = 0.5

    type_agree = 1.0 if local.get("incident_type") == llm.get("incident_type") else 0.4

    local_med = bool(local.get("medical_need"))
    llm_med = bool(llm.get("medical_need"))
    medical_agree = 1.0 if local_med == llm_med else 0.5

    return round(0.5 * severity_agree + 0.3 * type_agree + 0.2 * medical_agree, 3)


def merge_ensemble(local: dict[str, Any], llm: dict[str, Any] | None) -> dict[str, Any]:
    """Merge engine outputs. Returns a TriageOutput-compatible dict plus an
    `ensemble` diagnostics block. Never raises: malformed LLM output falls
    back to the local result."""
    if not llm or not isinstance(llm, dict) or "error" in llm:
        return {**local, "ensemble": {
            "engines": ["local"],
            "local_confidence": local.get("confidence"),
            "llm_confidence": None,
            "agreement": None,
            "disagreement_flag": False,
            "mode": "offline_local_only",
        }}

    agreement = agreement_score(local, llm)

    local_sev = local.get("severity", "medium")
    raw_llm_sev = llm.get("severity")
    llm_sev = raw_llm_sev if isinstance(raw_llm_sev, str) and raw_llm_sev in SEVERITY_LEVELS else local_sev
    distance = _severity_distance(local_sev, llm_sev)

    # Safety-first: on disagreement take the more severe level.
    final_severity = max(local_sev, llm_sev, key=lambda s: _SEVERITY_INDEX.get(s, 1))
    disagreement_flag = distance >= 2

    # Confidence: noisy-or combination, reinforced or dampened by agreement.
    c_local = float(local.get("confidence") or 0.0)
    c_llm = float(llm.get("confidence") or 0.0)
    combined = 1.0 - (1.0 - c_local) * (1.0 - c_llm)
    if agreement >= 0.8:
        combined = min(combined + 0.05, 0.97)
    elif disagreement_flag:
        combined *= 0.6
    confidence = round(max(combined, 0.05), 2)

    people_local = local.get("people_at_risk")
    people_llm = llm.get("people_at_risk")
    people_conflict = (
        people_local and people_llm and abs(int(people_local) - int(people_llm)) > max(2, int(people_llm) * 0.5)
    )

    final = {
        "incident_type": llm.get("incident_type") or local.get("incident_type"),
        "severity": final_severity,
        "people_at_risk": people_llm if people_llm is not None else people_local,
        "vulnerable_people": llm.get("vulnerable_people") or local.get("vulnerable_people"),
        "medical_need": bool(llm.get("medical_need")) or bool(local.get("medical_need")),
        "immediate_needs": sorted(set(local.get("immediate_needs", [])) | set(llm.get("immediate_needs", []))),
        "evidence_quality": max(float(local.get("evidence_quality") or 0.0), float(llm.get("evidence_quality") or 0.0)),
        "confidence": confidence,
        "reason_codes": sorted(set(local.get("reason_codes", [])) | set(llm.get("reason_codes", []))),
        "ensemble": {
            "engines": ["local", "llm"],
            "local_confidence": local.get("confidence"),
            "llm_confidence": llm.get("confidence"),
            "agreement": agreement,
            "disagreement_flag": disagreement_flag,
            "people_count_conflict": bool(people_conflict),
            "mode": "ensemble",
        },
    }
    if disagreement_flag:
        final["reason_codes"].append("ensemble_severity_disagreement")
    if people_conflict:
        final["reason_codes"].append("ensemble_people_count_conflict")
    return final
