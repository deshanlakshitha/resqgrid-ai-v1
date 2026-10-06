# ResQGrid AI — AI Integration Setup Guide

This guide covers the AI triage and command assistant configuration.

---

## Overview

ResQGrid AI uses Alibaba Cloud Model Studio (Qwen) for:
1. **Incident Triage** — Extract structured data from incident reports
2. **Command Assistant** — Natural language queries about the emergency situation
3. **Evidence Analysis** — Image analysis (future phase)

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌──────────────────┐
│  API Route  │────▶│ Triage       │────▶│  AI Adapter      │
│             │     │ Service      │     │  Interface       │
└─────────────┘     └──────────────┘     └────────┬─────────┘
                                                   │
                                    ┌──────────────┼──────────────┐
                                    ▼                             ▼
                            ┌──────────────┐             ┌──────────────┐
                            │ Model Studio  │             │  Mock        │
                            │ Adapter       │             │  Adapter     │
                            │ (Qwen API)   │             │  (Dev/Test)  │
                            └──────────────┘             └──────────────┘
```

## AI Adapter Interface

All AI providers are behind an interface so models can be swapped:

```python
class AIAdapter(ABC):
    async def complete(self, prompt: str, response_format: str = "text") -> dict | str:
        ...
```

### Available Adapters

| Adapter | Usage | Requirements |
|---------|-------|-------------|
| `ModelStudioAdapter` | Production AI via Qwen | DASHSCOPE_API_KEY |
| `MockAIAdapter` | Development/testing | None (automatic fallback) |

The adapter is selected automatically based on configuration:
- If `DASHSCOPE_API_KEY` is set → uses Model Studio
- Otherwise → uses Mock adapter

## Setup: Alibaba Cloud Model Studio

### Step 1: Get API Key

1. Visit https://www.alibabacloud.com/help/en/model-studio/get-api-key
2. Sign up for Alibaba Cloud account
3. Navigate to Model Studio console
4. Create an API key
5. Copy the key

### Step 2: Configure Environment

Add to your `.env` file:

```env
DASHSCOPE_API_KEY=sk-your-actual-api-key
MODEL_STUDIO_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
MODEL_STUDIO_MODEL=qwen-plus
```

### Step 3: Available Models

| Model | Best For | Notes |
|-------|----------|-------|
| `qwen-plus` | Triage, assistant | Good balance of speed and quality |
| `qwen-turbo` | Fast triage | Lower cost, faster response |
| `qwen-max` | Complex analysis | Highest quality, slower |
| `qwen-vl-plus` | Image analysis | Vision + language model |

### Step 4: Test

```bash
# Start the API
uvicorn app.main:app --reload

# Test triage (after login):
curl -X POST http://localhost:8000/api/v1/incidents/{id}/triage \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Mock Mode (Development)

Without an API key, the system uses mock responses:

```json
{
  "incident_type": "flood",
  "severity": "high",
  "people_at_risk": 15,
  "vulnerable_people": 5,
  "medical_need": true,
  "immediate_needs": ["evacuation", "medical", "shelter"],
  "evidence_quality": 0.8,
  "confidence": 0.85,
  "reason_codes": ["rapid_water_rise", "vulnerable_population", "medical_need"]
}
```

## AI Safety Rules

- **Never** let AI make autonomous dispatch decisions
- **Always** validate AI output against Pydantic schemas
- **Always** require human approval for high-impact actions
- **Never** expose restricted personal data through the assistant
- **Never** trust LLM output as executable authorization
- Return `null`/`unknown` for missing information (never invent)
- Treat citizen reports as claims, not verified facts
- Include confidence scores separately from severity

## Prompt Engineering

The triage prompt includes:
1. Clear role definition ("emergency triage AI")
2. Exact output schema specification
3. Safety rules (no invented data, no diagnoses)
4. Structured incident context
5. Reason code requirements

## Response Validation

All AI output is validated by Pydantic before use:

```python
class TriageOutput(BaseModel):
    severity: str = Field(..., pattern="^(low|medium|high|critical)$")
    people_at_risk: Optional[int] = Field(None, ge=0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    ...
```

Invalid AI output is rejected and logged.

## References

- Model Studio: https://www.alibabacloud.com/help/en/model-studio/
- Qwen API: https://www.alibabacloud.com/help/en/model-studio/qwen-api-reference
- Models: https://www.alibabacloud.com/help/en/model-studio/models
