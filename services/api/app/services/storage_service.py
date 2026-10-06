"""Storage Service — upload files to Alibaba Cloud OSS or local storage."""

import os
import uuid
from datetime import datetime

from fastapi import UploadFile

from app.core.config import settings


async def upload_file_to_storage(file: UploadFile) -> str:
    """
    Upload a file to object storage and return the URL.
    Uses Alibaba Cloud OSS in production, local filesystem in development.
    """
    file_ext = os.path.splitext(file.filename or "file")[1]
    storage_key = f"evidence/{datetime.utcnow().strftime('%Y/%m/%d')}/{uuid.uuid4()}{file_ext}"

    if settings.APP_ENV == "production" and settings.OSS_ACCESS_KEY_ID:
        return await _upload_to_oss(file, storage_key)
    else:
        return await _upload_to_local(file, storage_key)


async def _upload_to_oss(file: UploadFile, storage_key: str) -> str:
    """Upload to Alibaba Cloud OSS."""
    import oss2

    auth = oss2.Auth(settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET)
    bucket = oss2.Bucket(auth, settings.OSS_ENDPOINT, settings.OSS_BUCKET)

    content = await file.read()
    bucket.put_object(storage_key, content)

    return f"https://{settings.OSS_BUCKET}.{settings.OSS_ENDPOINT.replace('https://', '')}/{storage_key}"


async def _upload_to_local(file: UploadFile, storage_key: str) -> str:
    """Upload to local filesystem (development only)."""
    upload_dir = os.path.join("uploads", os.path.dirname(storage_key))
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join("uploads", storage_key)
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    return f"/uploads/{storage_key}"
