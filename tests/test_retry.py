"""Tests for hookpipe.retry module."""

import pytest
from unittest.mock import MagicMock, call
from hookpipe.retry import with_retry, RetryError, _compute_delay


# ---------------------------------------------------------------------------
# _compute_delay
# ---------------------------------------------------------------------------

def test_compute_delay_first_attempt():
    assert _compute_delay(0, backoff_base=2.0, max_delay=60.0) == 1.0


def test_compute_delay_second_attempt():
    assert _compute_delay(1, backoff_base=2.0, max_delay=60.0) == 2.0


def test_compute_delay_capped_by_max():
    assert _compute_delay(10, backoff_base=2.0, max_delay=60.0) == 60.0


# ---------------------------------------------------------------------------
# with_retry — success paths
# ---------------------------------------------------------------------------

def test_success_on_first_attempt():
    fn = MagicMock(return_value="ok")
    result = with_retry(fn, max_attempts=3, _sleep=MagicMock())
    assert result == "ok"
    fn.assert_called_once()


def test_success_on_second_attempt():
    sleep = MagicMock()
    fn = MagicMock(side_effect=[ValueError("boom"), "ok"])
    result = with_retry(fn, max_attempts=3, _sleep=sleep)
    assert result == "ok"
    assert fn.call_count == 2
    sleep.assert_called_once()


def test_success_on_last_attempt():
    sleep = MagicMock()
    fn = MagicMock(side_effect=[RuntimeError(), RuntimeError(), "final"])
    result = with_retry(fn, max_attempts=3, _sleep=sleep)
    assert result == "final"
    assert fn.call_count == 3
    assert sleep.call_count == 2


# ---------------------------------------------------------------------------
# with_retry — failure paths
# ---------------------------------------------------------------------------

def test_raises_retry_error_after_all_attempts():
    sleep = MagicMock()
    fn = MagicMock(side_effect=ConnectionError("timeout"))
    with pytest.raises(RetryError, match="All 3 attempt"):
        with_retry(fn, max_attempts=3, _sleep=sleep)
    assert fn.call_count == 3


def test_non_retryable_exception_propagates_immediately():
    sleep = MagicMock()
    fn = MagicMock(side_effect=ValueError("bad value"))
    with pytest.raises(ValueError):
        with_retry(
            fn,
            max_attempts=5,
            retryable_exceptions=(ConnectionError,),
            _sleep=sleep,
        )
    fn.assert_called_once()
    sleep.assert_not_called()


def test_max_attempts_one_no_sleep():
    sleep = MagicMock()
    fn = MagicMock(side_effect=IOError("fail"))
    with pytest.raises(RetryError):
        with_retry(fn, max_attempts=1, _sleep=sleep)
    fn.assert_called_once()
    sleep.assert_not_called()


# ---------------------------------------------------------------------------
# with_retry — backoff timing
# ---------------------------------------------------------------------------

def test_backoff_delays_are_correct():
    sleep = MagicMock()
    fn = MagicMock(side_effect=[OSError(), OSError(), OSError()])
    with pytest.raises(RetryError):
        with_retry(fn, max_attempts=3, backoff_base=2.0, max_delay=60.0, _sleep=sleep)
    assert sleep.call_args_list == [call(1.0), call(2.0)]


def test_invalid_max_attempts_raises():
    with pytest.raises(ValueError):
        with_retry(lambda: None, max_attempts=0)
