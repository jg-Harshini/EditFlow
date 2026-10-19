import asyncio
import hashlib
import hmac
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine, Dict, Optional
import httpx
from app.config import settings
from app.logging_config import logger
from app.models.job import Job


class JobService:
    """Manages background jobs, progress updates, idempotency, and HMAC-signed webhooks."""

    def __init__(self):
        self.jobs: Dict[str, Job] = {}
        self.idempotency_map: Dict[str, str] = {}  # idempotency_key -> job_id

    def create_job(
        self,
        idempotency_key: Optional[str] = None,
        callback_url: Optional[str] = None,
    ) -> Job:
        """Creates a new job or returns existing job if idempotency key matches."""
        if idempotency_key and idempotency_key in self.idempotency_map:
            existing_job_id = self.idempotency_map[idempotency_key]
            logger.info("Idempotent hit: returning existing job %s for key %s", existing_job_id, idempotency_key)
            return self.jobs[existing_job_id]

        job_id = str(uuid.uuid4())
        job = Job(
            job_id=job_id,
            status="queued",
            progress=0,
            callback_url=callback_url,
            idempotency_key=idempotency_key,
        )
        self.jobs[job_id] = job
        if idempotency_key:
            self.idempotency_map[idempotency_key] = job_id

        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        return self.jobs.get(job_id)

    def update_progress(self, job_id: str, progress: int, status: str = "running") -> None:
        job = self.jobs.get(job_id)
        if job:
            job.progress = max(0, min(100, progress))
            job.status = status
            job.updated_at = datetime.now(timezone.utc)

    def complete_job(self, job_id: str, result: Dict[str, Any]) -> None:
        job = self.jobs.get(job_id)
        if job:
            job.progress = 100
            job.status = "succeeded"
            job.result = result
            job.updated_at = datetime.now(timezone.utc)
            if job.callback_url:
                asyncio.create_task(self.dispatch_webhook(job))

    def fail_job(self, job_id: str, error: Dict[str, Any]) -> None:
        job = self.jobs.get(job_id)
        if job:
            job.status = "failed"
            job.error = error
            job.updated_at = datetime.now(timezone.utc)
            if job.callback_url:
                asyncio.create_task(self.dispatch_webhook(job))

    @staticmethod
    def generate_hmac_signature(payload_bytes: bytes, secret: str) -> str:
        """Generates HMAC-SHA256 hex digest for webhook verification."""
        return hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()

    async def dispatch_webhook(self, job: Job) -> None:
        """Dispatches signed webhook to callback URL."""
        if not job.callback_url:
            return

        payload = {
            "job_id": job.job_id,
            "status": job.status,
            "progress": job.progress,
            "result": job.result,
            "error": job.error,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        body_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
        signature = self.generate_hmac_signature(body_bytes, settings.WEBHOOK_HMAC_SECRET)

        headers = {
            "Content-Type": "application/json",
            "X-IncuBrix-Signature": signature,
        }

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(job.callback_url, content=body_bytes, headers=headers)
                logger.info("Webhook dispatched for job %s to %s (HTTP %d)", job.job_id, job.callback_url, resp.status_code)
        except Exception as e:
            logger.warning("Failed to dispatch webhook for job %s: %s", job.job_id, str(e))


job_service = JobService()
