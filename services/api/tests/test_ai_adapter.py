"""Tests for AI adapter interface."""

import pytest
from app.adapters.ai_adapter import MockAIAdapter, get_ai_adapter


class TestMockAIAdapter:
    """Test the mock AI adapter."""

    @pytest.mark.asyncio
    async def test_mock_json_response(self):
        adapter = MockAIAdapter()
        result = await adapter.complete("test prompt", response_format="json")
        assert isinstance(result, dict)
        assert "severity" in result
        assert "confidence" in result
        assert "reason_codes" in result

    @pytest.mark.asyncio
    async def test_mock_text_response(self):
        adapter = MockAIAdapter()
        result = await adapter.complete("test prompt", response_format="text")
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_mock_triage_schema_compatible(self):
        """Mock output should be compatible with TriageOutput schema."""
        from app.schemas.schemas import TriageOutput

        adapter = MockAIAdapter()
        result = await adapter.complete("test", response_format="json")
        # This should not raise a validation error
        validated = TriageOutput(**result)
        assert validated.severity in ("low", "medium", "high", "critical")
        assert 0 <= validated.confidence <= 1


class TestAdapterSelection:
    """Test adapter factory selection."""

    def test_returns_mock_without_api_key(self):
        """Without API key, should return MockAIAdapter."""
        adapter = get_ai_adapter()
        assert isinstance(adapter, MockAIAdapter)
