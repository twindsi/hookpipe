"""Timeout guard — wraps a delivery callable with a per-route deadline.

Usage::

    guarded = with_timeout(deliver_fn, route_key="github", timeout=5.0)
    result  = guarded(payload, headers)
"""

from __future__ import annotations

import signal
import functools
from typing import Any, Callable


class TimeoutError(Exception):
    """Raised when a delivery callable exceeds its allowed wall-clock time."""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _raise_timeout(signum: int, frame: Any) -> None:  # pragma: no cover
    raise TimeoutError("delivery timed out")


def _timeout_context(seconds: float):
    """Context manager that raises TimeoutError after *seconds* elapsed."""
    import contextlib

    @contextlib.contextmanager
    def _ctx():
        old = signal.signal(signal.SIGALRM, _raise_timeout)
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            yield
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, old)

    return _ctx()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def check_timeout(seconds: float, route_key: str) -> None:
    """Validate *seconds* is a positive finite number."""
    if not isinstance(seconds, (int, float)) or seconds <= 0:
        raise ValueError(
            f"timeout for route '{route_key}' must be a positive number, got {seconds!r}"
        )


def with_timeout(
    fn: Callable[..., Any],
    *,
    route_key: str,
    timeout: float,
) -> Callable[..., Any]:
    """Return a wrapper around *fn* that enforces a wall-clock *timeout*.

    Raises :class:`TimeoutError` if the call takes longer than *timeout* seconds.
    Only supported on POSIX systems (requires ``signal.SIGALRM``).
    """
    check_timeout(timeout, route_key)

    @functools.wraps(fn)
    def _wrapped(*args: Any, **kwargs: Any) -> Any:
        with _timeout_context(timeout):
            return fn(*args, **kwargs)

    _wrapped._route_key = route_key  # type: ignore[attr-defined]
    _wrapped._timeout = timeout       # type: ignore[attr-defined]
    return _wrapped
