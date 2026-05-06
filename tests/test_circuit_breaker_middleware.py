"""Tests for hookpipe.circuit_breaker_middleware."""

import pytest
from hookpipe.circuit_breaker import reset, get_status, CIRCUIT_OPEN, CIRCUIT_CLOSED
from hookpipe.circuit_breaker_middleware import with_circuit_breaker
from hookpipe.circuit_breaker import CircuitBreakerError


TARGET = {"url": "https://example.com/hook"}


@pytest.fixture(autouse=True)
def clean():
    reset()
    yield
    reset()


def _ok(*_args, **_kwargs):
    return {"status": "ok"}


def _fail(*_args, **_kwargs):
    raise RuntimeError("downstream error")


def test_success_returns_result():
    result = with_circuit_breaker(_ok, TARGET)
    assert result == {"status": "ok"}


def test_success_keeps_circuit_closed():
    with_circuit_breaker(_ok, TARGET)
    assert get_status(TARGET["url"]) == CIRCUIT_CLOSED


def test_failure_increments_and_reraises():
    with pytest.raises(RuntimeError, match="downstream error"):
        with_circuit_breaker(_fail, TARGET)


def test_repeated_failures_open_circuit():
    for _ in range(5):
        try:
            with_circuit_breaker(_fail, TARGET, failure_threshold=5)
        except RuntimeError:
            pass
    assert get_status(TARGET["url"]) == CIRCUIT_OPEN


def test_open_circuit_raises_circuit_breaker_error():
    for _ in range(5):
        try:
            with_circuit_breaker(_fail, TARGET, failure_threshold=5)
        except RuntimeError:
            pass
    with pytest.raises(CircuitBreakerError):
        with_circuit_breaker(_ok, TARGET, failure_threshold=5)


def test_custom_failure_threshold():
    for _ in range(3):
        try:
            with_circuit_breaker(_fail, TARGET, failure_threshold=3)
        except RuntimeError:
            pass
    assert get_status(TARGET["url"]) == CIRCUIT_OPEN


def test_target_without_url_uses_str_fallback():
    target_no_url = {"method": "POST"}
    result = with_circuit_breaker(_ok, target_no_url)
    assert result == {"status": "ok"}
