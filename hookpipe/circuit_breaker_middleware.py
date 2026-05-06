"""Middleware that integrates circuit breaker with delivery and retry."""

from typing import Any, Callable, Dict

from hookpipe.circuit_breaker import (
    CircuitBreakerError,
    check_circuit,
    record_failure,
    record_success,
)
from hookpipe.logging_utils import log_delivery_attempt


def with_circuit_breaker(
    fn: Callable[..., Any],
    target: Dict[str, Any],
    *args: Any,
    failure_threshold: int = 5,
    recovery_timeout: int = 30,
    **kwargs: Any,
) -> Any:
    """Call *fn* guarded by the circuit breaker for *target*.

    Parameters
    ----------
    fn:
        The delivery callable to wrap, e.g. ``deliver``.
    target:
        Target configuration dict; must contain a ``"url"`` key used as the
        circuit key.
    *args, **kwargs:
        Forwarded verbatim to *fn*.

    Returns
    -------
    The return value of *fn* on success.

    Raises
    ------
    CircuitBreakerError
        When the circuit is open and the call is blocked.
    Exception
        Any exception raised by *fn* is re-raised after recording the failure.
    """
    key = target.get("url", str(target))

    check_circuit(key, failure_threshold=failure_threshold,
                  recovery_timeout=recovery_timeout)

    try:
        result = fn(*args, **kwargs)
        record_success(key)
        return result
    except CircuitBreakerError:
        raise
    except Exception as exc:
        record_failure(key, failure_threshold=failure_threshold)
        log_delivery_attempt(
            target_url=key,
            status_code=None,
            success=False,
            error=str(exc),
        )
        raise
