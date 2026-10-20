import os
import shutil
import uuid
from pathlib import Path
from typing import Dict, Optional
from fastapi import APIRouter, File, Header, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl
from app.api.errors import AppException, ErrorCodes
from app.config import settings
from app.services.media_service import MediaService, MediaValidationError

router = APIRouter(prefix="/media", tags=["Media"])

# Idempotency cache for media ingest operations (Integration Standard 4)
_media_idempotency_cache: Dict[str, "MediaIngestResponse"] = {}


class IngestUrlRequest(BaseModel):
    url: str


class MediaIngestResponse(BaseModel):
    file_path: str
    download_url: str
    sha256: str
    duration_s: float
    fps: float
    width: int
    height: int


@router.post("/upload", response_model=MediaIngestResponse)
async def upload_media_file(
    file: UploadFile = File(...),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
):
    """Uploads a video file (MP4 or MOV) for editing."""
    if idempotency_key and idempotency_key in _media_idempotency_cache:
        return _media_idempotency_cache[idempotency_key]

    filename = file.filename or f"upload_{uuid.uuid4().hex[:8]}.mp4"
    ext = Path(filename).suffix.lower()
    if ext not in (".mp4", ".mov", ".m4v"):
        raise AppException(
            code=ErrorCodes.INVALID_MEDIA_FORMAT,
            message=f"Unsupported media format '{ext}'. Only MP4 and MOV are allowed.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    target_path = settings.STORAGE_DIR / f"{uuid.uuid4().hex[:8]}_{filename}"
    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        source_media = MediaService.inspect_and_register(str(target_path))
    except MediaValidationError as e:
        if target_path.exists():
            target_path.unlink(missing_ok=True)
        raise AppException(
            code=ErrorCodes.INVALID_MEDIA_FORMAT,
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    res = MediaIngestResponse(
        file_path=str(target_path),
        download_url=f"/api/v1/media/{target_path.name}",
        sha256=source_media.sha256,
        duration_s=source_media.duration_s,
        fps=source_media.fps,
        width=source_media.width,
        height=source_media.height,
    )
    if idempotency_key:
        _media_idempotency_cache[idempotency_key] = res
    return res


@router.post("/ingest-url", response_model=MediaIngestResponse)
async def ingest_media_from_url(
    payload: IngestUrlRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
):
    """Safely downloads a media file from a URL with SSRF protection."""
    if idempotency_key and idempotency_key in _media_idempotency_cache:
        return _media_idempotency_cache[idempotency_key]

    try:
        local_path = await MediaService.ingest_from_url(payload.url)
        source_media = MediaService.inspect_and_register(local_path)
    except MediaValidationError as e:
        raise AppException(
            code=ErrorCodes.SSRF_BLOCKED if "SSRF" in str(e) else ErrorCodes.DOWNLOAD_FAILED,
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    p = Path(local_path)
    res = MediaIngestResponse(
        file_path=local_path,
        download_url=f"/api/v1/media/{p.name}",
        sha256=source_media.sha256,
        duration_s=source_media.duration_s,
        fps=source_media.fps,
        width=source_media.width,
        height=source_media.height,
    )
    if idempotency_key:
        _media_idempotency_cache[idempotency_key] = res
    return res


@router.get("/{file_name}")
async def download_media(file_name: str):
    """Serves ingested and rendered media files for download."""
    search_dirs = [
        settings.STORAGE_DIR,
        settings.OUTPUT_DIR,
        Path("test_pack/assets"),  # allow streaming sample assets during demo
    ]
    target = None
    for d in search_dirs:
        candidate = d / file_name
        if candidate.exists():
            target = candidate
            break

    if not target:
        raise AppException(
            code=ErrorCodes.MEDIA_NOT_FOUND,
            message=f"Media file '{file_name}' not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    media_type = "video/mp4"
    if file_name.endswith(".mp3"):
        media_type = "audio/mpeg"
    elif file_name.endswith(".mov"):
        media_type = "video/quicktime"

    return FileResponse(path=str(target), media_type=media_type, filename=file_name)
