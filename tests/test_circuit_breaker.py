"""Tests for hookpipe.circuit_breaker."""

import time
import pytest
from hookpipe.circuit_breaker import (
    CircuitBreakerError,
    check_circuit,
    record_success,
    record_failure,
    get_status,
    reset,
    CIRCUIT_CLOSED,
    CIRCUIT_OPEN,
    CIRCUIT_HALF_OPEN,
)


@pytest.fixture(autouse=True)
def clean_state():
    reset()
    yield
    reset()


def test_new_circuit_is_closed():
    assert get_status("target-a") == CIRCUIT_CLOSED


def test_check_circuit_passes_when_closed():
    check_circuit("target-a")  # should not raise


def test_circuit_opens_after_threshold():
    for _ in range(5):
        record_failure("target-a")
    assert get_status("target-a") == CIRCUIT_OPEN


def test_circuit_does_not_open_below_threshold():
    for _ in range(4):
        record_failure("target-a")
    assert get_status("target-a") == CIRCUIT_CLOSED


def test_check_circuit_raises_when_open():
    for _ in range(5):
        record_failure("target-a")
    with pytest.raises(CircuitBreakerError, match="Circuit open"):
        check_circuit("target-a")


def test_error_message_contains_key():
    for _ in range(5):
        record_failure("my-route")
    with pytest.raises(CircuitBreakerError, match="my-route"):
        check_circuit("my-route")


def test_record_success_closes_circuit():
    for _ in range(5):
        record_failure("target-a")
    record_success("target-a")
    assert get_status("target-a") == CIRCUIT_CLOSED


def test_record_success_resets_failure_count():
    for _ in range(4):
        record_failure("target-a")
    record_success("target-a")
    record_failure("target-a")  # 1 failure after reset; should still be closed
    assert get_status("target-a") == CIRCUIT_CLOSED


def test_circuit_transitions_to_half_open_after_timeout(monkeypatch):
    start = time.monotonic()
    monkeypatch.setattr("hookpipe.circuit_breaker.time.monotonic",
                        lambda: start + 31)
    for _ in range(5):
        record_failure("target-a")
    # patch opened_at so elapsed >= recovery_timeout
    from hookpipe import circuit_breaker
    circuit_breaker._state["target-a"]["opened_at"] = start
    check_circuit("target-a", recovery_timeout=30)  # should not raise
    assert get_status("target-a") == CIRCUIT_HALF_OPEN


def test_reset_single_key():
    record_failure("target-a")
    reset("target-a")
    assert get_status("target-a") == CIRCUIT_CLOSED


def test_reset_all_keys():
    record_failure("target-a")
    record_failure("target-b")
    reset()
    assert get_status("target-a") == CIRCUIT_CLOSED
    assert get_status("target-b") == CIRCUIT_CLOSED


def test_custom_failure_threshold():
    for _ in range(3):
        record_failure("target-a", failure_threshold=3)
    assert get_status("target-a") == CIRCUIT_OPEN
