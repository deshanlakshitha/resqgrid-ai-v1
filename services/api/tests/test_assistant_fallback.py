"""Tests for assistant degraded-mode fallback when the LLM backend fails."""

import pytest

import app.services.assistant_service as svc
from app.adapters.ai_adapter import MockAIAdapter
from app.schemas.schemas import AssistantQuery


class _FailingAdapter:
    """Stand-in for GeminiAIAdapter that simulates a provider outage."""

    async def complete(self, prompt: str, response_format: str = "text"):
        raise RuntimeError("simulated LLM outage")


def _no_context(monkeypatch, incidents=None, hazards=None, resources=None, pending=0):
    monkeypatch.setattr(
        svc, "_gather_context",
        lambda db: _async_ctx(incidents or [], hazards or [], resources or [], pending),
    )


class _Ctx:
    def __init__(self, value):
        self.value = value

    def __await__(self):
        yield
        return self.value


def _async_ctx(incidents, hazards, resources, pending):
    return _Ctx((incidents, hazards, resources, pending))


@pytest.mark.asyncio
async def test_llm_failure_falls_back_to_database_answer(monkeypatch):
    """When the provider raises, the assistant must still answer from the DB."""
    monkeypatch.setattr(svc, "get_ai_adapter", lambda: _FailingAdapter())
    _no_context(monkeypatch)

    result = await svc.process_assistant_query(
        db=None, query=AssistantQuery(question="what is happening?"), current_user=None
    )

    assert "operations database" in result.answer
    assert result.confidence == 0.6


@pytest.mark.asyncio
async def test_llm_failure_answers_critical_incidents_question(monkeypatch):
    """The exact reported failing question must produce a useful answer."""
    from app.models.incident import Incident, IncidentSeverity, IncidentStatus, IncidentType

    incident = Incident(
        title="Flash flood at Bambalapitiya",
        description="water rising",
        incident_type=IncidentType.FLOOD,
        severity=IncidentSeverity.CRITICAL,
        status=IncidentStatus.REPORTED,
        address="Bambalapitiya",
        latitude=6.91,
        longitude=79.85,
    )
    monkeypatch.setattr(svc, "get_ai_adapter", lambda: _FailingAdapter())
    _no_context(monkeypatch, incidents=[incident])

    result = await svc.process_assistant_query(
        db=None, query=AssistantQuery(question="current critical incidents"), current_user=None
    )

    assert "Flash flood at Bambalapitiya" in result.answer


@pytest.mark.asyncio
async def test_mock_adapter_path_unchanged(monkeypatch):
    """Without an API key the deterministic path keeps its original behavior."""
    monkeypatch.setattr(svc, "get_ai_adapter", lambda: MockAIAdapter())
    _no_context(monkeypatch)

    result = await svc.process_assistant_query(
        db=None, query=AssistantQuery(question="how many incidents?"), current_user=None
    )

    assert "operations database" not in result.answer
    assert result.confidence == 0.92
