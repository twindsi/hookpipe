"""Payload size enforcement for incoming webhook requests."""

from typing import Optional


class PayloadSizeError(Exception):
    """Raised when a payload exceeds the configured size limit."""


# Default maximum payload size in bytes (512 KB)
DEFAULT_MAX_BYTES = 512 * 1024


def check_payload_size(
    raw_body: bytes,
    max_bytes: int = DEFAULT_MAX_BYTES,
    route_key: Optional[str] = None,
) -> None:
    """Raise PayloadSizeError if *raw_body* exceeds *max_bytes*.

    Args:
        raw_body:  The raw request body as bytes.
        max_bytes: Maximum allowed size in bytes (inclusive).
        route_key: Optional route identifier used in the error message.

    Raises:
        PayloadSizeError: When ``len(raw_body) > max_bytes``.
        ValueError: When *max_bytes* is not a positive integer.
    """
    if not isinstance(max_bytes, int) or max_bytes <= 0:
        raise ValueError(f"max_bytes must be a positive integer, got {max_bytes!r}")

    actual = len(raw_body)
    if actual > max_bytes:
        location = f" for route '{route_key}'" if route_key else ""
        raise PayloadSizeError(
            f"Payload size {actual} bytes exceeds limit of {max_bytes} bytes{location}."
        )


def with_size_guard(
    handler,
    max_bytes: int = DEFAULT_MAX_BYTES,
    route_key: Optional[str] = None,
):
    """Wrap *handler* so that oversized payloads are rejected before processing.

    Args:
        handler:   Callable ``(raw_body: bytes) -> any`` to protect.
        max_bytes: Maximum allowed payload size in bytes.
        route_key: Optional route identifier forwarded to :func:`check_payload_size`.

    Returns:
        A new callable with the same signature as *handler* that first
        enforces the size limit and then delegates to the original handler.
    """

    def _guarded(raw_body: bytes):
        check_payload_size(raw_body, max_bytes=max_bytes, route_key=route_key)
        return handler(raw_body)

    return _guarded
