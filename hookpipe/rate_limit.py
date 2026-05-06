"""Simple in-memory rate limiting for incoming webhook routes."""

import time
from collections import defaultdict, deque
from typing import Dict, Deque


class RateLimitError(Exception):
    """Raised when a rate limit is exceeded."""


# route_key -> deque of timestamps (seconds, float)
_windows: Dict[str, Deque[float]] = defaultdict(deque)


def _now() -> float:
    return time.monotonic()


def check_rate_limit(route_key: str, max_requests: int, window_seconds: float) -> None:
    """Raise RateLimitError if *route_key* has exceeded *max_requests* within
    the rolling *window_seconds* window.

    Args:
        route_key: Unique identifier for the route / source being tracked.
        max_requests: Maximum number of requests allowed in the window.
        window_seconds: Length of the rolling window in seconds.

    Raises:
        RateLimitError: If the limit has been exceeded.
        ValueError: If max_requests < 1 or window_seconds <= 0.
    """
    if max_requests < 1:
        raise ValueError("max_requests must be >= 1")
    if window_seconds <= 0:
        raise ValueError("window_seconds must be > 0")

    now = _now()
    cutoff = now - window_seconds
    window = _windows[route_key]

    # Evict timestamps outside the rolling window
    while window and window[0] <= cutoff:
        window.popleft()

    if len(window) >= max_requests:
        oldest = window[0]
        retry_after = window_seconds - (now - oldest)
        raise RateLimitError(
            f"Rate limit exceeded for '{route_key}': "
            f"{max_requests} requests per {window_seconds}s. "
            f"Retry after {retry_after:.2f}s."
        )

    window.append(now)


def reset(route_key: str | None = None) -> None:
    """Clear rate-limit state.  Pass *route_key* to reset a single key,
    or omit / pass None to reset all keys."""
    if route_key is None:
        _windows.clear()
    else:
        _windows.pop(route_key, None)


def current_count(route_key: str, window_seconds: float) -> int:
    """Return how many requests are recorded within the rolling window."""
    now = _now()
    cutoff = now - window_seconds
    window = _windows[route_key]
    while window and window[0] <= cutoff:
        window.popleft()
    return len(window)
