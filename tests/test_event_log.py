"""Tests for hookpipe.event_log and hookpipe.event_log_handler."""

import json
from io import BytesIO
from unittest.mock import MagicMock

import pytest

from hookpipe import event_log as el
from hookpipe.event_log import EventLogError, append_event, query_events, reset
from hookpipe.event_log_handler import EventLogHandler


@pytest.fixture(autouse=True)
def clean_state():
    reset()
    yield
    reset()


# --- append_event ---

def test_append_event_returns_entry():
    entry = append_event("github", {"ref": "main"}, "success", target_url="http://x")
    assert entry["route_key"] == "github"
    assert entry["status"] == "success"
    assert entry["target_url"] == "http://x"


def test_append_event_stores_entry():
    append_event("stripe", {"type": "charge"}, "failure", error="timeout")
    results = query_events()
    assert len(results) == 1
    assert results[0]["error"] == "timeout"


def test_append_event_invalid_status_raises():
    with pytest.raises(EventLogError, match="Invalid status"):
        append_event("r", {}, "unknown")


def test_append_event_empty_route_key_raises():
    with pytest.raises(EventLogError, match="route_key"):
        append_event("", {}, "success")


def test_append_event_no_optional_fields():
    entry = append_event("r", {}, "filtered")
    assert "target_url" not in entry
    assert "error" not in entry


# --- query_events ---

def test_query_events_filter_by_route_key():
    append_event("a", {}, "success")
    append_event("b", {}, "success")
    results = query_events(route_key="a")
    assert all(e["route_key"] == "a" for e in results)
    assert len(results) == 1


def test_query_events_filter_by_status():
    append_event("r", {}, "success")
    append_event("r", {}, "failure")
    results = query_events(status="failure")
    assert len(results) == 1
    assert results[0]["status"] == "failure"


def test_query_events_limit():
    for i in range(10):
        append_event("r", {"i": i}, "success")
    results = query_events(limit=3)
    assert len(results) == 3


def test_query_events_returns_most_recent_when_limited():
    for i in range(5):
        append_event("r", {"i": i}, "success")
    results = query_events(limit=2)
    assert results[-1]["payload"]["i"] == 4


# --- EventLogHandler ---

def _make_handler(path="/events"):
    handler = EventLogHandler.__new__(EventLogHandler)
    handler.path = path
    handler.wfile = BytesIO()
    handler.send_response = MagicMock()
    handler.send_header = MagicMock()
    handler.end_headers = MagicMock()
    return handler


def test_handler_returns_200():
    h = _make_handler()
    h.do_GET()
    h.send_response.assert_called_once_with(200)


def test_handler_returns_events():
    append_event("r", {"x": 1}, "success")
    h = _make_handler()
    h.do_GET()
    h.wfile.seek(0)
    body = json.loads(h.wfile.read())
    assert body["count"] == 1
    assert body["events"][0]["route_key"] == "r"


def test_handler_404_for_unknown_path():
    h = _make_handler("/unknown")
    h.do_GET()
    h.send_response.assert_called_once_with(404)


def test_handler_filters_by_query_param():
    append_event("a", {}, "success")
    append_event("b", {}, "success")
    h = _make_handler("/events?route_key=a")
    h.do_GET()
    h.wfile.seek(0)
    body = json.loads(h.wfile.read())
    assert body["count"] == 1


def test_handler_strips_internal_ts():
    append_event("r", {}, "success")
    h = _make_handler()
    h.do_GET()
    h.wfile.seek(0)
    body = json.loads(h.wfile.read())
    assert "_ts" not in body["events"][0]
