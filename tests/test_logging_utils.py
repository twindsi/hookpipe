"""Tests for hookpipe.logging_utils."""

import json
import logging
from unittest.mock import patch

import pytest

from hookpipe.logging_utils import (
    build_log_record,
    log_delivery_attempt,
    log_event,
)


# ---------------------------------------------------------------------------
# build_log_record
# ---------------------------------------------------------------------------

def test_build_log_record_required_fields():
    record = build_log_record(event="test_event")
    assert record["event"] == "test_event"
    assert "timestamp" in record


def test_build_log_record_optional_fields_absent_by_default():
    record = build_log_record(event="test_event")
    for key in ("destination", "status", "error", "attempt", "duration_ms", "payload_keys"):
        assert key not in record


def test_build_log_record_all_fields():
    payload = {"action": "push", "ref": "main"}
    record = build_log_record(
        event="delivery_attempt",
        payload=payload,
        destination="https://example.com/hook",
        status="200",
        error=None,
        attempt=1,
        duration_ms=42.1234,
    )
    assert record["destination"] == "https://example.com/hook"
    assert record["status"] == "200"
    assert record["attempt"] == 1
    assert record["duration_ms"] == 42.123
    assert set(record["payload_keys"]) == {"action", "ref"}
    assert "error" not in record


def test_build_log_record_error_field():
    record = build_log_record(event="delivery_attempt", error="timeout")
    assert record["error"] == "timeout"


# ---------------------------------------------------------------------------
# log_event
# ---------------------------------------------------------------------------

def test_log_event_emits_json(caplog):
    with caplog.at_level(logging.INFO, logger="hookpipe"):
        log_event("pipeline_start", destination="https://example.com")
    assert len(caplog.records) == 1
    data = json.loads(caplog.records[0].getMessage())
    assert data["event"] == "pipeline_start"
    assert data["destination"] == "https://example.com"


def test_log_event_warning_level(caplog):
    with caplog.at_level(logging.WARNING, logger="hookpipe"):
        log_event("filter_rejected", level=logging.WARNING, error="no match")
    assert len(caplog.records) == 1
    assert caplog.records[0].levelno == logging.WARNING


# ---------------------------------------------------------------------------
# log_delivery_attempt
# ---------------------------------------------------------------------------

def test_log_delivery_attempt_success(caplog):
    with caplog.at_level(logging.INFO, logger="hookpipe"):
        log_delivery_attempt(
            destination="https://example.com/hook",
            attempt=1,
            status_code=200,
            duration_ms=15.5,
        )
    assert len(caplog.records) == 1
    data = json.loads(caplog.records[0].getMessage())
    assert data["status"] == "200"
    assert data["attempt"] == 1
    assert caplog.records[0].levelno == logging.INFO


def test_log_delivery_attempt_failure_uses_warning(caplog):
    with caplog.at_level(logging.WARNING, logger="hookpipe"):
        log_delivery_attempt(
            destination="https://example.com/hook",
            attempt=2,
            status_code=500,
        )
    assert len(caplog.records) == 1
    assert caplog.records[0].levelno == logging.WARNING


def test_log_delivery_attempt_network_error(caplog):
    with caplog.at_level(logging.WARNING, logger="hookpipe"):
        log_delivery_attempt(
            destination="https://example.com/hook",
            attempt=1,
            error="ConnectionError",
        )
    data = json.loads(caplog.records[0].getMessage())
    assert data["error"] == "ConnectionError"
    assert data["status"] == "error"
