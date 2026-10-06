"""API v1 router — aggregates all endpoint modules."""

from fastapi import APIRouter

from app.api.v1.routes import auth, incidents, resources, recommendations, assignments, dashboard, hazards, audit, assistant, evidence

api_v1_router = APIRouter()

api_v1_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(incidents.router, prefix="/incidents", tags=["Incidents"])
api_v1_router.include_router(resources.router, prefix="/resources", tags=["Resources"])
api_v1_router.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations"])
api_v1_router.include_router(assignments.router, prefix="/assignments", tags=["Assignments"])
api_v1_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_v1_router.include_router(hazards.router, prefix="/hazards", tags=["Hazards"])
api_v1_router.include_router(audit.router, prefix="/audit", tags=["Audit"])
api_v1_router.include_router(assistant.router, prefix="/assistant", tags=["AI Assistant"])
api_v1_router.include_router(evidence.router, prefix="/evidence", tags=["Evidence"])
