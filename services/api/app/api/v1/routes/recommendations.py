"""Recommendation routes: approve/reject resource recommendations."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_role
from app.models.user import User, UserRole
from app.models.entities import Recommendation, RecommendationStatus, AuditAction
from app.schemas.schemas import RecommendationResponse, ApprovalRequest
from app.services.audit_service import log_action

router = APIRouter()


@router.get("", response_model=list[RecommendationResponse])
async def list_recommendations(
    status_filter: str | None = None,
    incident_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.DISPATCHER, UserRole.ADMIN)),
):
    """List all recommendations with optional filters."""
    query = select(Recommendation).where(Recommendation.is_deleted == False)
    if status_filter:
        query = query.where(Recommendation.status == status_filter)
    if incident_id:
        query = query.where(Recommendation.incident_id == incident_id)

    result = await db.execute(query.order_by(Recommendation.created_at.desc()))
    return result.scalars().all()


@router.post("/{recommendation_id}/approve", response_model=RecommendationResponse)
async def approve_recommendation(
    recommendation_id: uuid.UUID,
    data: ApprovalRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.DISPATCHER, UserRole.ADMIN)),
):
    """Approve a resource recommendation (human approval required)."""
    result = await db.execute(
        select(Recommendation).where(Recommendation.id == recommendation_id, Recommendation.is_deleted == False)
    )
    rec = result.scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    if rec.status != RecommendationStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Recommendation is already {rec.status}")

    if not data.approved:
        raise HTTPException(status_code=400, detail="Use /reject endpoint to reject")

    rec.status = RecommendationStatus.APPROVED
    rec.approved_by = current_user.id
    rec.approved_at = datetime.now(timezone.utc)

    await log_action(
        db,
        action=AuditAction.APPROVE,
        entity_type="recommendation",
        entity_id=rec.id,
        user_id=current_user.id,
        details={
            "incident_id": str(rec.incident_id),
            "resource_id": str(rec.resource_id),
            "confidence": rec.confidence,
        },
    )
    await db.flush()
    await db.refresh(rec)
    return rec


@router.post("/{recommendation_id}/reject", response_model=RecommendationResponse)
async def reject_recommendation(
    recommendation_id: uuid.UUID,
    data: ApprovalRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.DISPATCHER, UserRole.ADMIN)),
):
    """Reject a resource recommendation."""
    result = await db.execute(
        select(Recommendation).where(Recommendation.id == recommendation_id, Recommendation.is_deleted == False)
    )
    rec = result.scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    if rec.status != RecommendationStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Recommendation is already {rec.status}")

    rec.status = RecommendationStatus.REJECTED
    rec.approved_by = current_user.id
    rec.approved_at = datetime.now(timezone.utc)
    rec.rejection_reason = data.reason

    await log_action(
        db,
        action=AuditAction.REJECT,
        entity_type="recommendation",
        entity_id=rec.id,
        user_id=current_user.id,
        details={
            "incident_id": str(rec.incident_id),
            "resource_id": str(rec.resource_id),
            "reason": data.reason,
        },
    )
    await db.flush()
    await db.refresh(rec)
    return rec
