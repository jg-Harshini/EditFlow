import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Dict

correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="")
job_id_ctx: ContextVar[str] = ContextVar("job_id", default="")


class StructuredJSONFormatter(logging.Formatter):
    """Formats log records as structured JSON including timestamp, level, correlation_id, and job_id."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }

        # Include request context variables
        corr_id = correlation_id_ctx.get()
        if corr_id:
            log_obj["correlation_id"] = corr_id

        jid = job_id_ctx.get()
        if jid or hasattr(record, "job_id"):
            log_obj["job_id"] = jid or getattr(record, "job_id", "")

        # Attach extra properties if available
        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            log_obj.update(record.extra_data)

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj)


def setup_logging(log_level: str = "INFO") -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Clear existing handlers
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredJSONFormatter())
    root_logger.addHandler(handler)


logger = logging.getLogger("incubrix")
