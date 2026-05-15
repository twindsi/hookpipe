"""Tests for hookpipe.timeout_guard."""

import time
import pytest

from hookpipe.timeout_guard import (
    TimeoutError,
    check_timeout,
    with_timeout,
)


# ---------------------------------------------------------------------------
# check_timeout
# ---------------------------------------------------------------------------

def test_check_timeout_valid_int():
    check_timeout(5, "my-route")  # must not raise


def test_check_timeout_valid_float():
    check_timeout(0.5, "my-route")  # must not raise


def test_check_timeout_zero_raises():
    with pytest.raises(ValueError, match="positive number"):
        check_timeout(0, "my-route")


def test_check_timeout_negative_raises():
    with pytest.raises(ValueError, match="positive number"):
        check_timeout(-1, "my-route")


def test_check_timeout_string_raises():
    with pytest.raises(ValueError, match="positive number"):
        check_timeout("5", "my-route")  # type: ignore[arg-type]


def test_check_timeout_error_contains_route_key():
    with pytest.raises(ValueError, match="webhook-inbound"):
        check_timeout(0, "webhook-inbound")


# ---------------------------------------------------------------------------
# with_timeout — metadata
# ---------------------------------------------------------------------------

def test_with_timeout_returns_callable():
    wrapped = with_timeout(lambda: None, route_key="r", timeout=2)
    assert callable(wrapped)


def test_with_timeout_preserves_function_name():
    def my_deliver():
        return "ok"

    wrapped = with_timeout(my_deliver, route_key="r", timeout=2)
    assert wrapped.__name__ == "my_deliver"


def test_with_timeout_stores_route_key():
    wrapped = with_timeout(lambda: None, route_key="stripe", timeout=3)
    assert wrapped._route_key == "stripe"


def test_with_timeout_stores_timeout_value():
    wrapped = with_timeout(lambda: None, route_key="r", timeout=7.5)
    assert wrapped._timeout == 7.5


def test_with_timeout_invalid_timeout_raises():
    with pytest.raises(ValueError):
        with_timeout(lambda: None, route_key="r", timeout=-1)


# ---------------------------------------------------------------------------
# with_timeout — behaviour
# ---------------------------------------------------------------------------

def test_success_returns_result():
    def fast():
        return {"status": "delivered"}

    wrapped = with_timeout(fast, route_key="r", timeout=2)
    assert wrapped() == {"status": "delivered"}


def test_success_passes_args_and_kwargs():
    def echo(a, b=0):
        return a + b

    wrapped = with_timeout(echo, route_key="r", timeout=2)
    assert wrapped(3, b=4) == 7


def test_timeout_raises_on_slow_function():
    def slow():
        time.sleep(5)

    wrapped = with_timeout(slow, route_key="r", timeout=0.1)
    with pytest.raises(TimeoutError):
        wrapped()


def test_timeout_does_not_trigger_for_fast_function():
    def fast():
        return "done"

    wrapped = with_timeout(fast, route_key="r", timeout=2)
    assert wrapped() == "done"  # should complete well within 2 s
