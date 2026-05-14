"""Tests for hookpipe.payload_size_guard."""

import pytest

from hookpipe.payload_size_guard import (
    DEFAULT_MAX_BYTES,
    PayloadSizeError,
    check_payload_size,
    with_size_guard,
)


# ---------------------------------------------------------------------------
# check_payload_size
# ---------------------------------------------------------------------------

def test_exact_limit_passes():
    body = b"x" * DEFAULT_MAX_BYTES
    # Should not raise
    check_payload_size(body)


def test_below_limit_passes():
    check_payload_size(b"hello world", max_bytes=100)


def test_exceeds_limit_raises():
    with pytest.raises(PayloadSizeError):
        check_payload_size(b"x" * 101, max_bytes=100)


def test_error_message_contains_sizes():
    with pytest.raises(PayloadSizeError, match="101"):
        check_payload_size(b"x" * 101, max_bytes=100)


def test_error_message_contains_route_key():
    with pytest.raises(PayloadSizeError, match="my-route"):
        check_payload_size(b"x" * 10, max_bytes=5, route_key="my-route")


def test_error_message_no_route_key_no_spurious_text():
    with pytest.raises(PayloadSizeError) as exc_info:
        check_payload_size(b"x" * 10, max_bytes=5)
    assert "route" not in str(exc_info.value)


def test_empty_body_passes():
    check_payload_size(b"", max_bytes=1)


def test_invalid_max_bytes_zero_raises():
    with pytest.raises(ValueError):
        check_payload_size(b"hello", max_bytes=0)


def test_invalid_max_bytes_negative_raises():
    with pytest.raises(ValueError):
        check_payload_size(b"hello", max_bytes=-1)


def test_invalid_max_bytes_string_raises():
    with pytest.raises(ValueError):
        check_payload_size(b"hello", max_bytes="100")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# with_size_guard
# ---------------------------------------------------------------------------

def test_returns_callable():
    guarded = with_size_guard(lambda b: b, max_bytes=100)
    assert callable(guarded)


def test_valid_payload_delegated_to_handler():
    results = []
    guarded = with_size_guard(lambda b: results.append(b), max_bytes=100)
    guarded(b"ok")
    assert results == [b"ok"]


def test_oversized_payload_not_delegated():
    calls = []
    guarded = with_size_guard(lambda b: calls.append(b), max_bytes=5)
    with pytest.raises(PayloadSizeError):
        guarded(b"toolong")
    assert calls == []


def test_with_size_guard_passes_route_key_in_error():
    guarded = with_size_guard(lambda b: b, max_bytes=5, route_key="orders")
    with pytest.raises(PayloadSizeError, match="orders"):
        guarded(b"toolong")


def test_handler_return_value_propagated():
    guarded = with_size_guard(lambda b: {"size": len(b)}, max_bytes=100)
    result = guarded(b"hello")
    assert result == {"size": 5}
