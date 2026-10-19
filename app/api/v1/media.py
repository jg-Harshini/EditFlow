import os
import shutil
import uuid
from pathlib import Path
from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl
from app.api.errors import AppException, ErrorCodes
from app.config import settings
from app.services.media_service import MediaService, MediaValidationError

router = APIRouter(prefix="/media", tags=["Media"])


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
async def upload_media_file(file: UploadFile = File(...)):
    """Uploads a video file (MP4 or MOV) for editing."""
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

    return MediaIngestResponse(
        file_path=str(target_path),
        download_url=f"/api/v1/media/{target_path.name}",
        sha256=source_media.sha256,
        duration_s=source_media.duration_s,
        fps=source_media.fps,
        width=source_media.width,
        height=source_media.height,
    )


@router.post("/ingest-url", response_model=MediaIngestResponse)
async def ingest_media_from_url(payload: IngestUrlRequest):
    """Safely downloads a media file from a URL with SSRF protection."""
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
    return MediaIngestResponse(
        file_path=local_path,
        download_url=f"/api/v1/media/{p.name}",
        sha256=source_media.sha256,
        duration_s=source_media.duration_s,
        fps=source_media.fps,
        width=source_media.width,
        height=source_media.height,
    )


@router.get("/{file_name}")
async def download_media(file_name: str):
    """Serves ingested and rendered media files for download."""
    storage_file = settings.STORAGE_DIR / file_name
    output_file = settings.OUTPUT_DIR / file_name

    target = None
    if storage_file.exists():
        target = storage_file
    elif output_file.exists():
        target = output_file

    if not target or not target.exists():
        raise AppException(
            code=ErrorCodes.MEDIA_NOT_FOUND,
            message=f"Media file '{file_name}' not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return FileResponse(path=str(target), media_type="video/mp4", filename=file_name)
