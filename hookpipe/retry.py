"""Retry logic for failed webhook deliveries."""

import time
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)


class RetryError(Exception):
    """Raised when all retry attempts are exhausted."""
    pass


DEFAULT_BACKOFF_BASE = 2.0
DEFAULT_MAX_DELAY = 60.0


def _compute_delay(attempt: int, backoff_base: float, max_delay: float) -> float:
    """Compute exponential backoff delay for a given attempt (0-indexed)."""
    delay = backoff_base ** attempt
    return min(delay, max_delay)


def with_retry(
    fn: Callable[[], Any],
    max_attempts: int = 3,
    backoff_base: float = DEFAULT_BACKOFF_BASE,
    max_delay: float = DEFAULT_MAX_DELAY,
    retryable_exceptions: tuple = (Exception,),
    _sleep: Callable[[float], None] = time.sleep,
) -> Any:
    """Call *fn* up to *max_attempts* times, retrying on *retryable_exceptions*.

    Args:
        fn: Zero-argument callable to invoke.
        max_attempts: Total number of attempts before raising RetryError.
        backoff_base: Base for exponential backoff calculation.
        max_delay: Maximum delay in seconds between attempts.
        retryable_exceptions: Tuple of exception types that trigger a retry.
        _sleep: Injectable sleep function (for testing).

    Returns:
        The return value of *fn* on success.

    Raises:
        RetryError: When all attempts are exhausted.
    """
    if max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")

    last_exc: Exception = RuntimeError("No attempts made")

    for attempt in range(max_attempts):
        try:
            return fn()
        except retryable_exceptions as exc:  # type: ignore[misc]
            last_exc = exc
            if attempt < max_attempts - 1:
                delay = _compute_delay(attempt, backoff_base, max_delay)
                logger.warning(
                    "Attempt %d/%d failed: %s. Retrying in %.1fs.",
                    attempt + 1,
                    max_attempts,
                    exc,
                    delay,
                )
                _sleep(delay)
            else:
                logger.error(
                    "Attempt %d/%d failed: %s. No more retries.",
                    attempt + 1,
                    max_attempts,
                    exc,
                )

    raise RetryError(
        f"All {max_attempts} attempt(s) failed. Last error: {last_exc}"
    ) from last_exc
