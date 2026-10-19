from fastapi import APIRouter
from app.api.v1.jobs import router as jobs_router
from app.api.v1.media import router as media_router
from app.api.v1.sessions import router as sessions_router

api_router = APIRouter()
api_router.include_router(sessions_router)
api_router.include_router(jobs_router)
api_router.include_router(media_router)
