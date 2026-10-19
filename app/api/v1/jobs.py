from fastapi import APIRouter, HTTPException, status
from app.api.errors import AppException, ErrorCodes
from app.models.job import Job
from app.services.job_service import job_service

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("/{job_id}", response_model=Job)
async def get_job_status(job_id: str):
    """Retrieves the status, progress (0-100), and results of a background job."""
    job = job_service.get_job(job_id)
    if not job:
        raise AppException(
            code=ErrorCodes.JOB_NOT_FOUND,
            message=f"Job '{job_id}' not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    return job
