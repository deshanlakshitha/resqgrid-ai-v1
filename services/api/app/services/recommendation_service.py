"""Resource Recommendation Service — matches incidents to available resources."""

import math
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.incident import Incident
from app.models.resource import Resource, ResourceStatus
from app.models.entities import Recommendation, RecommendationStatus


def _haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points in km."""
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _estimate_eta_minutes(distance_km: float) -> float:
    """Rough ETA estimate: assume average 40 km/h in emergency conditions."""
    return round((distance_km / 40) * 60, 1)


# Mapping incident types to resource types that can handle them
INCIDENT_RESOURCE_MAP = {
    "flood": ["rescue_boat", "helicopter", "rescue_team"],
    "fire": ["fire_truck", "rescue_team", "ambulance"],
    "earthquake": ["rescue_team", "ambulance", "medical_team", "helicopter"],
    "landslide": ["rescue_team", "fire_truck", "ambulance"],
    "accident": ["ambulance", "fire_truck", "medical_team"],
    "medical": ["ambulance", "medical_team"],
    "hazmat": ["fire_truck", "rescue_team"],
    "infrastructure": ["rescue_team", "supply_truck", "generator"],
    "other": ["rescue_team", "ambulance"],
}


async def generate_resource_recommendations(db: AsyncSession, incident: Incident) -> list[dict]:
    """
    Generate resource recommendations for an incident.
    Returns a list of recommendations sorted by compatibility score.
    All recommendations require human approval.
    """
    needed_types = INCIDENT_RESOURCE_MAP.get(incident.incident_type.value, ["rescue_team"])

    # Find available resources matching the needed types
    result = await db.execute(
        select(Resource).where(
            Resource.is_deleted == False,
            Resource.status == ResourceStatus.AVAILABLE,
            Resource.resource_type.in_(needed_types),
        )
    )
    candidates = result.scalars().all()

    if not candidates:
        # Fallback: find any available resource
        result = await db.execute(
            select(Resource).where(Resource.is_deleted == False, Resource.status == ResourceStatus.AVAILABLE)
        )
        candidates = result.scalars().all()

    recommendations = []
    for resource in candidates:
        distance = _haversine_distance_km(
            incident.latitude, incident.longitude,
            resource.latitude, resource.longitude,
        )

        # Check range constraint
        if resource.max_range_km and distance > resource.max_range_km:
            continue

        eta = _estimate_eta_minutes(distance)
        is_preferred_type = resource.resource_type.value in needed_types
        confidence = 0.9 if is_preferred_type else 0.5
        confidence -= min(distance / 100, 0.3)  # Distance penalty
        confidence = max(confidence, 0.1)

        compatibility_reasons = []
        if is_preferred_type:
            compatibility_reasons.append(f"Resource type '{resource.resource_type.value}' matches incident type")
        compatibility_reasons.append(f"Distance: {distance:.1f} km")
        compatibility_reasons.append(f"ETA: {eta} minutes")

        if resource.capabilities:
            compatibility_reasons.append(f"Capabilities: {', '.join(resource.capabilities)}")

        constraints = []
        if resource.operating_hours:
            constraints.append(f"Operating hours: {resource.operating_hours}")
        if resource.max_range_km:
            constraints.append(f"Max range: {resource.max_range_km} km")

        # Create recommendation in DB
        rec = Recommendation(
            incident_id=incident.id,
            resource_id=resource.id,
            status=RecommendationStatus.PENDING,
            confidence=round(confidence, 2),
            estimated_eta_minutes=eta,
            compatibility_reasons=compatibility_reasons,
            constraints=constraints if constraints else None,
            reasoning=f"Selected {resource.name} ({resource.resource_type.value}) based on proximity and type compatibility.",
            human_approval_required=True,
        )
        db.add(rec)
        await db.flush()

        recommendations.append({
            "id": str(rec.id),
            "incident_id": str(incident.id),
            "resource_id": str(resource.id),
            "resource_name": resource.name,
            "resource_type": resource.resource_type.value,
            "confidence": rec.confidence,
            "estimated_eta_minutes": eta,
            "distance_km": round(distance, 1),
            "compatibility_reasons": compatibility_reasons,
            "constraints": constraints,
            "human_approval_required": True,
        })

    # Sort by confidence descending
    recommendations.sort(key=lambda r: r["confidence"], reverse=True)

    # Add alternatives reference
    for i, rec in enumerate(recommendations):
        rec["alternatives"] = [r["resource_name"] for r in recommendations if r["id"] != rec["id"]][:3]

    return recommendations[:5]  # Top 5 recommendations
