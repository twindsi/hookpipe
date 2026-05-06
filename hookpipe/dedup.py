"""Payload deduplication using a sliding window of seen event IDs."""

import hashlib
import time
from collections import OrderedDict
from typing import Any, Dict, Optional


class DedupError(Exception):
    """Raised when deduplication check fails due to misconfiguration."""


# Module-level store: {event_id: expiry_timestamp}
_seen: OrderedDict = OrderedDict()

_DEFAULT_TTL = 300  # seconds


def _now() -> float:
    return time.monotonic()


def _evict_expired(ttl: float) -> None:
    """Remove entries whose TTL has elapsed."""
    cutoff = _now() - ttl
    expired = [k for k, ts in _seen.items() if ts < cutoff]
    for k in expired:
        del _seen[k]


def compute_event_id(payload: Dict[str, Any], id_field: Optional[str] = None) -> str:
    """Return a stable ID for *payload*.

    If *id_field* is given, its value (coerced to str) is used directly.
    Otherwise a SHA-256 digest of the sorted JSON representation is returned.
    """
    if id_field is not None:
        parts = id_field.split(".")
        value = payload
        for part in parts:
            if not isinstance(value, dict) or part not in value:
                raise DedupError(
                    f"id_field '{id_field}' not found in payload"
                )
            value = value[part]
        return str(value)

    import json
    serialised = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialised.encode()).hexdigest()


def is_duplicate(
    payload: Dict[str, Any],
    id_field: Optional[str] = None,
    ttl: float = _DEFAULT_TTL,
) -> bool:
    """Return True if *payload* has been seen within *ttl* seconds.

    Side-effect: records the event ID when first seen.
    """
    if ttl <= 0:
        raise DedupError("ttl must be a positive number")

    _evict_expired(ttl)
    event_id = compute_event_id(payload, id_field)

    if event_id in _seen:
        return True

    _seen[event_id] = _now()
    return False


def reset() -> None:
    """Clear all stored event IDs (useful in tests)."""
    _seen.clear()
