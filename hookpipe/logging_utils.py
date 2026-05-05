"""Structured logging utilities for hookpipe pipeline events."""

import json
import logging
import time
from typing import Any, Dict, Optional

logger = logging.getLogger("hookpipe")


def _utc_timestamp() -> str:
    """Return current UTC time as ISO-8601 string."""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def build_log_record(
    event: str,
    payload: Optional[Dict[str, Any]] = None,
    destination: Optional[str] = None,
    status: Optional[str] = None,
    error: Optional[str] = None,
    attempt: Optional[int] = None,
    duration_ms: Optional[float] = None,
) -> Dict[str, Any]:
    """Build a structured log record dict for a pipeline event."""
    record: Dict[str, Any] = {
        "timestamp": _utc_timestamp(),
        "event": event,
    }
    if destination is not None:
        record["destination"] = destination
    if status is not None:
        record["status"] = status
    if error is not None:
        record["error"] = error
    if attempt is not None:
        record["attempt"] = attempt
    if duration_ms is not None:
        record["duration_ms"] = round(duration_ms, 3)
    if payload is not None:
        record["payload_keys"] = list(payload.keys())
    return record


def log_event(
    event: str,
    level: int = logging.INFO,
    **kwargs: Any,
) -> None:
    """Emit a structured JSON log line for the given pipeline event."""
    record = build_log_record(event, **kwargs)
    logger.log(level, json.dumps(record))


def log_delivery_attempt(
    destination: str,
    attempt: int,
    status_code: Optional[int] = None,
    error: Optional[str] = None,
    duration_ms: Optional[float] = None,
) -> None:
    """Convenience wrapper for logging a delivery attempt."""
    success = error is None and status_code is not None and status_code < 400
    level = logging.INFO if success else logging.WARNING
    log_event(
        event="delivery_attempt",
        level=level,
        destination=destination,
        status=str(status_code) if status_code is not None else "error",
        error=error,
        attempt=attempt,
        duration_ms=duration_ms,
    )
