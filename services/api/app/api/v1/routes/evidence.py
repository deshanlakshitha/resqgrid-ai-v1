"""Evidence upload routes."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.entities import Evidence
from app.schemas.schemas import IncidentResponse

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_evidence(
    incident_id: str,
    file: UploadFile = File(...),
    analyze: bool = Query(True, description="Run AI vision analysis on image evidence after upload"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload evidence (image/file) for an incident."""
    from app.services.storage_service import upload_file_to_storage
    from app.services.vision_service import run_vision_analysis_for_evidence

    # Upload to object storage
    file_url = await upload_file_to_storage(file)

    evidence = Evidence(
        incident_id=uuid.UUID(incident_id),
        uploaded_by=current_user.id,
        evidence_type="image" if file.content_type and file.content_type.startswith("image/") else "document",
        file_url=file_url,
        file_name=file.filename or "unknown",
        file_size_bytes=file.size or 0,
        mime_type=file.content_type or "application/octet-stream",
    )
    db.add(evidence)
    await db.flush()
    await db.refresh(evidence)

    ai_analysis = None
    if analyze and evidence.evidence_type.value == "image":
        try:
            evidence = await run_vision_analysis_for_evidence(db, str(evidence.id))
            ai_analysis = evidence.ai_analysis
        except Exception as e:
            # Do not fail the upload if analysis fails
            ai_analysis = {"error": str(e), "analyzed_at": None}

    return {
        "id": str(evidence.id),
        "file_url": evidence.file_url,
        "file_name": evidence.file_name,
        "evidence_type": evidence.evidence_type.value,
        "mime_type": evidence.mime_type,
        "ai_analysis": ai_analysis,
        "uploaded_at": evidence.created_at.isoformat(),
    }


@router.get("/incident/{incident_id}")
async def list_evidence_for_incident(
    incident_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all evidence for a specific incident."""
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
            "file_url": ev.file_url,
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

    evidence = await run_vision_analysis_for_evidence(db, str(evidence_id))
    return {
        "id": str(evidence.id),
        "file_url": evidence.file_url,
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
    result = await db.execute(select(Evidence).where(Evidence.id == evidence_id, Evidence.is_deleted == False))
    evidence = result.scalar_one_or_none()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return {
        "id": str(evidence.id),
        "incident_id": str(evidence.incident_id),
        "file_url": evidence.file_url,
        "file_name": evidence.file_name,
        "evidence_type": evidence.evidence_type.value,
        "mime_type": evidence.mime_type,
        "file_size_bytes": evidence.file_size_bytes,
        "description": evidence.description,
        "ai_analysis": evidence.ai_analysis,
        "created_at": evidence.created_at.isoformat(),
    }
