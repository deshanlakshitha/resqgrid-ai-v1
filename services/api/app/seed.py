"""Seed data: Sri Lanka disaster simulation for demo purposes.

Seeds Colombo-centered demo data with:
- 5 demo users (admin, dispatcher, responder, citizen)
- 20 incidents of various types and severities
- 30 resources
- 5 shelters
- 3 hospitals
- 8 hazards

Run: python -m app.seed
"""

import asyncio
from datetime import datetime, timezone, timedelta

from app.core.database import async_session_factory
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.models.incident import Incident, IncidentType, IncidentSeverity, IncidentStatus
from app.models.resource import Resource, ResourceType, ResourceStatus
from app.models.entities import Hazard, HazardType, HazardStatus


# ---- Demo Users ----
DEMO_USERS = [
    {"email": "admin@resqgrid.local", "username": "admin", "password": "admin123", "full_name": "System Admin", "role": UserRole.ADMIN, "organization": "ResQGrid HQ"},
    {"email": "dispatcher@resqgrid.local", "username": "dispatcher", "password": "dispatch123", "full_name": "Sarah Chen", "role": UserRole.DISPATCHER, "organization": "Emergency Operations Center"},
    {"email": "responder1@resqgrid.local", "username": "responder1", "password": "respond123", "full_name": "John Rivera", "role": UserRole.RESPONDER, "organization": "Fire Department"},
    {"email": "responder2@resqgrid.local", "username": "responder2", "password": "respond123", "full_name": "Maria Lopez", "role": UserRole.RESPONDER, "organization": "Medical Corps"},
    {"email": "citizen@resqgrid.local", "username": "citizen", "password": "citizen123", "full_name": "Alex Tan", "role": UserRole.CITIZEN, "organization": None},
]

# ---- Base coordinates: Colombo, Sri Lanka ----
BASE_LAT, BASE_LNG = 6.9271, 79.8612

# ---- 20 Incidents ----
DEMO_INCIDENTS = [
    {"title": "Flash flood at Bambalapitiya", "description": "Rapid water rise reported near the canal. Multiple families trapped on upper floors.", "type": IncidentType.FLOOD, "severity": IncidentSeverity.CRITICAL, "lat": BASE_LAT + 0.01, "lng": BASE_LNG + 0.02, "people": 25, "vulnerable": 8, "medical": True},
    {"title": "Building fire at Pettah Market", "description": "Large commercial building on fire. Thick black smoke visible from 2km away.", "type": IncidentType.FIRE, "severity": IncidentSeverity.CRITICAL, "lat": BASE_LAT - 0.005, "lng": BASE_LNG + 0.01, "people": 40, "vulnerable": 5, "medical": True},
    {"title": "Landslide on Kandy Road", "description": "Part of the hillside collapsed blocking the main road. Vehicles may be trapped.", "type": IncidentType.LANDSLIDE, "severity": IncidentSeverity.HIGH, "lat": BASE_LAT + 0.03, "lng": BASE_LNG - 0.01, "people": 10, "vulnerable": 2, "medical": True},
    {"title": "Multi-vehicle accident on Galle Road", "description": "5-vehicle pileup reported near Galle Face. At least 3 injuries visible.", "type": IncidentType.ACCIDENT, "severity": IncidentSeverity.HIGH, "lat": BASE_LAT - 0.02, "lng": BASE_LNG + 0.03, "people": 15, "vulnerable": 0, "medical": True},
    {"title": "Power outage in Colombo North", "description": "Entire neighborhood without power. Nursing home on life support affected.", "type": IncidentType.INFRASTRUCTURE, "severity": IncidentSeverity.HIGH, "lat": BASE_LAT + 0.02, "lng": BASE_LNG + 0.04, "people": 200, "vulnerable": 30, "medical": True},
    {"title": "Gas leak at Colombo Port", "description": "Strong gas smell near warehouse district. Evacuation may be needed.", "type": IncidentType.HAZMAT, "severity": IncidentSeverity.HIGH, "lat": BASE_LAT - 0.01, "lng": BASE_LNG - 0.02, "people": 50, "vulnerable": 0, "medical": False},
    {"title": "Person trapped in elevator", "description": "Elevator stuck between floors in apartment complex near Havelock City. Person reports difficulty breathing.", "type": IncidentType.OTHER, "severity": IncidentSeverity.MEDIUM, "lat": BASE_LAT + 0.005, "lng": BASE_LNG - 0.005, "people": 1, "vulnerable": 1, "medical": True},
    {"title": "Fallen tree blocking Duplication Road", "description": "Large tree down across the road near the school in Bambalapitiya.", "type": IncidentType.OTHER, "severity": IncidentSeverity.MEDIUM, "lat": BASE_LAT + 0.015, "lng": BASE_LNG + 0.015, "people": 0, "vulnerable": 0, "medical": False},
    {"title": "Water main break at Baseline Road", "description": "Water gushing from broken main. Street flooding. Water pressure lost for 3 blocks.", "type": IncidentType.INFRASTRUCTURE, "severity": IncidentSeverity.MEDIUM, "lat": BASE_LAT - 0.008, "lng": BASE_LNG + 0.008, "people": 100, "vulnerable": 10, "medical": False},
    {"title": "Medical emergency at Dehiwala Senior Center", "description": "Multiple elderly residents feeling unwell. Possible food poisoning.", "type": IncidentType.MEDICAL, "severity": IncidentSeverity.HIGH, "lat": BASE_LAT + 0.008, "lng": BASE_LNG + 0.025, "people": 12, "vulnerable": 12, "medical": True},
    {"title": "Roof collapse at Colombo Warehouse", "description": "Partial roof collapse after heavy rain. No injuries reported but structural concerns.", "type": IncidentType.INFRASTRUCTURE, "severity": IncidentSeverity.MEDIUM, "lat": BASE_LAT - 0.015, "lng": BASE_LNG - 0.015, "people": 5, "vulnerable": 0, "medical": False},
    {"title": "Car swept into Wellawatte canal", "description": "Vehicle with 2 occupants swept into canal during flash flood.", "type": IncidentType.FLOOD, "severity": IncidentSeverity.CRITICAL, "lat": BASE_LAT + 0.012, "lng": BASE_LNG + 0.018, "people": 2, "vulnerable": 0, "medical": True},
    {"title": "Kitchen fire at Galle Face restaurants", "description": "Grease fire spread to adjacent restaurants. All evacuated.", "type": IncidentType.FIRE, "severity": IncidentSeverity.MEDIUM, "lat": BASE_LAT - 0.003, "lng": BASE_LNG + 0.005, "people": 30, "vulnerable": 0, "medical": False},
    {"title": "Suspicious package at Fort Railway Station", "description": "Unattended bag at bus and rail terminal. Area cordoned off.", "type": IncidentType.OTHER, "severity": IncidentSeverity.MEDIUM, "lat": BASE_LAT + 0.002, "lng": BASE_LNG + 0.012, "people": 50, "vulnerable": 5, "medical": False},
    {"title": "Child missing near Bambalapitiya flood zone", "description": "Parent reports child missing near flooded area. Search needed.", "type": IncidentType.FLOOD, "severity": IncidentSeverity.CRITICAL, "lat": BASE_LAT + 0.018, "lng": BASE_LNG + 0.022, "people": 1, "vulnerable": 1, "medical": True},
    {"title": "Generator failure at National Hospital", "description": "Backup generator failed. ICU patients at risk.", "type": IncidentType.INFRASTRUCTURE, "severity": IncidentSeverity.CRITICAL, "lat": BASE_LAT - 0.01, "lng": BASE_LNG + 0.02, "people": 20, "vulnerable": 20, "medical": True},
    {"title": "Storm drain overflow at Slave Island", "description": "Storm drains overwhelmed. Water rising slowly on residential street.", "type": IncidentType.FLOOD, "severity": IncidentSeverity.MEDIUM, "lat": BASE_LAT + 0.007, "lng": BASE_LNG - 0.008, "people": 30, "vulnerable": 5, "medical": False},
    {"title": "Chemical spill at University of Colombo Lab", "description": "Unknown chemical spill in chemistry lab. Building evacuated.", "type": IncidentType.HAZMAT, "severity": IncidentSeverity.HIGH, "lat": BASE_LAT + 0.025, "lng": BASE_LNG + 0.01, "people": 25, "vulnerable": 0, "medical": True},
    {"title": "Bridge structural damage reported", "description": "Visible cracks on Kelani Bridge after earthquake tremor. Inspection needed.", "type": IncidentType.INFRASTRUCTURE, "severity": IncidentSeverity.HIGH, "lat": BASE_LAT - 0.005, "lng": BASE_LNG + 0.035, "people": 0, "vulnerable": 0, "medical": False},
    {"title": "Earthquake aftershock damage", "description": "Multiple reports of wall cracks and fallen debris after 4.5 magnitude aftershock in Kotte.", "type": IncidentType.EARTHQUAKE, "severity": IncidentSeverity.HIGH, "lat": BASE_LAT + 0.01, "lng": BASE_LNG + 0.01, "people": 50, "vulnerable": 15, "medical": True},
]

# ---- 30 Resources ----
DEMO_RESOURCES = [
    {"name": "Ambulance A-01", "type": ResourceType.AMBULANCE, "lat": BASE_LAT + 0.005, "lng": BASE_LNG, "capacity": 2, "caps": ["BLS", "ALS", "trauma"]},
    {"name": "Ambulance A-02", "type": ResourceType.AMBULANCE, "lat": BASE_LAT - 0.005, "lng": BASE_LNG + 0.01, "capacity": 2, "caps": ["BLS", "ALS"]},
    {"name": "Ambulance A-03", "type": ResourceType.AMBULANCE, "lat": BASE_LAT + 0.01, "lng": BASE_LNG + 0.015, "capacity": 2, "caps": ["BLS", "pediatric"]},
    {"name": "Fire Truck FT-01", "type": ResourceType.FIRE_TRUCK, "lat": BASE_LAT, "lng": BASE_LNG + 0.005, "capacity": 6, "caps": ["fire_suppression", "rescue", "hazmat"]},
    {"name": "Fire Truck FT-02", "type": ResourceType.FIRE_TRUCK, "lat": BASE_LAT - 0.01, "lng": BASE_LNG - 0.005, "capacity": 6, "caps": ["fire_suppression", "rescue"]},
    {"name": "Fire Truck FT-03", "type": ResourceType.FIRE_TRUCK, "lat": BASE_LAT + 0.02, "lng": BASE_LNG + 0.01, "capacity": 6, "caps": ["fire_suppression", "ladder"]},
    {"name": "Rescue Boat RB-01", "type": ResourceType.RESCUE_BOAT, "lat": BASE_LAT + 0.015, "lng": BASE_LNG + 0.02, "capacity": 8, "caps": ["water_rescue", "flood_evacuation"]},
    {"name": "Rescue Boat RB-02", "type": ResourceType.RESCUE_BOAT, "lat": BASE_LAT + 0.012, "lng": BASE_LNG + 0.025, "capacity": 6, "caps": ["water_rescue"]},
    {"name": "Helicopter H-01", "type": ResourceType.HELICOPTER, "lat": BASE_LAT + 0.03, "lng": BASE_LNG, "capacity": 4, "caps": ["aerial_rescue", "medical_evacuation", "surveillance"]},
    {"name": "Helicopter H-02", "type": ResourceType.HELICOPTER, "lat": BASE_LAT + 0.03, "lng": BASE_LNG + 0.01, "capacity": 3, "caps": ["medical_evacuation"]},
    {"name": "Rescue Team Alpha", "type": ResourceType.RESCUE_TEAM, "lat": BASE_LAT + 0.003, "lng": BASE_LNG + 0.003, "capacity": 10, "caps": ["urban_search_rescue", "rope_rescue", "confined_space"]},
    {"name": "Rescue Team Bravo", "type": ResourceType.RESCUE_TEAM, "lat": BASE_LAT - 0.007, "lng": BASE_LNG + 0.012, "capacity": 8, "caps": ["urban_search_rescue", "water_rescue"]},
    {"name": "Rescue Team Charlie", "type": ResourceType.RESCUE_TEAM, "lat": BASE_LAT + 0.015, "lng": BASE_LNG - 0.005, "capacity": 8, "caps": ["structural_assessment", "debris_removal"]},
    {"name": "Medical Team Med-1", "type": ResourceType.MEDICAL_TEAM, "lat": BASE_LAT - 0.008, "lng": BASE_LNG + 0.018, "capacity": 15, "caps": ["triage", "field_surgery", "stabilization"]},
    {"name": "Medical Team Med-2", "type": ResourceType.MEDICAL_TEAM, "lat": BASE_LAT + 0.01, "lng": BASE_LNG + 0.02, "capacity": 10, "caps": ["triage", "pediatric_care"]},
    {"name": "Supply Truck ST-01", "type": ResourceType.SUPPLY_TRUCK, "lat": BASE_LAT + 0.005, "lng": BASE_LNG - 0.01, "capacity": 5000, "caps": ["food", "water", "blankets"]},
    {"name": "Supply Truck ST-02", "type": ResourceType.SUPPLY_TRUCK, "lat": BASE_LAT - 0.01, "lng": BASE_LNG - 0.01, "capacity": 3000, "caps": ["medical_supplies", "sandbags"]},
    {"name": "Generator G-01", "type": ResourceType.GENERATOR, "lat": BASE_LAT + 0.002, "lng": BASE_LNG + 0.008, "capacity": 100, "caps": ["power_restoration", "emergency_power"]},
    {"name": "Generator G-02", "type": ResourceType.GENERATOR, "lat": BASE_LAT - 0.005, "lng": BASE_LNG + 0.025, "capacity": 200, "caps": ["hospital_backup", "power_restoration"]},
    {"name": "Drone D-01", "type": ResourceType.DRONE, "lat": BASE_LAT, "lng": BASE_LNG, "capacity": 0, "caps": ["surveillance", "damage_assessment", "thermal_imaging"]},
    {"name": "Drone D-02", "type": ResourceType.DRONE, "lat": BASE_LAT + 0.01, "lng": BASE_LNG + 0.01, "capacity": 0, "caps": ["surveillance", "delivery_small_items"]},
    # 5 Shelters
    {"name": "Viharamahadevi Park Shelter", "type": ResourceType.SHELTER, "lat": BASE_LAT + 0.02, "lng": BASE_LNG - 0.01, "capacity": 200, "caps": ["shelter", "food", "first_aid"]},
    {"name": "Royal College Gymnasium Shelter", "type": ResourceType.SHELTER, "lat": BASE_LAT - 0.015, "lng": BASE_LNG + 0.03, "capacity": 150, "caps": ["shelter", "food"]},
    {"name": "Sugathadasa Stadium Shelter", "type": ResourceType.SHELTER, "lat": BASE_LAT + 0.025, "lng": BASE_LNG + 0.03, "capacity": 500, "caps": ["shelter", "food", "medical", "parking"]},
    {"name": "St. Joseph's Church Hall Shelter", "type": ResourceType.SHELTER, "lat": BASE_LAT - 0.02, "lng": BASE_LNG - 0.01, "capacity": 80, "caps": ["shelter", "food"]},
    {"name": "Bandaranaike Memorial Hall Shelter", "type": ResourceType.SHELTER, "lat": BASE_LAT + 0.005, "lng": BASE_LNG + 0.04, "capacity": 1000, "caps": ["shelter", "food", "medical", "communications"]},
    # 3 Hospitals
    {"name": "National Hospital of Sri Lanka", "type": ResourceType.SHELTER, "lat": BASE_LAT - 0.01, "lng": BASE_LNG + 0.02, "capacity": 300, "caps": ["emergency", "surgery", "ICU", "trauma"]},
    {"name": "Lady Ridgeway Hospital", "type": ResourceType.SHELTER, "lat": BASE_LAT + 0.02, "lng": BASE_LNG + 0.035, "capacity": 200, "caps": ["emergency", "pediatric", "maternity"]},
    {"name": "Castle Street Hospital for Women", "type": ResourceType.SHELTER, "lat": BASE_LAT - 0.025, "lng": BASE_LNG + 0.015, "capacity": 150, "caps": ["trauma", "surgery", "burn_unit", "ICU"]},
    # Additional resources
    {"name": "Ambulance A-04", "type": ResourceType.AMBULANCE, "lat": BASE_LAT + 0.018, "lng": BASE_LNG - 0.008, "capacity": 2, "caps": ["BLS", "ALS"]},
]

# ---- Hazards & Blocked Roads ----
DEMO_HAZARDS = [
    {"type": HazardType.FLOOD, "title": "Flash Flood Zone — Bambalapitiya", "lat": BASE_LAT + 0.012, "lng": BASE_LNG + 0.02, "radius": 500, "severity": "critical"},
    {"type": HazardType.FIRE, "title": "Active Fire Zone — Pettah Market", "lat": BASE_LAT - 0.005, "lng": BASE_LNG + 0.01, "radius": 200, "severity": "high"},
    {"type": HazardType.ROAD_BLOCKED, "title": "Landslide Blockage — Kandy Road", "lat": BASE_LAT + 0.03, "lng": BASE_LNG - 0.01, "radius": 100, "severity": "high"},
    {"type": HazardType.ROAD_BLOCKED, "title": "Fallen Tree — Duplication Road", "lat": BASE_LAT + 0.015, "lng": BASE_LNG + 0.015, "radius": 50, "severity": "medium"},
    {"type": HazardType.ROAD_BLOCKED, "title": "Flooded Underpass — Galle Road", "lat": BASE_LAT - 0.018, "lng": BASE_LNG + 0.028, "radius": 150, "severity": "high"},
    {"type": HazardType.CHEMICAL_SPILL, "title": "Hazmat Zone — Colombo Port", "lat": BASE_LAT - 0.01, "lng": BASE_LNG - 0.02, "radius": 300, "severity": "high"},
    {"type": HazardType.STRUCTURAL_COLLAPSE, "title": "Bridge Damage — Kelani Bridge", "lat": BASE_LAT - 0.005, "lng": BASE_LNG + 0.035, "radius": 200, "severity": "high"},
    {"type": HazardType.POWER_OUTAGE, "title": "Power Outage — Colombo North", "lat": BASE_LAT + 0.02, "lng": BASE_LNG + 0.04, "radius": 1000, "severity": "medium"},
]


async def seed():
    """Seed the database with demo data."""
    async with async_session_factory() as db:
        # Seed users
        print("Seeding users...")
        users = {}
        for u in DEMO_USERS:
            user = User(
                email=u["email"], username=u["username"],
                hashed_password=hash_password(u["password"]),
                full_name=u["full_name"], role=u["role"], organization=u["organization"],
            )
            db.add(user)
            await db.flush()
            users[u["username"]] = user

        # Seed incidents
        print("Seeding incidents...")
        reporter = users["citizen"]
        for inc_data in DEMO_INCIDENTS:
            incident = Incident(
                title=inc_data["title"], description=inc_data["description"],
                incident_type=inc_data["type"], severity=inc_data["severity"],
                status=IncidentStatus.REPORTED,
                latitude=inc_data["lat"], longitude=inc_data["lng"],
                people_at_risk=inc_data["people"],
                vulnerable_people=inc_data["vulnerable"],
                medical_need=inc_data["medical"],
                reporter_id=reporter.id, reporter_name=reporter.full_name,
            )
            db.add(incident)

        # Seed resources
        print("Seeding resources...")
        for r in DEMO_RESOURCES:
            resource = Resource(
                name=r["name"], resource_type=r["type"],
                status=ResourceStatus.AVAILABLE,
                latitude=r["lat"], longitude=r["lng"],
                capacity=r.get("capacity"), capabilities=r.get("caps"),
                organization="ResQGrid Sri Lanka Emergency Services",
            )
            db.add(resource)

        # Seed hazards
        print("Seeding hazards...")
        for h in DEMO_HAZARDS:
            hazard = Hazard(
                hazard_type=h["type"], title=h["title"],
                latitude=h["lat"], longitude=h["lng"],
                radius_meters=h["radius"], severity=h["severity"],
                status=HazardStatus.ACTIVE,
                reported_by=users["dispatcher"].id,
            )
            db.add(hazard)

        await db.commit()
        print(f"Seed complete! Users: {len(DEMO_USERS)}, Incidents: {len(DEMO_INCIDENTS)}, Resources: {len(DEMO_RESOURCES)}, Hazards: {len(DEMO_HAZARDS)}")
        print("\nDemo credentials:")
        print("  Admin:      admin@resqgrid.local / admin123")
        print("  Dispatcher: dispatcher@resqgrid.local / dispatch123")
        print("  Responder:  responder1@resqgrid.local / respond123")
        print("  Citizen:    citizen@resqgrid.local / citizen123")


if __name__ == "__main__":
    asyncio.run(seed())
