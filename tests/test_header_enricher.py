"""Tests for hookpipe.header_enricher."""

import pytest

from hookpipe.header_enricher import (
    HeaderEnricherError,
    build_enricher,
)


# ---------------------------------------------------------------------------
# build_enricher — validation
# ---------------------------------------------------------------------------

def test_empty_config_produces_enricher():
    enrich = build_enricher()
    result = enrich({}, {})
    assert result == {}


def test_reserved_static_header_raises():
    with pytest.raises(HeaderEnricherError, match="reserved"):
        build_enricher(static_headers={"Content-Length": "0"})


def test_reserved_dynamic_header_raises():
    with pytest.raises(HeaderEnricherError, match="reserved"):
        build_enricher(dynamic_headers={"host": lambda p: "example.com"})


def test_empty_static_key_raises():
    with pytest.raises(HeaderEnricherError, match="empty"):
        build_enricher(static_headers={"": "value"})


def test_non_string_static_value_raises():
    with pytest.raises(HeaderEnricherError, match="string"):
        build_enricher(static_headers={"X-Version": 42})  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# enrich — static headers
# ---------------------------------------------------------------------------

def test_static_header_added():
    enrich = build_enricher(static_headers={"X-Source": "hookpipe"})
    result = enrich({"event": "push"}, {})
    assert result["X-Source"] == "hookpipe"


def test_static_header_overwrites_existing():
    enrich = build_enricher(static_headers={"X-Source": "hookpipe"})
    result = enrich({}, {"X-Source": "old-value"})
    assert result["X-Source"] == "hookpipe"


def test_existing_headers_preserved():
    enrich = build_enricher(static_headers={"X-New": "yes"})
    result = enrich({}, {"Authorization": "Bearer token"})
    assert result["Authorization"] == "Bearer token"
    assert result["X-New"] == "yes"


# ---------------------------------------------------------------------------
# enrich — dynamic headers
# ---------------------------------------------------------------------------

def test_dynamic_header_receives_payload():
    enrich = build_enricher(
        dynamic_headers={"X-Event-Type": lambda p: p.get("type", "unknown")}
    )
    result = enrich({"type": "push"}, {})
    assert result["X-Event-Type"] == "push"


def test_dynamic_header_fallback_when_key_missing():
    enrich = build_enricher(
        dynamic_headers={"X-Event-Type": lambda p: p.get("type", "unknown")}
    )
    result = enrich({}, {})
    assert result["X-Event-Type"] == "unknown"


def test_dynamic_header_overwrites_static_for_same_key():
    enrich = build_enricher(
        static_headers={"X-Trace": "static"},
        dynamic_headers={"X-Trace": lambda p: "dynamic-" + p.get("id", "0")},
    )
    result = enrich({"id": "99"}, {})
    # dynamic is applied after static, so dynamic wins
    assert result["X-Trace"] == "dynamic-99"


# ---------------------------------------------------------------------------
# enrich — no mutation of input
# ---------------------------------------------------------------------------

def test_existing_headers_dict_not_mutated():
    enrich = build_enricher(static_headers={"X-Added": "1"})
    original = {"X-Keep": "yes"}
    enrich({}, original)
    assert "X-Added" not in original
