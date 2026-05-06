"""Event replay buffer: stores recent events and replays them on demand."""

import time
import hashlib
import json
from collections import deque
from typing import Any, Dict, List, Optional


class ReplayError(Exception):
    """Raised when replay operations fail."""


_buffer: deque = deque()
_max_size: int = 500
_ttl_seconds: int = 3600


def _now() -> float:
    return time.monotonic()


def _event_key(payload: Dict[str, Any]) -> str:
    """Compute a stable key for a payload."""
    serialized = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode()).hexdigest()


def store_event(payload: Dict[str, Any], route_key: str) -> str:
    """Store an event in the replay buffer. Returns the event key."""
    if not isinstance(payload, dict):
        raise ReplayError("payload must be a dict")
    if not route_key:
        raise ReplayError("route_key must not be empty")
    key = _event_key(payload)
    _buffer.append({
        "key": key,
        "route_key": route_key,
        "payload": payload,
        "stored_at": _now(),
    })
    while len(_buffer) > _max_size:
        _buffer.popleft()
    return key


def _evict_expired() -> None:
    now = _now()
    while _buffer and (now - _buffer[0]["stored_at"]) > _ttl_seconds:
        _buffer.popleft()


def get_events(route_key: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return stored events, optionally filtered by route_key."""
    _evict_expired()
    events = list(_buffer)
    if route_key is not None:
        events = [e for e in events if e["route_key"] == route_key]
    return [{"key": e["key"], "route_key": e["route_key"], "payload": e["payload"]} for e in events]


def get_event_by_key(key: str) -> Optional[Dict[str, Any]]:
    """Return a single event by its key, or None if not found."""
    _evict_expired()
    for entry in _buffer:
        if entry["key"] == key:
            return {"key": entry["key"], "route_key": entry["route_key"], "payload": entry["payload"]}
    return None


def reset() -> None:
    """Clear the replay buffer (used in tests)."""
    _buffer.clear()
