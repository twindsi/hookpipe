"""Simple in-memory metrics collection for hookpipe."""

import threading
import time
from typing import Dict, Any


class MetricsError(Exception):
    """Raised when a metrics operation fails."""


_lock = threading.Lock()

_counters: Dict[str, int] = {
    "requests_received": 0,
    "requests_rejected": 0,
    "deliveries_attempted": 0,
    "deliveries_succeeded": 0,
    "deliveries_failed": 0,
    "retries_total": 0,
}

_timings: Dict[str, list] = {
    "delivery_duration_seconds": [],
}

_start_time: float = time.monotonic()


def increment(counter: str, amount: int = 1) -> None:
    """Increment a named counter by the given amount."""
    with _lock:
        if counter not in _counters:
            raise MetricsError(f"Unknown counter: {counter!r}")
        _counters[counter] += amount


def record_timing(metric: str, duration: float) -> None:
    """Append a timing sample (in seconds) to a named timing metric."""
    with _lock:
        if metric not in _timings:
            raise MetricsError(f"Unknown timing metric: {metric!r}")
        _timings[metric].append(duration)


def snapshot() -> Dict[str, Any]:
    """Return a point-in-time snapshot of all metrics."""
    with _lock:
        counters_copy = dict(_counters)
        timings_summary: Dict[str, Any] = {}
        for name, samples in _timings.items():
            if samples:
                timings_summary[name] = {
                    "count": len(samples),
                    "sum": round(sum(samples), 6),
                    "min": round(min(samples), 6),
                    "max": round(max(samples), 6),
                    "avg": round(sum(samples) / len(samples), 6),
                }
            else:
                timings_summary[name] = {"count": 0, "sum": 0.0, "min": None, "max": None, "avg": None}

    return {
        "uptime_seconds": round(time.monotonic() - _start_time, 3),
        "counters": counters_copy,
        "timings": timings_summary,
    }


def reset() -> None:
    """Reset all metrics to zero (intended for testing)."""
    global _start_time
    with _lock:
        for key in _counters:
            _counters[key] = 0
        for key in _timings:
            _timings[key] = []
        _start_time = time.monotonic()
