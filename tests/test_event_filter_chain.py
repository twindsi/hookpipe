"""Tests for hookpipe/event_filter_chain.py."""

import pytest
from hookpipe.event_filter_chain import (
    FilterChainError,
    build_chain,
    run_filter_chain,
)


# ---------------------------------------------------------------------------
# build_chain
# ---------------------------------------------------------------------------

def test_build_chain_returns_normalised_steps():
    steps = [{"name": "check_event", "filters": [{"field": "type", "op": "eq", "value": "push"}]}]
    chain = build_chain(steps)
    assert len(chain) == 1
    assert chain[0]["name"] == "check_event"
    assert chain[0]["stop_on_match"] is False
    assert chain[0]["optional"] is False


def test_build_chain_non_list_raises():
    with pytest.raises(FilterChainError, match="steps must be a list"):
        build_chain("not a list")


def test_build_chain_step_not_dict_raises():
    with pytest.raises(FilterChainError, match="must be a dict"):
        build_chain(["bad"])


def test_build_chain_missing_name_raises():
    with pytest.raises(FilterChainError, match="must have a 'name' field"):
        build_chain([{"filters": []}])


def test_build_chain_empty_name_raises():
    with pytest.raises(FilterChainError, match="non-empty string"):
        build_chain([{"name": "  ", "filters": []}])


def test_build_chain_missing_filters_raises():
    with pytest.raises(FilterChainError, match="must have a 'filters' field"):
        build_chain([{"name": "s1"}])


def test_build_chain_filters_not_list_raises():
    with pytest.raises(FilterChainError, match="filters must be a list"):
        build_chain([{"name": "s1", "filters": {}}])


def test_build_chain_duplicate_names_raises():
    steps = [
        {"name": "dup", "filters": []},
        {"name": "dup", "filters": []},
    ]
    with pytest.raises(FilterChainError, match="Duplicate step names"):
        build_chain(steps)


def test_build_chain_stop_on_match_and_optional_flags():
    steps = [{"name": "s", "filters": [], "stop_on_match": True, "optional": True}]
    chain = build_chain(steps)
    assert chain[0]["stop_on_match"] is True
    assert chain[0]["optional"] is True


# ---------------------------------------------------------------------------
# run_filter_chain
# ---------------------------------------------------------------------------

_PAYLOAD = {"type": "push", "repo": "acme/core", "ref": "refs/heads/main"}


def test_all_steps_match_returns_all_names():
    steps = build_chain([
        {"name": "type_check", "filters": [{"field": "type", "op": "eq", "value": "push"}]},
        {"name": "ref_check", "filters": [{"field": "ref", "op": "contains", "value": "main"}]},
    ])
    matched = run_filter_chain(_PAYLOAD, steps)
    assert matched == ["type_check", "ref_check"]


def test_required_step_mismatch_raises():
    steps = build_chain([
        {"name": "type_check", "filters": [{"field": "type", "op": "eq", "value": "pr"}]},
    ])
    with pytest.raises(FilterChainError, match="type_check"):
        run_filter_chain(_PAYLOAD, steps)


def test_optional_step_mismatch_skipped():
    steps = build_chain([
        {"name": "optional_step", "filters": [{"field": "type", "op": "eq", "value": "pr"}], "optional": True},
        {"name": "ref_check", "filters": [{"field": "ref", "op": "contains", "value": "main"}]},
    ])
    matched = run_filter_chain(_PAYLOAD, steps)
    assert matched == ["ref_check"]


def test_stop_on_match_halts_chain():
    steps = build_chain([
        {"name": "first", "filters": [{"field": "type", "op": "eq", "value": "push"}], "stop_on_match": True},
        {"name": "second", "filters": [{"field": "ref", "op": "contains", "value": "main"}]},
    ])
    matched = run_filter_chain(_PAYLOAD, steps)
    assert matched == ["first"]


def test_raise_on_mismatch_false_returns_partial():
    steps = build_chain([
        {"name": "fail_step", "filters": [{"field": "type", "op": "eq", "value": "pr"}]},
        {"name": "pass_step", "filters": [{"field": "ref", "op": "contains", "value": "main"}]},
    ])
    matched = run_filter_chain(_PAYLOAD, steps, raise_on_mismatch=False)
    assert matched == ["pass_step"]


def test_empty_steps_returns_empty_list():
    assert run_filter_chain(_PAYLOAD, []) == []


def test_empty_filters_in_step_always_matches():
    steps = build_chain([{"name": "catch_all", "filters": []}])
    matched = run_filter_chain(_PAYLOAD, steps)
    assert matched == ["catch_all"]
