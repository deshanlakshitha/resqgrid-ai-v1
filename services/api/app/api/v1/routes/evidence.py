"""Evidence upload routes."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload evidence (image/file) for an incident."""
    from app.services.storage_service import upload_file_to_storage

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

    return {
        "id": str(evidence.id),
        "file_url": evidence.file_url,
        "file_name": evidence.file_name,
        "evidence_type": evidence.evidence_type,
        "uploaded_at": evidence.created_at.isoformat(),
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
        "evidence_type": evidence.evidence_type,
        "mime_type": evidence.mime_type,
        "file_size_bytes": evidence.file_size_bytes,
        "description": evidence.description,
        "ai_analysis": evidence.ai_analysis,
        "created_at": evidence.created_at.isoformat(),
    }
