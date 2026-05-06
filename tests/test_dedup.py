"""Tests for hookpipe.dedup."""

import pytest

import hookpipe.dedup as dedup
from hookpipe.dedup import DedupError, compute_event_id, is_duplicate, reset


@pytest.fixture(autouse=True)
def clean_state():
    reset()
    yield
    reset()


# ---------------------------------------------------------------------------
# compute_event_id
# ---------------------------------------------------------------------------

def test_compute_event_id_hash_is_stable():
    payload = {"action": "push", "ref": "main"}
    assert compute_event_id(payload) == compute_event_id(payload)


def test_compute_event_id_different_payloads_differ():
    a = {"x": 1}
    b = {"x": 2}
    assert compute_event_id(a) != compute_event_id(b)


def test_compute_event_id_uses_id_field():
    payload = {"id": "abc123", "data": "ignored"}
    assert compute_event_id(payload, id_field="id") == "abc123"


def test_compute_event_id_nested_id_field():
    payload = {"event": {"id": "nested-id"}}
    assert compute_event_id(payload, id_field="event.id") == "nested-id"


def test_compute_event_id_missing_id_field_raises():
    with pytest.raises(DedupError, match="id_field"):
        compute_event_id({"other": 1}, id_field="missing")


# ---------------------------------------------------------------------------
# is_duplicate
# ---------------------------------------------------------------------------

def test_first_occurrence_not_duplicate():
    assert is_duplicate({"id": "1"}, id_field="id") is False


def test_second_occurrence_is_duplicate():
    payload = {"id": "42"}
    is_duplicate(payload, id_field="id")
    assert is_duplicate(payload, id_field="id") is True


def test_different_payloads_not_duplicate():
    is_duplicate({"id": "a"}, id_field="id")
    assert is_duplicate({"id": "b"}, id_field="id") is False


def test_hash_based_dedup_works():
    payload = {"action": "open", "number": 7}
    assert is_duplicate(payload) is False
    assert is_duplicate(payload) is True


def test_zero_ttl_raises():
    with pytest.raises(DedupError, match="ttl"):
        is_duplicate({"id": "x"}, ttl=0)


def test_negative_ttl_raises():
    with pytest.raises(DedupError, match="ttl"):
        is_duplicate({"id": "x"}, ttl=-5)


def test_expired_entry_not_duplicate(monkeypatch):
    """After TTL elapses the same payload should be accepted again."""
    base = 1000.0
    monkeypatch.setattr(dedup, "_now", lambda: base)
    is_duplicate({"id": "exp"}, id_field="id", ttl=10)

    # Advance time beyond TTL
    monkeypatch.setattr(dedup, "_now", lambda: base + 11)
    assert is_duplicate({"id": "exp"}, id_field="id", ttl=10) is False


def test_reset_clears_state():
    is_duplicate({"id": "z"}, id_field="id")
    reset()
    assert is_duplicate({"id": "z"}, id_field="id") is False
