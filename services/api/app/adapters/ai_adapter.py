"""
AI Adapter Interface — abstracts the AI provider so models can be swapped.

Currently supports:
- Google Gemini (via REST API)
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
        """Send a text prompt and return the response."""
        ...

    @abstractmethod
    async def analyze_image(self, image_url: str, prompt: str, response_format: str = "text") -> dict | str:
        """Send an image (URL or base64 data URL) plus a prompt and return the response."""
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

    async def analyze_image(self, image_url: str, prompt: str, response_format: str = "text") -> dict | str:
        """Analyze an image using a multimodal model (Qwen-VL compatible)."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an emergency response image analyst. Respond with valid JSON when requested.",
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                },
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

    async def analyze_image(self, image_url: str, prompt: str, response_format: str = "text") -> dict | str:
        """Return a realistic mock vision analysis for development."""
        if response_format == "json":
            return {
                "scene_description": "Mock analysis: image shows standing water on a residential street with a partially submerged vehicle. Visible debris suggests recent flooding.",
                "detected_signals": ["flooded_road", "standing_water", "vehicle_accident", "debris"],
                "severity_hint": "high",
                "estimated_people_at_risk": 2,
                "reasoning": "Water covers the road surface, a vehicle is stalled, and debris is scattered. These are consistent with flash-flood conditions.",
                "confidence": 0.78,
            }
        return "Mock image analysis: flooded road detected. Configure DASHSCOPE_API_KEY for real AI vision analysis."


class GeminiAIAdapter(AIAdapter):
    """Google Gemini adapter using the Gemini REST API."""

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model = settings.GEMINI_MODEL
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}"

    async def complete(self, prompt: str, response_format: str = "text") -> dict | str:
        payload: dict = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 2000,
            },
        }

        if response_format == "json":
            payload["generationConfig"]["responseMimeType"] = "application/json"

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}:generateContent?key={self.api_key}",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        content = data["candidates"][0]["content"]["parts"][0]["text"]

        if response_format == "json":
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {"error": "Invalid JSON response from AI", "raw": content}

        return content

    async def analyze_image(self, image_url: str, prompt: str, response_format: str = "text") -> dict | str:
        """Analyze an image using Gemini multimodal."""
        # Fetch image and encode as base64 for Gemini
        import base64
        async with httpx.AsyncClient(timeout=30.0) as client:
            img_response = await client.get(image_url)
            img_response.raise_for_status()
            image_data = base64.b64encode(img_response.content).decode("utf-8")
            mime_type = img_response.headers.get("content-type", "image/jpeg").split(";")[0]

        payload: dict = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": mime_type, "data": image_data}},
                ]
            }],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 2000,
            },
        }

        if response_format == "json":
            payload["generationConfig"]["responseMimeType"] = "application/json"

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}:generateContent?key={self.api_key}",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        content = data["candidates"][0]["content"]["parts"][0]["text"]

        if response_format == "json":
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {"error": "Invalid JSON response from AI", "raw": content}

        return content


def get_ai_adapter() -> AIAdapter:
    """Factory: return the appropriate AI adapter based on configuration."""
    if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "":
        return GeminiAIAdapter()
    if settings.DASHSCOPE_API_KEY and settings.DASHSCOPE_API_KEY != "your-dashscope-api-key":
        return ModelStudioAdapter()
    return MockAIAdapter()
