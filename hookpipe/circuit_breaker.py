"""Circuit breaker for outbound delivery targets."""

import time
from typing import Dict

CIRCUIT_OPEN = "open"
CIRCUIT_CLOSED = "closed"
CIRCUIT_HALF_OPEN = "half_open"

DEFAULT_FAILURE_THRESHOLD = 5
DEFAULT_RECOVERY_TIMEOUT = 30  # seconds
DEFAULT_HALF_OPEN_MAX = 1


class CircuitBreakerError(Exception):
    """Raised when a circuit is open and the call is blocked."""


_state: Dict[str, dict] = {}


def _get_or_create(key: str) -> dict:
    if key not in _state:
        _state[key] = {
            "status": CIRCUIT_CLOSED,
            "failures": 0,
            "opened_at": None,
            "half_open_attempts": 0,
        }
    return _state[key]


def check_circuit(key: str, failure_threshold: int = DEFAULT_FAILURE_THRESHOLD,
                  recovery_timeout: int = DEFAULT_RECOVERY_TIMEOUT) -> None:
    """Raise CircuitBreakerError if the circuit for key is open."""
    entry = _get_or_create(key)

    if entry["status"] == CIRCUIT_OPEN:
        elapsed = time.monotonic() - entry["opened_at"]
        if elapsed >= recovery_timeout:
            entry["status"] = CIRCUIT_HALF_OPEN
            entry["half_open_attempts"] = 0
        else:
            raise CircuitBreakerError(
                f"Circuit open for '{key}'; retry after {recovery_timeout - elapsed:.1f}s"
            )

    if entry["status"] == CIRCUIT_HALF_OPEN:
        if entry["half_open_attempts"] >= DEFAULT_HALF_OPEN_MAX:
            raise CircuitBreakerError(
                f"Circuit half-open for '{key}'; probe attempt already in flight"
            )
        entry["half_open_attempts"] += 1


def record_success(key: str) -> None:
    """Record a successful delivery; close the circuit."""
    entry = _get_or_create(key)
    entry["status"] = CIRCUIT_CLOSED
    entry["failures"] = 0
    entry["opened_at"] = None
    entry["half_open_attempts"] = 0


def record_failure(key: str, failure_threshold: int = DEFAULT_FAILURE_THRESHOLD) -> None:
    """Record a failed delivery; open the circuit if threshold reached."""
    entry = _get_or_create(key)
    entry["failures"] += 1
    if entry["failures"] >= failure_threshold:
        entry["status"] = CIRCUIT_OPEN
        entry["opened_at"] = time.monotonic()


def get_status(key: str) -> str:
    """Return the current circuit status string for key."""
    return _get_or_create(key)["status"]


def reset(key: str = None) -> None:
    """Reset state for a specific key or all keys."""
    global _state
    if key is None:
        _state.clear()
    elif key in _state:
        del _state[key]
