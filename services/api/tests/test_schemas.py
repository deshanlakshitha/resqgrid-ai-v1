"""Tests for Pydantic schema validation."""

import pytest
from pydantic import ValidationError

from app.schemas.schemas import TriageOutput, IncidentCreate, PriorityScore


class TestTriageOutputValidation:
    """Test AI triage output validation."""

    def test_valid_triage_output(self):
        """Valid triage output should pass validation."""
        data = {
            "incident_type": "flood",
            "severity": "critical",
            "people_at_risk": 12,
            "vulnerable_people": 4,
            "medical_need": True,
            "immediate_needs": ["evacuation", "medical"],
            "evidence_quality": 0.86,
            "confidence": 0.91,
            "reason_codes": ["rapid_water_rise", "elderly_person"],
        }
        result = TriageOutput(**data)
        assert result.severity == "critical"
        assert result.confidence == 0.91

    def test_invalid_severity_rejected(self):
        """Invalid severity value should be rejected."""
        with pytest.raises(ValidationError):
            TriageOutput(severity="extreme", confidence=0.5)

    def test_confidence_out_of_range_rejected(self):
        """Confidence > 1.0 or < 0.0 should be rejected."""
        with pytest.raises(ValidationError):
            TriageOutput(severity="high", confidence=1.5)
        with pytest.raises(ValidationError):
            TriageOutput(severity="high", confidence=-0.1)

    def test_negative_people_rejected(self):
        """Negative people count should be rejected."""
        with pytest.raises(ValidationError):
            TriageOutput(severity="high", confidence=0.5, people_at_risk=-1)

    def test_minimal_triage_output(self):
        """Minimal valid output should pass."""
        result = TriageOutput(severity="low", confidence=0.1)
        assert result.severity == "low"
        assert result.medical_need == False
        assert result.immediate_needs == []


class TestIncidentCreateValidation:
    """Test incident creation validation."""

    def test_valid_incident(self):
        data = {
            "title": "Flash flood reported",
            "description": "Water rising rapidly near the bridge.",
            "latitude": 1.35,
            "longitude": 103.82,
        }
        result = IncidentCreate(**data)
        assert result.title == "Flash flood reported"

    def test_invalid_latitude_rejected(self):
        with pytest.raises(ValidationError):
            IncidentCreate(title="Test", description="Test", latitude=999, longitude=0)

    def test_invalid_longitude_rejected(self):
        with pytest.raises(ValidationError):
            IncidentCreate(title="Test", description="Test", latitude=0, longitude=999)

    def test_empty_title_rejected(self):
        with pytest.raises(ValidationError):
            IncidentCreate(title="", description="Test", latitude=1.0, longitude=1.0)
