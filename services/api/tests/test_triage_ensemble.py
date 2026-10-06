"""Tests for the local triage engine and the LLM ensemble merger."""

from types import SimpleNamespace

from app.ai.triage.ensemble import agreement_score, merge_ensemble
from app.ai.triage.local_engine import analyze_incident, analyze_text
from app.schemas.schemas import TriageOutput


def make_incident(title, description, itype="other", **fields):
    defaults = dict(
        title=title, description=description,
        incident_type=SimpleNamespace(value=itype),
        people_at_risk=None, vulnerable_people=None,
        medical_need=False, injuries_reported=None,
    )
    defaults.update(fields)
    return SimpleNamespace(**defaults)


class TestLocalEngine:
    def test_flood_with_people_count(self):
        result = analyze_text(
            "Flash flood", "Water rising rapidly, 12 people trapped in homes", "flood",
        )
        assert result["incident_type"] == "flood"
        assert result["people_at_risk"] == 12
        assert result["severity"] in ("high", "critical")
        assert "evacuation" in result["immediate_needs"] or "rescue_extraction" in result["immediate_needs"]
        assert "flood_signal" in result["reason_codes"] or "water_rising" in result["reason_codes"]

    def test_fire_detection(self):
        result = analyze_text("Building on fire", "Smoke and flames visible on the second floor", "other")
        assert result["incident_type"] == "fire"
        assert result["severity"] in ("medium", "high", "critical")

    def test_negation_suppresses_signal(self):
        result = analyze_text("Strange smell", "There is smoke but no fire, situation calm", "other")
        assert result["incident_type"] == "other"
        assert result["severity"] in ("low", "medium")

    def test_deescalator_reduces_severity(self):
        result = analyze_text("Small fire", "Minor fire in a bin, already contained, no injuries", "fire")
        assert result["severity"] == "low"

    def test_vulnerable_people_detected(self):
        result = analyze_text("Flood rescue", "3 people including an elderly and a child stranded on the roof", "flood")
        assert result["vulnerable_people"] == 2
        assert result["people_at_risk"] == 3
        assert result["medical_need"] is False

    def test_medical_keywords(self):
        result = analyze_text("Medical emergency", "Victim unconscious, needs hospital and oxygen", "medical")
        assert result["medical_need"] is True
        assert result["severity"] == "critical"
        assert "medical" in result["immediate_needs"]

    def test_earthquake_collapse(self):
        result = analyze_text("Earthquake", "Building collapsed, multiple people trapped in rubble", "earthquake")
        assert result["incident_type"] == "earthquake"
        assert result["severity"] == "critical"

    def test_type_refinement_with_strong_evidence(self):
        result = analyze_text("Strange smell", "Gas leak reported near the school, strong chemical odor", "other")
        assert result["incident_type"] == "hazmat"
        assert any(code.startswith("type_refined") for code in result["reason_codes"])

    def test_single_person_count(self):
        result = analyze_text("Accident", "A person injured after a car crash on the highway", "accident")
        assert result["people_at_risk"] == 1

    def test_deterministic(self):
        args = ("Flood", "Water is rising, 5 families evacuated, elderly residents present", "flood")
        assert analyze_text(*args) == analyze_text(*args)

    def test_output_validates_against_schema(self):
        result = analyze_text("Fire", "Building burning with smoke and flames", "fire")
        TriageOutput(**{k: v for k, v in result.items() if k != "engine"})

    def test_incident_structured_fields_override(self):
        incident = make_incident(
            "Flood report", "Water everywhere", "flood",
            people_at_risk=30, medical_need=True, injuries_reported=2,
        )
        result = analyze_incident(incident)
        assert result["people_at_risk"] == 30
        assert result["medical_need"] is True

    def test_no_signals_low_confidence(self):
        result = analyze_text("Routine check", "Everything looks normal today", "other")
        assert result["confidence"] <= 0.35
        assert result["severity"] == "low"


def local_result(severity="high", itype="flood", confidence=0.8, people=10):
    return {
        "incident_type": itype, "severity": severity, "people_at_risk": people,
        "vulnerable_people": None, "medical_need": False, "immediate_needs": ["evacuation"],
        "evidence_quality": 0.7, "confidence": confidence, "reason_codes": ["flood_signal"],
        "engine": "local_lexicon_v1",
    }


class TestEnsemble:
    def test_offline_returns_local_only(self):
        merged = merge_ensemble(local_result(), None)
        assert merged["ensemble"]["mode"] == "offline_local_only"
        assert merged["ensemble"]["engines"] == ["local"]
        assert merged["severity"] == "high"
        TriageOutput(**{k: v for k, v in merged.items() if k != "ensemble"})

    def test_error_dict_falls_back_to_local(self):
        merged = merge_ensemble(local_result(), {"error": "Invalid JSON", "raw": "..."})
        assert merged["ensemble"]["mode"] == "offline_local_only"

    def test_agreement_boosts_confidence(self):
        llm = {**local_result(), "confidence": 0.9, "reason_codes": ["llm_signal"]}
        merged = merge_ensemble(local_result(confidence=0.8), llm)
        assert merged["ensemble"]["agreement"] >= 0.8
        assert merged["confidence"] > 0.9
        assert merged["ensemble"]["disagreement_flag"] is False
        assert "llm_signal" in merged["reason_codes"]

    def test_severity_disagreement_escalates_and_flags(self):
        llm = {**local_result(severity="low", confidence=0.7)}
        merged = merge_ensemble(local_result(severity="critical"), llm)
        assert merged["severity"] == "critical"
        assert merged["ensemble"]["disagreement_flag"] is True
        assert "ensemble_severity_disagreement" in merged["reason_codes"]
        # Disagreement dampens confidence vs the agreeing case.
        agreeing = merge_ensemble(local_result(severity="critical"), {**llm, "severity": "critical"})
        assert merged["confidence"] < agreeing["confidence"]

    def test_people_count_conflict_detected(self):
        llm = {**local_result(), "people_at_risk": 60}
        merged = merge_ensemble(local_result(people=10), llm)
        assert merged["ensemble"]["people_count_conflict"] is True
        assert merged["people_at_risk"] == 60

    def test_agreement_score_symmetric(self):
        a = local_result(severity="high", itype="fire")
        b = {**local_result(severity="high", itype="fire")}
        assert agreement_score(a, b) == 1.0
