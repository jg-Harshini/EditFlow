import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import yaml
from app.api.errors import AppException, app_exception_handler, generic_exception_handler
from app.api.middleware import CorrelationIdMiddleware
from app.api.v1.health import router as health_router
from app.api.v1.router import api_router
from app.config import settings
from app.logging_config import logger, setup_logging


def export_openapi_yaml(app: FastAPI, path: str = "openapi.yaml") -> None:
    """Generates and writes OpenAPI 3.1 schema to openapi.yaml."""
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        openapi_version="3.1.0",
        description=app.description,
        routes=app.routes,
    )
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(openapi_schema, f, sort_keys=False, default_flow_style=False)
    logger.info("Exported OpenAPI 3.1 documentation to %s", path)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging(settings.LOG_LEVEL)
    logger.info("Starting %s on %s:%d", settings.APP_NAME, settings.HOST, settings.PORT)
    try:
        export_openapi_yaml(app, "openapi.yaml")
    except Exception as e:
        logger.warning("Could not write openapi.yaml during startup: %s", str(e))
    yield
    # Shutdown
    logger.info("Shutting down %s", settings.APP_NAME)


app = FastAPI(
    title="EditFlow Prompt-Based Video Editing Engine API",
    version="1.0.0",
    description="High-performance, content-anchored prompt-based conversational video editing service.",
    lifespan=lifespan,
)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        openapi_version="3.1.0",
        description=app.description,
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

# CORS middleware for demo/frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom correlation ID tracing middleware
app.add_middleware(CorrelationIdMiddleware)

# Exception Handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Top-level Health Endpoints
app.include_router(health_router)

# Mount frontend production assets if built
frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if (frontend_dist / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="frontend_assets")

# Interactive Web UI on root /
@app.get("/", include_in_schema=False)
async def serve_ui():
    if (frontend_dist / "index.html").exists():
        return FileResponse(str(frontend_dist / "index.html"))
    ui_path = Path(__file__).parent / "static" / "index.html"
    return FileResponse(str(ui_path))

# Versioned API routes under /api/v1/
app.include_router(api_router, prefix=settings.API_V1_STR)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
