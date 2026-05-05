"""Unit tests for hookpipe.filters."""

import pytest

from hookpipe.filters import apply_filters, FilterError


SAMPLE_PAYLOAD = {
    "action": "opened",
    "repository": {
        "name": "hookpipe",
        "private": False,
    },
    "sender": {"login": "alice"},
}


def test_eq_match():
    rules = [{"field": "action", "op": "eq", "value": "opened"}]
    assert apply_filters(SAMPLE_PAYLOAD, rules) is True


def test_eq_no_match():
    rules = [{"field": "action", "op": "eq", "value": "closed"}]
    assert apply_filters(SAMPLE_PAYLOAD, rules) is False


def test_neq_match():
    rules = [{"field": "action", "op": "neq", "value": "closed"}]
    assert apply_filters(SAMPLE_PAYLOAD, rules) is True


def test_neq_no_match():
    rules = [{"field": "action", "op": "neq", "value": "opened"}]
    assert apply_filters(SAMPLE_PAYLOAD, rules) is False


def test_contains_match():
    rules = [{"field": "repository.name", "op": "contains", "value": "hook"}]
    assert apply_filters(SAMPLE_PAYLOAD, rules) is True


def test_contains_no_match():
    rules = [{"field": "repository.name", "op": "contains", "value": "xyz"}]
    assert apply_filters(SAMPLE_PAYLOAD, rules) is False


def test_exists_present():
    rules = [{"field": "sender.login", "op": "exists"}]
    assert apply_filters(SAMPLE_PAYLOAD, rules) is True


def test_exists_missing():
    rules = [{"field": "sender.email", "op": "exists"}]
    assert apply_filters(SAMPLE_PAYLOAD, rules) is False


def test_multiple_rules_all_pass():
    rules = [
        {"field": "action", "op": "eq", "value": "opened"},
        {"field": "repository.private", "op": "eq", "value": False},
    ]
    assert apply_filters(SAMPLE_PAYLOAD, rules) is True


def test_multiple_rules_one_fails():
    rules = [
        {"field": "action", "op": "eq", "value": "opened"},
        {"field": "repository.private", "op": "eq", "value": True},
    ]
    assert apply_filters(SAMPLE_PAYLOAD, rules) is False


def test_empty_rules_always_pass():
    assert apply_filters(SAMPLE_PAYLOAD, []) is True


def test_unknown_op_raises():
    with pytest.raises(FilterError, match="Unknown filter operator"):
        apply_filters(SAMPLE_PAYLOAD, [{"field": "action", "op": "regex", "value": ".*"}])


def test_missing_field_raises():
    with pytest.raises(FilterError, match="Invalid filter rule"):
        apply_filters(SAMPLE_PAYLOAD, [{"op": "eq", "value": "opened"}])
