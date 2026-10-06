"""Tests for assistant degraded-mode fallback when the LLM backend fails."""

import pytest

import app.services.assistant_service as svc
from app.adapters.ai_adapter import MockAIAdapter
from app.schemas.schemas import AssistantQuery


class _FailingAdapter:
    """Stand-in for GeminiAIAdapter that simulates a provider outage."""

    async def complete(self, prompt: str, response_format: str = "text"):
        raise RuntimeError("simulated LLM outage")


class _CountingAdapter:
    """Stand-in that counts calls so tests can verify cache/cooldown behavior."""

    def __init__(self, fail: bool = False):
        self.calls = 0
        self.fail = fail

    async def complete(self, prompt: str, response_format: str = "text"):
        self.calls += 1
        if self.fail:
            raise RuntimeError("simulated LLM outage")
        return "LLM situation report"


@pytest.fixture(autouse=True)
def _reset_assistant_state():
    """Module-level cache/cooldown must not leak between tests."""
    svc._response_cache.clear()
    svc._llm_cooldown_until = 0.0
    yield
    svc._response_cache.clear()
    svc._llm_cooldown_until = 0.0


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


@pytest.mark.asyncio
async def test_degraded_wording_does_not_ask_for_api_key(monkeypatch):
    """Degraded-mode fallback must say 'temporarily unavailable', not 'configure a key'."""
    monkeypatch.setattr(svc, "get_ai_adapter", lambda: _FailingAdapter())
    _no_context(monkeypatch)

    result = await svc.process_assistant_query(
        db=None, query=AssistantQuery(question="something unusual"), current_user=None
    )

    assert "temporarily unavailable" in result.answer
    assert "once an AI API key is configured" not in result.answer


@pytest.mark.asyncio
async def test_repeat_questions_are_cached(monkeypatch):
    """Repeat questions within the TTL must not trigger new provider calls."""
    adapter = _CountingAdapter()
    monkeypatch.setattr(svc, "get_ai_adapter", lambda: adapter)
    _no_context(monkeypatch)

    question = AssistantQuery(question="what is happening?")
    first = await svc.process_assistant_query(db=None, query=question, current_user=None)
    second = await svc.process_assistant_query(db=None, query=question, current_user=None)

    assert adapter.calls == 1
    assert first.answer == second.answer == "LLM situation report"


@pytest.mark.asyncio
async def test_cooldown_skips_provider_calls_after_failure(monkeypatch):
    """After a provider failure, further questions skip the LLM call entirely."""
    adapter = _CountingAdapter(fail=True)
    monkeypatch.setattr(svc, "get_ai_adapter", lambda: adapter)
    _no_context(monkeypatch)

    await svc.process_assistant_query(
        db=None, query=AssistantQuery(question="how many incidents?"), current_user=None
    )
    assert adapter.calls == 1

    second = await svc.process_assistant_query(
        db=None, query=AssistantQuery(question="current critical incidents"), current_user=None
    )

    assert adapter.calls == 1
    assert "operations database" in second.answer
