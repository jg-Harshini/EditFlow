from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Base application exception following Integration Standard 5."""

    def __init__(
        self,
        code: str,
        message: str,
        retryable: bool = False,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
    ):
        self.code = code
        self.message = message
        self.retryable = retryable
        self.details = details or {}
        self.status_code = status_code
        super().__init__(message)


# Standardized UPPER_SNAKE_CASE Error Codes
class ErrorCodes:
    INVALID_REQUEST = "INVALID_REQUEST"
    MEDIA_NOT_FOUND = "MEDIA_NOT_FOUND"
    INVALID_MEDIA_FORMAT = "INVALID_MEDIA_FORMAT"
    SSRF_BLOCKED = "SSRF_BLOCKED"
    DOWNLOAD_FAILED = "DOWNLOAD_FAILED"
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"
    JOB_NOT_FOUND = "JOB_NOT_FOUND"
    OPERATION_REJECTED = "OPERATION_REJECTED"
    AMBIGUOUS_INSTRUCTION = "AMBIGUOUS_INSTRUCTION"
    RENDER_FAILED = "RENDER_FAILED"
    STT_FAILED = "STT_FAILED"
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Formats AppException into standardized JSON: {"error": {"code", "message", "retryable", "details"}}"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "retryable": exc.retryable,
                "details": exc.details,
            }
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": ErrorCodes.INTERNAL_SERVER_ERROR,
                "message": str(exc),
                "retryable": False,
                "details": {"type": type(exc).__name__},
            }
        },
    )
