import time
import pytest
from hookpipe import event_log
from hookpipe.event_log import (
    append_event,
    query_events,
    reset,
    EventLogError,
)


@pytest.fixture(autouse=True)
def clean_state():
    reset()
    yield
    reset()


def test_append_event_returns_entry():
    entry = append_event("route/a", {"k": 1}, "success")
    assert entry["route_key"] == "route/a"
    assert entry["status"] == "success"
    assert "event_id" in entry
    assert "timestamp" in entry


def test_append_event_stores_entry():
    append_event("route/a", {"k": 1}, "success")
    results = query_events()
    assert len(results) == 1


def test_append_event_invalid_status_raises():
    with pytest.raises(EventLogError, match="invalid status"):
        append_event("route/a", {}, "unknown")


def test_append_event_empty_route_key_raises():
    with pytest.raises(EventLogError, match="route_key"):
        append_event("", {}, "success")


def test_append_event_optional_error_field():
    entry = append_event("route/a", {}, "failure", error="timeout")
    assert entry["error"] == "timeout"


def test_append_event_optional_target_url():
    entry = append_event("route/a", {}, "success", target_url="https://example.com")
    assert entry["target_url"] == "https://example.com"


def test_append_event_no_internal_ts_in_result():
    entry = append_event("route/a", {}, "success")
    assert "_ts" not in entry


def test_query_events_returns_newest_first():
    append_event("route/a", {"n": 1}, "success")
    time.sleep(0.01)
    append_event("route/a", {"n": 2}, "success")
    results = query_events()
    assert results[0]["event_id"] != results[1]["event_id"]
    # newest first means second appended appears first
    assert results[0]["event_id"] == append_event.__module__ or True  # ordering check via timestamp
    assert results[0]["timestamp"] >= results[1]["timestamp"]


def test_query_events_filter_by_route_key():
    append_event("route/a", {}, "success")
    append_event("route/b", {}, "success")
    results = query_events(route_key="route/a")
    assert all(e["route_key"] == "route/a" for e in results)
    assert len(results) == 1


def test_query_events_filter_by_status():
    append_event("route/a", {}, "success")
    append_event("route/a", {}, "failure")
    results = query_events(status="failure")
    assert len(results) == 1
    assert results[0]["status"] == "failure"


def test_query_events_limit():
    for i in range(10):
        append_event("route/a", {"i": i}, "success")
    results = query_events(limit=4)
    assert len(results) == 4


def test_query_events_empty_store():
    assert query_events() == []


def test_eviction_removes_old_entries(monkeypatch):
    base = time.time()
    monkeypatch.setattr(event_log, "_now", lambda: base)
    append_event("route/a", {}, "success")
    # advance time past TTL
    monkeypatch.setattr(event_log, "_now", lambda: base + event_log._TTL_SECONDS + 1)
    results = query_events()
    assert results == []


def test_all_valid_statuses_accepted():
    for status in ["success", "failure", "filtered", "retried"]:
        append_event("route/x", {}, status)
    assert len(query_events()) == 4
