"""
AI Adapter Interface — abstracts the AI provider so models can be swapped.

Currently supports:
- Alibaba Cloud Model Studio / Qwen (via OpenAI-compatible API)
- Mock adapter (for development/testing without API keys)
"""

import json
from abc import ABC, abstractmethod

import httpx

from app.core.config import settings


class AIAdapter(ABC):
    """Abstract base class for AI model adapters."""

    @abstractmethod
    async def complete(self, prompt: str, response_format: str = "text") -> dict | str:
        """Send a prompt and return the response."""
        ...


class ModelStudioAdapter(AIAdapter):
    """Alibaba Cloud Model Studio / Qwen adapter using OpenAI-compatible API."""

    def __init__(self):
        self.base_url = settings.MODEL_STUDIO_BASE_URL
        self.api_key = settings.DASHSCOPE_API_KEY
        self.model = settings.MODEL_STUDIO_MODEL

    async def complete(self, prompt: str, response_format: str = "text") -> dict | str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a helpful emergency response AI assistant. Always respond with valid JSON when requested."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 2000,
        }

        if response_format == "json":
            payload["response_format"] = {"type": "json_object"}

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        content = data["choices"][0]["message"]["content"]

        if response_format == "json":
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {"error": "Invalid JSON response from AI", "raw": content}

        return content


class MockAIAdapter(AIAdapter):
    """Mock adapter for development and testing without API keys."""

    async def complete(self, prompt: str, response_format: str = "text") -> dict | str:
        if response_format == "json":
            return {
                "incident_type": "flood",
                "severity": "high",
                "people_at_risk": 15,
                "vulnerable_people": 5,
                "medical_need": True,
                "immediate_needs": ["evacuation", "medical", "shelter"],
                "evidence_quality": 0.8,
                "confidence": 0.85,
                "reason_codes": ["rapid_water_rise", "vulnerable_population", "medical_need"],
            }
        return "This is a mock AI response. Configure DASHSCOPE_API_KEY for real AI responses."


def get_ai_adapter() -> AIAdapter:
    """Factory: return the appropriate AI adapter based on configuration."""
    if settings.DASHSCOPE_API_KEY and settings.DASHSCOPE_API_KEY != "your-dashscope-api-key":
        return ModelStudioAdapter()
    return MockAIAdapter()
