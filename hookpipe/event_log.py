"""In-memory event log with TTL eviction and query support."""
import hashlib
import time
from typing import Any, Dict, List, Optional

_VALID_STATUSES = {"success", "failure", "filtered", "retried"}
_TTL_SECONDS = 3600
_MAX_ENTRIES = 10_000

_store: List[Dict[str, Any]] = []


class EventLogError(Exception):
    pass


def _now() -> float:
    return time.time()


def _evict_expired() -> None:
    cutoff = _now() - _TTL_SECONDS
    global _store
    _store = [e for e in _store if e["_ts"] >= cutoff]


def reset() -> None:
    """Clear all stored events (primarily for testing)."""
    global _store
    _store = []


def append_event(
    route_key: str,
    payload: Dict[str, Any],
    status: str,
    *,
    error: Optional[str] = None,
    target_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Append a processed-event record to the log."""
    if not route_key:
        raise EventLogError("route_key must not be empty")
    if status not in _VALID_STATUSES:
        raise EventLogError(
            f"invalid status {status!r}; must be one of {sorted(_VALID_STATUSES)}"
        )

    _evict_expired()
    if len(_store) >= _MAX_ENTRIES:
        _store.pop(0)

    raw = json_stable(payload)
    event_id = hashlib.sha256(f"{route_key}:{raw}".encode()).hexdigest()[:16]

    entry: Dict[str, Any] = {
        "event_id": event_id,
        "route_key": route_key,
        "status": status,
        "timestamp": _now(),
        "_ts": _now(),
    }
    if error is not None:
        entry["error"] = error
    if target_url is not None:
        entry["target_url"] = target_url

    _store.append(entry)
    return {k: v for k, v in entry.items() if k != "_ts"}


def query_events(
    *,
    route_key: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Return log entries matching the given filters, newest-first."""
    _evict_expired()
    results = list(reversed(_store))
    if route_key is not None:
        results = [e for e in results if e["route_key"] == route_key]
    if status is not None:
        results = [e for e in results if e["status"] == status]
    results = results[:limit]
    return [{k: v for k, v in e.items() if k != "_ts"} for e in results]


def json_stable(obj: Any) -> str:
    import json
    return json.dumps(obj, sort_keys=True, default=str)
