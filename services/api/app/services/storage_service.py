"""Storage Service — upload files to Alibaba Cloud OSS or local storage."""

import io
import uuid
import warnings
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from fastapi import HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
from starlette.concurrency import run_in_threadpool

from app.core.config import settings


async def upload_file_to_storage(file: UploadFile, *, remaining_bytes: int | None = None) -> str:
    """
    Upload a file to object storage and return the URL.
    Uses Alibaba Cloud OSS in production, local filesystem in development.
    """
    content = bytearray()
    while chunk := await file.read(64 * 1024):
        content.extend(chunk)
        if len(content) > settings.MAX_UPLOAD_BYTES:
            raise HTTPException(413, "Evidence exceeds the upload size limit")
    clean, file_ext, mime = await run_in_threadpool(_sanitize_image, bytes(content))
    if remaining_bytes is not None and len(clean) > remaining_bytes:
        raise HTTPException(413, "Evidence storage quota reached")
    # Replace the spooled upload with verified, re-encoded image bytes, stripping metadata and active content.
    await file.seek(0)
    await run_in_threadpool(file.file.truncate, 0)
    file.size = 0
    await file.write(clean)
    await file.seek(0)
    file.filename = f"{Path(file.filename or 'evidence').stem[:120]}{file_ext}"
    file.headers = type(file.headers)({"content-type": mime})
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

    await file.seek(0)
    await run_in_threadpool(bucket.put_object, storage_key, file.file, headers={
        "x-oss-object-acl": "private", "Content-Type": file.content_type,
        "Content-Disposition": "attachment",
    })

    return f"https://{settings.OSS_BUCKET}.{settings.OSS_ENDPOINT.replace('https://', '')}/{storage_key}"


async def _upload_to_local(file: UploadFile, storage_key: str) -> str:
    """Upload to local filesystem (development only)."""
    file_path = local_storage_path(f"/uploads/{storage_key}")
    await run_in_threadpool(file_path.parent.mkdir, parents=True, exist_ok=True)
    await file.seek(0)
    await run_in_threadpool(_copy_upload, file.file, file_path)
    return f"/uploads/{storage_key}"


def _sanitize_image(content: bytes) -> tuple[bytes, str, str]:
    if not content:
        raise HTTPException(400, "Empty evidence file")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(content)) as image:
                if image.format not in {"JPEG", "PNG", "WEBP", "GIF"}:
                    raise HTTPException(415, "Use a JPEG, PNG, WebP, or GIF image")
                if image.width * image.height > settings.MAX_IMAGE_PIXELS:
                    raise HTTPException(413, "Image dimensions exceed the limit")
                image.load()
                output = io.BytesIO()
                # Use a fresh image so EXIF, comments, and appended payloads are not preserved.
                mode = "RGBA" if "A" in image.getbands() or "transparency" in image.info else "RGB"
                converted = image.convert(mode)
                clean = Image.new(mode, image.size)
                clean.paste(converted)
                clean.save(output, format="PNG")
                result = output.getvalue()
                if len(result) > settings.MAX_UPLOAD_BYTES:
                    raise HTTPException(413, "Decoded image exceeds the upload size limit")
                return result, ".png", "image/png"
    except (Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise HTTPException(413, "Image dimensions exceed the limit") from None
    except (UnidentifiedImageError, OSError, ValueError):
        raise HTTPException(415, "Use a valid JPEG, PNG, WebP, or GIF image") from None


def local_storage_path(file_url: str) -> Path:
    if not file_url.startswith("/uploads/"):
        raise HTTPException(404, "Evidence file not found")
    root = settings.UPLOAD_DIR.resolve()
    path = (root / file_url.removeprefix("/uploads/")).resolve()
    if not path.is_relative_to(root) or path == root:
        raise HTTPException(404, "Evidence file not found")
    return path


def _copy_upload(source, path: Path) -> None:
    import shutil
    with path.open("xb") as destination:
        try:
            shutil.copyfileobj(source, destination, length=64 * 1024)
        except OSError:
            destination.close()
            path.unlink(missing_ok=True)
            raise


def _oss_bucket_and_key(file_url: str):
    import oss2
    parsed = urlparse(file_url)
    expected_host = f"{settings.OSS_BUCKET}.{urlparse(settings.OSS_ENDPOINT).netloc}"
    if parsed.scheme != "https" or parsed.netloc != expected_host or not parsed.path.startswith("/evidence/"):
        raise HTTPException(404, "Evidence file not found")
    auth = oss2.Auth(settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET)
    return oss2.Bucket(auth, settings.OSS_ENDPOINT, settings.OSS_BUCKET), parsed.path.lstrip("/")


async def read_evidence_bytes(file_url: str) -> bytes:
    def read():
        if file_url.startswith("/uploads/"):
            path = local_storage_path(file_url)
            if not path.is_file():
                raise HTTPException(404, "Evidence file not found")
            with path.open("rb") as source:
                return source.read(settings.MAX_UPLOAD_BYTES + 1)
        bucket, key = _oss_bucket_and_key(file_url)
        source = bucket.get_object(key)
        try:
            return source.read(settings.MAX_UPLOAD_BYTES + 1)
        finally:
            source.close()
    content = await run_in_threadpool(read)
    if len(content) > settings.MAX_UPLOAD_BYTES:
        raise HTTPException(413, "Evidence exceeds the download size limit")
    return content


async def discard_stored_file(file_url: str) -> None:
    """Compensate for database failures after storing a new upload."""
    if file_url.startswith("/uploads/"):
        await run_in_threadpool(local_storage_path(file_url).unlink, missing_ok=True)
    else:
        bucket, key = _oss_bucket_and_key(file_url)
        await run_in_threadpool(bucket.delete_object, key)
