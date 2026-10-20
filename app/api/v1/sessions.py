import asyncio
import os
import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Response, status
from pydantic import BaseModel, Field
from app.api.errors import AppException, ErrorCodes
from app.config import settings
from app.engine.otio_export import OTIOExporter
from app.engine.renderer import VideoRenderer
from app.engine.timeline_engine import TimelineEngine
from app.logging_config import logger
from app.models.manifest import OutputManifest
from app.models.session import SessionState, StepResult
from app.models.timeline import Timeline
from app.services.job_service import job_service
from app.services.media_service import MediaService
from app.services.session_service import SessionService
from app.services.storage_service import storage_service

router = APIRouter(prefix="/sessions", tags=["Sessions"])

# Shared session service instance
session_service = SessionService()


class CreateSessionRequest(BaseModel):
    video_uri: str


class StepRequest(BaseModel):
    say: str
    answer: Optional[str] = None
    callback_url: Optional[str] = None


class JobAcceptedResponse(BaseModel):
    job_id: str
    status: str = "queued"
    message: str = "Operation accepted for background processing"
    poll_url: str


@router.post("", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_session(
    payload: CreateSessionRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
):
    """Creates a new editing session for the given video file or URL."""
    video_path = payload.video_uri

    # Ingest from URL if needed
    if video_path.startswith(("http://", "https://")):
        video_path = await MediaService.ingest_from_url(video_path)

    if not os.path.exists(video_path):
        raise AppException(
            code=ErrorCodes.MEDIA_NOT_FOUND,
            message=f"Video file '{video_path}' not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    source_media = MediaService.inspect_and_register(video_path)
    state = session_service.create_session(video_path, source_media)

    return {
        "session_id": state.session_id,
        "video_uri": state.video_uri,
        "timeline_hash": state.timeline.timeline_hash,
        "duration_s": state.timeline.duration_ms / 1000.0,
        "timeline": state.timeline.model_dump(),
    }


@router.get("/{session_id}")
async def get_session(session_id: str):
    """Retrieves session details and current timeline."""
    try:
        state = session_service.get_session(session_id)
        return {
            "session_id": state.session_id,
            "video_uri": state.video_uri,
            "timeline_hash": state.timeline.timeline_hash,
            "duration_s": state.timeline.duration_ms / 1000.0,
            "timeline": state.timeline.model_dump(),
            "history_count": len(state.history),
            "step_count": len(state.step_results),
        }
    except KeyError:
        raise AppException(
            code=ErrorCodes.SESSION_NOT_FOUND,
            message=f"Session '{session_id}' not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )


async def execute_render_job(job_id: str, session_id: str, timeline: Timeline):
    """Background task executing video rendering."""
    try:
        job_service.update_progress(job_id, 10, status="running")
        # In a real heavy render, progress increases
        job_service.update_progress(job_id, 35, status="running")
        output_path, meta = VideoRenderer.render(timeline)
        job_service.update_progress(job_id, 90, status="running")

        # Create output manifest & upload to S3/MinIO if enabled
        filename = os.path.basename(output_path)
        download_url = storage_service.upload_output(output_path)
        manifest = OutputManifest(
            timeline_id=timeline.timeline_id,
            timeline_hash=timeline.timeline_hash,
            output_video_path=output_path,
            output_video_url=download_url,
            output_duration_s=meta["actual_duration_s"],
            models_used={"stt": settings.STT_PROVIDER},
            providers={"stt": settings.STT_PROVIDER},
            timings={"render_time_s": 1.2},
            warnings=[],
        )

        job_service.complete_job(
            job_id,
            {
                "output_video_path": output_path,
                "download_url": download_url,
                "metadata": meta,
                "manifest": manifest.model_dump(),
            },
        )
    except Exception as e:
        logger.exception("Render job %s failed: %s", job_id, str(e))
        job_service.fail_job(
            job_id,
            {
                "code": ErrorCodes.RENDER_FAILED,
                "message": str(e),
                "retryable": True,
            },
        )


@router.post("/{session_id}/steps")
async def execute_step(
    session_id: str,
    payload: StepRequest,
    response: Response,
    background_tasks: BackgroundTasks,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
):
    """
    Applies an editing instruction to the session.
    If instruction is 'render', dispatches a background job and returns HTTP 202.
    Otherwise executes synchronously in < 2 seconds and returns StepResult.
    """
    try:
        state = session_service.get_session(session_id)
    except KeyError:
        raise AppException(
            code=ErrorCodes.SESSION_NOT_FOUND,
            message=f"Session '{session_id}' not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    # Check for render instruction -> Background Job (Integration Standard 3)
    if payload.say.strip().lower() in ("render", "export", "render video", "render the video"):
        job = job_service.create_job(
            idempotency_key=idempotency_key,
            callback_url=payload.callback_url,
        )
        if job.status == "queued":
            background_tasks.add_task(execute_render_job, job.job_id, session_id, state.timeline)

        response.status_code = status.HTTP_202_ACCEPTED
        return JobAcceptedResponse(
            job_id=job.job_id,
            status=job.status,
            poll_url=f"/api/v1/jobs/{job.job_id}",
        )

    # Standard editing instruction -> Fast execution
    result = session_service.process_step(
        session_id=session_id,
        say=payload.say,
        answer=payload.answer,
    )
    return result


@router.post("/{session_id}/render", status_code=status.HTTP_202_ACCEPTED, response_model=JobAcceptedResponse)
async def trigger_render(
    session_id: str,
    background_tasks: BackgroundTasks,
    callback_url: Optional[str] = None,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
):
    """Triggers rendering of the session timeline as a background job."""
    try:
        state = session_service.get_session(session_id)
    except KeyError:
        raise AppException(
            code=ErrorCodes.SESSION_NOT_FOUND,
            message=f"Session '{session_id}' not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    job = job_service.create_job(idempotency_key=idempotency_key, callback_url=callback_url)
    if job.status == "queued":
        background_tasks.add_task(execute_render_job, job.job_id, session_id, state.timeline)

    return JobAcceptedResponse(
        job_id=job.job_id,
        status=job.status,
        poll_url=f"/api/v1/jobs/{job.job_id}",
    )


@router.get("/{session_id}/export-otio")
async def export_otio(session_id: str):
    """Exports session timeline to OpenTimelineIO (.otio) format."""
    try:
        state = session_service.get_session(session_id)
        out_path = OTIOExporter.export_timeline(state.timeline)
        download_url = storage_service.upload_output(out_path)
        return {
            "status": "success",
            "file_path": out_path,
            "filename": os.path.basename(out_path),
            "download_url": download_url,
        }
    except KeyError:
        raise AppException(
            code=ErrorCodes.SESSION_NOT_FOUND,
            message=f"Session '{session_id}' not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )
