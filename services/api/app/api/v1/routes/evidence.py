"""Evidence upload routes."""

import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_incident_access
from app.core.config import settings
from app.core.rate_limit import enforce_rate_limit
from app.models.user import User
from app.models.entities import Evidence
from app.models.incident import Incident

router = APIRouter()
logger = structlog.get_logger()


async def authorized_evidence(db, evidence_id, user, *, write=False):
    evidence = (await db.execute(select(Evidence).where(
        Evidence.id == evidence_id, Evidence.is_deleted == False,
    ))).scalar_one_or_none()
    if evidence is None:
        raise HTTPException(404, "Evidence not found")
    await require_incident_access(db, evidence.incident_id, user, write=write)
    return evidence


def content_url(evidence):
    return f"/api/v1/evidence/{evidence.id}/content"


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_evidence(
    incident_id: uuid.UUID,
    file: UploadFile = File(...),
    analyze: bool = Query(True, description="Run AI vision analysis on image evidence after upload"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload evidence (image/file) for an incident."""
    from app.services.storage_service import upload_file_to_storage, discard_stored_file
    from app.services.vision_service import run_vision_analysis_for_evidence

    await require_incident_access(db, incident_id, current_user, write=True)
    await enforce_rate_limit("evidence-upload", str(current_user.id), 30, 3600)
    # Serialize quota checks across concurrent uploads by the same user or to the same incident.
    await db.execute(select(User.id).where(User.id == current_user.id).with_for_update())
    await db.execute(select(Incident.id).where(Incident.id == incident_id).with_for_update())
    used = (await db.execute(select(func.coalesce(func.sum(Evidence.file_size_bytes), 0)).where(
        Evidence.uploaded_by == current_user.id,
    ))).scalar_one()
    count = (await db.execute(select(func.count(Evidence.id)).where(
        Evidence.incident_id == incident_id,
    ))).scalar_one()
    if used >= settings.EVIDENCE_USER_QUOTA_BYTES or count >= settings.EVIDENCE_INCIDENT_LIMIT:
        raise HTTPException(413, "Evidence storage quota reached")

    # Upload to object storage
    file_url = await upload_file_to_storage(file, remaining_bytes=settings.EVIDENCE_USER_QUOTA_BYTES - used)

    evidence = Evidence(
        incident_id=incident_id,
        uploaded_by=current_user.id,
        evidence_type="image" if file.content_type and file.content_type.startswith("image/") else "document",
        file_url=file_url,
        file_name=file.filename or "unknown",
        file_size_bytes=file.size or 0,
        mime_type=file.content_type or "application/octet-stream",
    )
    try:
        db.add(evidence)
        await db.flush()
        await db.refresh(evidence)
        await db.commit()
    except Exception:
        await db.rollback()
        try:
            await discard_stored_file(file_url)
        except Exception:
            logger.error("Could not clean up failed evidence upload")
        raise

    result = {
        "id": str(evidence.id),
        "file_url": content_url(evidence),
        "file_name": evidence.file_name,
        "evidence_type": evidence.evidence_type.value,
        "mime_type": evidence.mime_type,
        "ai_analysis": None,
        "uploaded_at": evidence.created_at.isoformat(),
    }
    if analyze and evidence.evidence_type.value == "image":
        try:
            await enforce_rate_limit("evidence-analysis", str(current_user.id), 30, 3600)
            evidence = await run_vision_analysis_for_evidence(db, result["id"])
            result["ai_analysis"] = evidence.ai_analysis
            await db.commit()
        except Exception:
            # Do not fail the upload if analysis fails
            await db.rollback()
            logger.warning("Evidence analysis unavailable", evidence_id=result["id"])
            result["ai_analysis"] = {"error": "Image analysis is temporarily unavailable", "analyzed_at": None}
    return result


@router.get("/incident/{incident_id}")
async def list_evidence_for_incident(
    incident_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all evidence for a specific incident."""
    await require_incident_access(db, incident_id, current_user)
    result = await db.execute(
        select(Evidence).where(
            Evidence.incident_id == incident_id,
            Evidence.is_deleted == False,
        ).order_by(Evidence.created_at.desc())
    )
    evidence_items = result.scalars().all()
    return [
        {
            "id": str(ev.id),
            "incident_id": str(ev.incident_id),
            "file_url": content_url(ev),
            "file_name": ev.file_name,
            "evidence_type": ev.evidence_type.value,
            "mime_type": ev.mime_type,
            "file_size_bytes": ev.file_size_bytes,
            "description": ev.description,
            "ai_analysis": ev.ai_analysis,
            "uploaded_by": str(ev.uploaded_by),
            "created_at": ev.created_at.isoformat(),
        }
        for ev in evidence_items
    ]


@router.post("/{evidence_id}/analyze", status_code=status.HTTP_200_OK)
async def analyze_evidence(
    evidence_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Re-run AI vision analysis on existing image evidence."""
    from app.services.vision_service import run_vision_analysis_for_evidence

    evidence = await authorized_evidence(db, evidence_id, current_user, write=True)
    if evidence.evidence_type.value != "image":
        raise HTTPException(415, "Only image evidence can be analyzed")
    await enforce_rate_limit("evidence-analysis", str(current_user.id), 30, 3600)
    try:
        evidence = await run_vision_analysis_for_evidence(db, str(evidence_id))
    except Exception:
        logger.warning("Evidence analysis unavailable", evidence_id=str(evidence_id))
        raise HTTPException(502, "Image analysis is temporarily unavailable") from None
    return {
        "id": str(evidence.id),
        "file_url": content_url(evidence),
        "file_name": evidence.file_name,
        "evidence_type": evidence.evidence_type.value,
        "mime_type": evidence.mime_type,
        "ai_analysis": evidence.ai_analysis,
        "created_at": evidence.created_at.isoformat(),
    }


@router.get("/{evidence_id}")
async def get_evidence(
    evidence_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get evidence details by ID."""
    evidence = await authorized_evidence(db, evidence_id, current_user)
    return {
        "id": str(evidence.id),
        "incident_id": str(evidence.incident_id),
        "file_url": content_url(evidence),
        "file_name": evidence.file_name,
        "evidence_type": evidence.evidence_type.value,
        "mime_type": evidence.mime_type,
        "file_size_bytes": evidence.file_size_bytes,
        "description": evidence.description,
        "ai_analysis": evidence.ai_analysis,
        "created_at": evidence.created_at.isoformat(),
    }


@router.get("/{evidence_id}/content")
async def download_evidence(
    evidence_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.services.storage_service import read_evidence_bytes
    evidence = await authorized_evidence(db, evidence_id, current_user)
    content = await read_evidence_bytes(evidence.file_url)
    safe_types = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    mime = evidence.mime_type if evidence.mime_type in safe_types else "application/octet-stream"
    return Response(content=content, media_type=mime, headers={
        "Cache-Control": "private, no-store",
        "Content-Disposition": "attachment",
        "X-Content-Type-Options": "nosniff",
        "Content-Security-Policy": "default-src 'none'; sandbox; frame-ancestors 'none'",
    })
