from fastapi import APIRouter
from app.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
async def get_health():
    """Liveness probe returning HTTP 200."""
    return {"status": "ok", "app": settings.APP_NAME}


@router.get("/ready")
async def get_ready():
    """Readiness probe checking disk storage and environment readiness."""
    storage_ready = settings.STORAGE_DIR.exists() and settings.OUTPUT_DIR.exists()
    return {
        "status": "ready" if storage_ready else "not_ready",
        "storage": storage_ready,
        "stt_provider": settings.STT_PROVIDER,
    }
