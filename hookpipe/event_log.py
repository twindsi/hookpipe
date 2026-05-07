"""Persistent in-memory event log for auditing processed webhook events."""

import time
from typing import Any, Dict, List, Optional

EVENT_LOG_MAX_SIZE = 500
EVENT_LOG_TTL = 3600  # seconds

_log: List[Dict[str, Any]] = []


class EventLogError(Exception):
    pass


def _now() -> float:
    return time.monotonic()


def _evict_expired() -> None:
    cutoff = _now() - EVENT_LOG_TTL
    global _log
    _log = [entry for entry in _log if entry["_ts"] >= cutoff]


def append_event(
    route_key: str,
    payload: Dict[str, Any],
    status: str,
    target_url: Optional[str] = None,
    error: Optional[str] = None,
) -> Dict[str, Any]:
    """Append an auditable event entry to the in-memory log."""
    if not route_key or not isinstance(route_key, str):
        raise EventLogError("route_key must be a non-empty string")
    if status not in ("success", "failure", "filtered", "duplicate"):
        raise EventLogError(f"Invalid status: {status!r}")

    _evict_expired()

    if len(_log) >= EVENT_LOG_MAX_SIZE:
        _log.pop(0)

    entry: Dict[str, Any] = {
        "_ts": _now(),
        "route_key": route_key,
        "status": status,
        "payload": payload,
    }
    if target_url is not None:
        entry["target_url"] = target_url
    if error is not None:
        entry["error"] = error

    _log.append(entry)
    return entry


def query_events(
    route_key: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Return recent log entries, optionally filtered by route_key or status."""
    _evict_expired()
    results = list(_log)
    if route_key is not None:
        results = [e for e in results if e["route_key"] == route_key]
    if status is not None:
        results = [e for e in results if e["status"] == status]
    return results[-limit:]


def reset() -> None:
    """Clear all log entries (primarily for testing)."""
    global _log
    _log = []
