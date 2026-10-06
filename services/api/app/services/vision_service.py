"""AI Vision Service — analyzes emergency evidence images."""

import base64
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.ai_adapter import get_ai_adapter
from app.models.entities import Evidence


VISION_PROMPT = """You are an emergency response image analyst. Analyze the provided image for disaster-response signals.

Return a JSON object with exactly these fields:
- scene_description (string): a concise description of what is visible.
- detected_signals (array of strings): specific signals such as flooded_road, standing_water, smoke, fire, damaged_structure, blocked_route, fallen_tree, debris, vehicle_accident, people_stranded, landslide, downed_power_line, or none.
- severity_hint (string): one of low/medium/high/critical.
- estimated_people_at_risk (integer or null): only if people are clearly visible and countable; otherwise null.
- reasoning (string): short explanation of what led to the conclusions.
- confidence (float 0-1): overall confidence in the analysis.

Rules:
- Do not invent details not visible in the image.
- If the image is unclear, return low confidence and state uncertainty.
- Treat the output as decision support, not verified fact.
"""


def _image_mime_type(filename: str | None) -> str:
    ext = (filename or "").lower().split(".")[-1] if filename else ""
    return {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "webp": "image/webp",
        "gif": "image/gif",
    }.get(ext, "image/jpeg")


async def analyze_evidence_image(evidence: Evidence) -> dict:
    """
    Run AI vision analysis on an evidence image.
    Works with remote URLs (http/https), local /uploads/ paths, or base64 data URLs.
    Returns a dict matching the JSON schema in VISION_PROMPT.
    """
    adapter = get_ai_adapter()

    file_url = evidence.file_url or ""

    # If the URL is a remote URL we can pass it directly to multimodal models
    if file_url.startswith(("http://", "https://")):
        image_url = file_url
    else:
        # Try to read from local filesystem under the api service root
        import os
        
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        local_path = file_url if file_url.startswith("/uploads/") else f"/uploads/{file_url.lstrip('/')}"
        full_path = os.path.join(base_dir, local_path.lstrip("/"))

        if not os.path.exists(full_path):
            return {
                "scene_description": "Image file not available for analysis.",
                "detected_signals": ["none"],
                "severity_hint": "low",
                "estimated_people_at_risk": None,
                "reasoning": "Could not locate the uploaded image file on the server.",
                "confidence": 0.0,
                "analyzed_at": datetime.now(timezone.utc).isoformat(),
            }

        with open(full_path, "rb") as f:
            image_bytes = f.read()
        mime = _image_mime_type(evidence.file_name)
        image_url = f"data:{mime};base64,{base64.b64encode(image_bytes).decode('utf-8')}"

    result = await adapter.analyze_image(image_url=image_url, prompt=VISION_PROMPT, response_format="json")

    if isinstance(result, dict) and "error" in result:
        return {
            "scene_description": "AI analysis failed.",
            "detected_signals": ["none"],
            "severity_hint": "low",
            "estimated_people_at_risk": None,
            "reasoning": result.get("raw", result["error"]),
            "confidence": 0.0,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
        }

    analysis = result if isinstance(result, dict) else {"raw_response": str(result)}
    analysis.setdefault("scene_description", "No description provided.")
    analysis.setdefault("detected_signals", [])
    analysis.setdefault("severity_hint", "low")
    analysis.setdefault("estimated_people_at_risk", None)
    analysis.setdefault("reasoning", "")
    analysis.setdefault("confidence", 0.0)
    analysis["analyzed_at"] = datetime.now(timezone.utc).isoformat()
    analysis["model"] = getattr(adapter, "model", "mock")
    return analysis


async def run_vision_analysis_for_evidence(db: AsyncSession, evidence_id: str) -> Evidence:
    """Fetch evidence, run AI vision analysis, and persist the result."""
    from sqlalchemy import select
    from uuid import UUID

    result = await db.execute(select(Evidence).where(Evidence.id == UUID(evidence_id), Evidence.is_deleted == False))
    evidence = result.scalar_one_or_none()
    if not evidence:
        raise ValueError("Evidence not found")

    analysis = await analyze_evidence_image(evidence)
    evidence.ai_analysis = analysis
    await db.flush()
    await db.refresh(evidence)
    return evidence
