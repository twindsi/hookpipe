"""Tests for hookpipe.rate_limit."""

import time
import pytest
from unittest.mock import patch

from hookpipe.rate_limit import (
    RateLimitError,
    check_rate_limit,
    current_count,
    reset,
)

ROUTE = "test-route"


@pytest.fixture(autouse=True)
def clean_state():
    reset()
    yield
    reset()


def test_single_request_within_limit():
    check_rate_limit(ROUTE, max_requests=5, window_seconds=10)
    assert current_count(ROUTE, 10) == 1


def test_multiple_requests_within_limit():
    for _ in range(5):
        check_rate_limit(ROUTE, max_requests=5, window_seconds=10)
    assert current_count(ROUTE, 10) == 5


def test_exceeds_limit_raises():
    for _ in range(3):
        check_rate_limit(ROUTE, max_requests=3, window_seconds=10)
    with pytest.raises(RateLimitError, match="Rate limit exceeded"):
        check_rate_limit(ROUTE, max_requests=3, window_seconds=10)


def test_error_message_contains_route_key():
    check_rate_limit(ROUTE, max_requests=1, window_seconds=10)
    with pytest.raises(RateLimitError, match=ROUTE):
        check_rate_limit(ROUTE, max_requests=1, window_seconds=10)


def test_window_evicts_old_timestamps():
    base = 1000.0
    with patch("hookpipe.rate_limit._now", side_effect=[base, base + 11, base + 11]):
        check_rate_limit(ROUTE, max_requests=1, window_seconds=10)
        # Second call: old timestamp is outside window, should not raise
        check_rate_limit(ROUTE, max_requests=1, window_seconds=10)


def test_different_routes_are_independent():
    check_rate_limit("route-a", max_requests=1, window_seconds=10)
    # route-b has its own counter
    check_rate_limit("route-b", max_requests=1, window_seconds=10)


def test_reset_single_route():
    check_rate_limit(ROUTE, max_requests=1, window_seconds=10)
    reset(ROUTE)
    assert current_count(ROUTE, 10) == 0


def test_reset_all():
    check_rate_limit("r1", max_requests=5, window_seconds=10)
    check_rate_limit("r2", max_requests=5, window_seconds=10)
    reset()
    assert current_count("r1", 10) == 0
    assert current_count("r2", 10) == 0


def test_invalid_max_requests_raises():
    with pytest.raises(ValueError, match="max_requests"):
        check_rate_limit(ROUTE, max_requests=0, window_seconds=10)


def test_invalid_window_raises():
    with pytest.raises(ValueError, match="window_seconds"):
        check_rate_limit(ROUTE, max_requests=5, window_seconds=0)


def test_current_count_returns_zero_for_unknown_route():
    assert current_count("unknown", 10) == 0
