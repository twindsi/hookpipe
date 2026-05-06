"""Tests for hookpipe.metrics."""

import pytest
from hookpipe import metrics
from hookpipe.metrics import MetricsError, increment, record_timing, snapshot, reset


@pytest.fixture(autouse=True)
def clean_metrics():
    reset()
    yield
    reset()


def test_increment_known_counter():
    increment("requests_received")
    data = snapshot()
    assert data["counters"]["requests_received"] == 1


def test_increment_by_amount():
    increment("deliveries_attempted", 5)
    data = snapshot()
    assert data["counters"]["deliveries_attempted"] == 5


def test_increment_accumulates():
    increment("retries_total")
    increment("retries_total")
    increment("retries_total")
    data = snapshot()
    assert data["counters"]["retries_total"] == 3


def test_increment_unknown_counter_raises():
    with pytest.raises(MetricsError, match="Unknown counter"):
        increment("nonexistent_counter")


def test_record_timing_stores_sample():
    record_timing("delivery_duration_seconds", 0.42)
    data = snapshot()
    t = data["timings"]["delivery_duration_seconds"]
    assert t["count"] == 1
    assert abs(t["sum"] - 0.42) < 1e-6


def test_record_timing_aggregates_multiple():
    record_timing("delivery_duration_seconds", 0.1)
    record_timing("delivery_duration_seconds", 0.3)
    data = snapshot()
    t = data["timings"]["delivery_duration_seconds"]
    assert t["count"] == 2
    assert abs(t["min"] - 0.1) < 1e-6
    assert abs(t["max"] - 0.3) < 1e-6
    assert abs(t["avg"] - 0.2) < 1e-6


def test_record_timing_unknown_metric_raises():
    with pytest.raises(MetricsError, match="Unknown timing metric"):
        record_timing("unknown_timing", 1.0)


def test_snapshot_empty_timing():
    data = snapshot()
    t = data["timings"]["delivery_duration_seconds"]
    assert t["count"] == 0
    assert t["min"] is None
    assert t["max"] is None
    assert t["avg"] is None


def test_snapshot_contains_uptime():
    data = snapshot()
    assert "uptime_seconds" in data
    assert data["uptime_seconds"] >= 0.0


def test_reset_clears_counters():
    increment("deliveries_succeeded", 10)
    reset()
    data = snapshot()
    assert data["counters"]["deliveries_succeeded"] == 0


def test_reset_clears_timings():
    record_timing("delivery_duration_seconds", 1.5)
    reset()
    data = snapshot()
    assert data["timings"]["delivery_duration_seconds"]["count"] == 0
