"""Tests for hookpipe/replay.py"""

import pytest
from hookpipe import replay
from hookpipe.replay import ReplayError


@pytest.fixture(autouse=True)
def clean_state():
    replay.reset()
    yield
    replay.reset()


def test_store_event_returns_key():
    key = replay.store_event({"x": 1}, "route-a")
    assert isinstance(key, str) and len(key) == 64


def test_store_event_same_payload_same_key():
    k1 = replay.store_event({"x": 1}, "route-a")
    k2 = replay.store_event({"x": 1}, "route-a")
    assert k1 == k2


def test_store_event_different_payload_different_key():
    k1 = replay.store_event({"x": 1}, "route-a")
    k2 = replay.store_event({"x": 2}, "route-a")
    assert k1 != k2


def test_store_event_invalid_payload_raises():
    with pytest.raises(ReplayError, match="payload must be a dict"):
        replay.store_event(["not", "a", "dict"], "route-a")


def test_store_event_empty_route_key_raises():
    with pytest.raises(ReplayError, match="route_key must not be empty"):
        replay.store_event({"x": 1}, "")


def test_get_events_returns_all():
    replay.store_event({"a": 1}, "r1")
    replay.store_event({"b": 2}, "r2")
    events = replay.get_events()
    assert len(events) == 2


def test_get_events_filtered_by_route_key():
    replay.store_event({"a": 1}, "r1")
    replay.store_event({"b": 2}, "r2")
    replay.store_event({"c": 3}, "r1")
    events = replay.get_events(route_key="r1")
    assert len(events) == 2
    assert all(e["route_key"] == "r1" for e in events)


def test_get_events_no_match_returns_empty():
    replay.store_event({"a": 1}, "r1")
    events = replay.get_events(route_key="nonexistent")
    assert events == []


def test_get_event_by_key_found():
    key = replay.store_event({"z": 99}, "route-z")
    event = replay.get_event_by_key(key)
    assert event is not None
    assert event["payload"] == {"z": 99}
    assert event["route_key"] == "route-z"


def test_get_event_by_key_not_found():
    result = replay.get_event_by_key("0" * 64)
    assert result is None


def test_buffer_caps_at_max_size():
    original_max = replay._max_size
    replay._max_size = 5
    for i in range(10):
        replay.store_event({"i": i}, "route-x")
    events = replay.get_events()
    assert len(events) == 5
    replay._max_size = original_max


def test_event_record_has_expected_fields():
    replay.store_event({"msg": "hello"}, "my-route")
    events = replay.get_events()
    assert len(events) == 1
    e = events[0]
    assert "key" in e
    assert "route_key" in e
    assert "payload" in e
