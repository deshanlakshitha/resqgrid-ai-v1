"""Tests for the deterministic priority engine."""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock

# Import priority calculation
from app.services.priority_service import calculate_priority_score


def create_mock_incident(**kwargs):
    """Create a mock incident for testing."""
    incident = MagicMock()
    incident.severity = MagicMock()
    incident.severity.value = kwargs.get("severity", "medium")
    incident.incident_type = MagicMock()
    incident.incident_type.value = kwargs.get("incident_type", "flood")
    incident.medical_need = kwargs.get("medical_need", False)
    incident.people_at_risk = kwargs.get("people_at_risk", 0)
    incident.vulnerable_people = kwargs.get("vulnerable_people", 0)
    incident.injuries_reported = kwargs.get("injuries_reported", 0)
    incident.triage_confidence = kwargs.get("triage_confidence", 0.8)
    incident.triage_data = kwargs.get("triage_data", None)
    incident.created_at = kwargs.get("created_at", datetime.now(timezone.utc))
    return incident


class TestPriorityEngine:
    """Test the deterministic priority calculation."""

    def test_critical_incident_scores_high(self):
        """Critical incidents with medical need should score high."""
        incident = create_mock_incident(
            severity="critical",
            incident_type="flood",
            medical_need=True,
            people_at_risk=25,
            vulnerable_people=8,
            injuries_reported=3,
            triage_confidence=0.9,
        )
        result = calculate_priority_score(incident)
        assert result.score > 60
        assert "high_life_risk" in result.reason_codes
        assert "urgent_medical_need" in result.reason_codes

    def test_low_severity_scores_low(self):
        """Low severity incidents should score low."""
        incident = create_mock_incident(
            severity="low",
            incident_type="other",
            medical_need=False,
            people_at_risk=0,
            vulnerable_people=0,
            injuries_reported=0,
            triage_confidence=0.5,
        )
        result = calculate_priority_score(incident)
        assert result.score < 40

    def test_score_is_between_0_and_100(self):
        """Score must always be between 0 and 100."""
        for severity in ["low", "medium", "high", "critical"]:
            incident = create_mock_incident(severity=severity)
            result = calculate_priority_score(incident)
            assert 0 <= result.score <= 100

    def test_deterministic_same_input_same_output(self):
        """Same inputs must always produce the same output."""
        incident = create_mock_incident(
            severity="high",
            incident_type="fire",
            medical_need=True,
            people_at_risk=10,
        )
        result1 = calculate_priority_score(incident)
        result2 = calculate_priority_score(incident)
        assert result1.score == result2.score
        assert result1.components == result2.components

    def test_components_sum_with_weights(self):
        """Verify the weighted sum calculation."""
        incident = create_mock_incident(
            severity="critical",
            incident_type="earthquake",
            medical_need=True,
            people_at_risk=50,
        )
        result = calculate_priority_score(incident)
        # Verify all components are present
        assert "life_risk" in result.components
        assert "medical_urgency" in result.components
        assert "people_at_risk" in result.components
        assert "environmental_risk" in result.components
        assert "time_sensitivity" in result.components
        assert "evidence_confidence" in result.components
        # Verify weights
        assert sum(result.weights.values()) == pytest.approx(1.0)

    def test_reason_codes_generated(self):
        """Reason codes should be generated based on thresholds."""
        incident = create_mock_incident(
            severity="critical",
            incident_type="fire",
            medical_need=True,
            people_at_risk=50,
            vulnerable_people=10,
        )
        result = calculate_priority_score(incident)
        assert len(result.reason_codes) > 0
        assert isinstance(result.reason_codes, list)

    def test_vulnerable_population_reason_code(self):
        """Vulnerable population should trigger reason code."""
        incident = create_mock_incident(
            severity="medium",
            vulnerable_people=5,
        )
        result = calculate_priority_score(incident)
        assert "vulnerable_population" in result.reason_codes
