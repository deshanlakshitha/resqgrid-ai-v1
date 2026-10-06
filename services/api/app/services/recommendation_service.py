"""Resource Recommendation Service — matches incidents to available resources."""

import math
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.incident import Incident
from app.models.resource import Resource, ResourceStatus
from app.models.entities import Recommendation, RecommendationStatus, Hazard, HazardStatus


def _haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points in km."""
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _point_to_segment_distance_km(
    lat_a: float, lon_a: float,
    lat_b: float, lon_b: float,
    lat_p: float, lon_p: float,
) -> float:
    """Shortest great-circle distance from point P to the line segment AB, in km."""
    # Project the point onto the segment in Euclidean lat/lng space; good enough for small distances.
    ax, ay = lon_a, lat_a
    bx, by = lon_b, lat_b
    px, py = lon_p, lat_p

    abx, aby = bx - ax, by - ay
    ab_len_sq = abx * abx + aby * aby
    if ab_len_sq == 0:
        return _haversine_distance_km(lat_a, lon_a, lat_p, lon_p)

    t = max(0, min(1, ((px - ax) * abx + (py - ay) * aby) / ab_len_sq))
    proj_lat = ay + t * aby
    proj_lon = ax + t * abx
    return _haversine_distance_km(proj_lat, proj_lon, lat_p, lon_p)


def _estimate_eta_minutes(distance_km: float, hazard_penalty: float = 0.0) -> float:
    """Rough ETA estimate: assume average 40 km/h in emergency conditions, plus hazard delay."""
    base_minutes = (distance_km / 40) * 60
    return round(base_minutes * (1 + hazard_penalty) + hazard_penalty * 10, 1)


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


async def _get_active_hazards(db: AsyncSession) -> list[Hazard]:
    result = await db.execute(
        select(Hazard).where(Hazard.is_deleted == False, Hazard.status == HazardStatus.ACTIVE)
    )
    return result.scalars().all()


def _calculate_hazard_penalty(
    resource_lat: float, resource_lon: float,
    incident_lat: float, incident_lon: float,
    hazards: list[Hazard],
) -> tuple[float, list[str]]:
    """
    Calculate a route penalty based on active hazards between resource and incident.
    Returns (penalty_factor, list of hazard warnings).
    """
    warnings = []
    total_penalty = 0.0

    for hazard in hazards:
        if hazard.latitude is None or hazard.longitude is None:
            continue
        distance_to_route = _point_to_segment_distance_km(
            resource_lat, resource_lon,
            incident_lat, incident_lon,
            hazard.latitude, hazard.longitude,
        )
        radius_km = (hazard.radius_meters or 0) / 1000.0
        buffer_km = max(radius_km, 0.1)

        if distance_to_route <= buffer_km:
            severity_multiplier = {"critical": 1.0, "high": 0.6, "medium": 0.35, "low": 0.15}.get(hazard.severity, 0.3)
            overlap = max(0, (buffer_km - distance_to_route) / buffer_km)
            penalty = round(severity_multiplier * overlap, 2)
            total_penalty += penalty
            warnings.append(
                f"Route near {hazard.hazard_type.value} hazard '{hazard.title}' (~{distance_to_route:.2f} km)"
            )

    return min(total_penalty, 1.0), warnings


async def generate_resource_recommendations(db: AsyncSession, incident: Incident) -> list[dict]:
    """
    Generate resource recommendations for an incident.
    Returns a list of recommendations sorted by compatibility score.
    All recommendations require human approval.
    """
    needed_types = INCIDENT_RESOURCE_MAP.get(incident.incident_type.value, ["rescue_team"])
    active_hazards = await _get_active_hazards(db)

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

        hazard_penalty, hazard_warnings = _calculate_hazard_penalty(
            resource.latitude, resource.longitude,
            incident.latitude, incident.longitude,
            active_hazards,
        )

        eta = _estimate_eta_minutes(distance, hazard_penalty)
        is_preferred_type = resource.resource_type.value in needed_types
        confidence = 0.9 if is_preferred_type else 0.5
        confidence -= min(distance / 100, 0.3)  # Distance penalty
        confidence -= hazard_penalty * 0.35  # Hazard penalty
        confidence = max(confidence, 0.1)

        compatibility_reasons = []
        if is_preferred_type:
            compatibility_reasons.append(f"Resource type '{resource.resource_type.value}' matches incident type")
        compatibility_reasons.append(f"Distance: {distance:.1f} km")
        compatibility_reasons.append(f"ETA: {eta} minutes")

        if resource.capabilities:
            compatibility_reasons.append(f"Capabilities: {', '.join(resource.capabilities)}")

        if hazard_warnings:
            compatibility_reasons.append("Route conditions: " + "; ".join(hazard_warnings))

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
            reasoning=f"Selected {resource.name} ({resource.resource_type.value}) based on proximity, type compatibility, and active hazard conditions.",
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
            "hazard_penalty": hazard_penalty,
        })

    # Sort by confidence descending
    recommendations.sort(key=lambda r: r["confidence"], reverse=True)

    # Add alternatives reference
    for i, rec in enumerate(recommendations):
        rec["alternatives"] = [r["resource_name"] for r in recommendations if r["id"] != rec["id"]][:3]

    return recommendations[:5]  # Top 5 recommendations
