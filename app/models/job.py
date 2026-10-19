from datetime import datetime, timezone
from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field


class Job(BaseModel):
    job_id: str
    status: Literal["queued", "running", "succeeded", "failed"] = "queued"
    progress: int = Field(ge=0, le=100, default=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    callback_url: Optional[str] = None
    idempotency_key: Optional[str] = None
