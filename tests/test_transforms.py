"""Tests for hookpipe/transforms.py"""

import pytest
from hookpipe.transforms import apply_transforms, TransformError


SAMPLE = {
    "event": "push",
    "repo": {"name": "hookpipe", "private": False},
    "sender": {"login": "alice", "id": 42},
}


def test_set_top_level():
    result = apply_transforms(SAMPLE, [{"op": "set", "field": "source", "value": "github"}])
    assert result["source"] == "github"
    assert "source" not in SAMPLE  # original unchanged


def test_set_nested():
    result = apply_transforms(SAMPLE, [{"op": "set", "field": "repo.stars", "value": 99}])
    assert result["repo"]["stars"] == 99


def test_copy_field():
    result = apply_transforms(SAMPLE, [{"op": "copy", "from": "repo.name", "to": "project"}])
    assert result["project"] == "hookpipe"
    assert result["repo"]["name"] == "hookpipe"  # original still present


def test_delete_top_level():
    result = apply_transforms(SAMPLE, [{"op": "delete", "field": "event"}])
    assert "event" not in result


def test_delete_nested():
    result = apply_transforms(SAMPLE, [{"op": "delete", "field": "repo.private"}])
    assert "private" not in result["repo"]
    assert "name" in result["repo"]


def test_rename_field():
    result = apply_transforms(SAMPLE, [{"op": "rename", "from": "event", "to": "action"}])
    assert result["action"] == "push"
    assert "event" not in result


def test_rename_nested():
    result = apply_transforms(
        SAMPLE, [{"op": "rename", "from": "sender.login", "to": "sender.username"}]
    )
    assert result["sender"]["username"] == "alice"
    assert "login" not in result["sender"]


def test_regex_substitution():
    result = apply_transforms(
        SAMPLE,
        [{"op": "regex", "field": "event", "pattern": r"push", "replacement": "PUSH"}],
    )
    assert result["event"] == "PUSH"


def test_regex_non_string_raises():
    with pytest.raises(TransformError, match="string field"):
        apply_transforms(
            SAMPLE,
            [{"op": "regex", "field": "sender.id", "pattern": r"\d+", "replacement": "0"}],
        )


def test_unknown_op_raises():
    with pytest.raises(TransformError, match="Unknown transform operation"):
        apply_transforms(SAMPLE, [{"op": "explode", "field": "event"}])


def test_copy_missing_key_raises():
    with pytest.raises(TransformError):
        apply_transforms(SAMPLE, [{"op": "copy", "from": "repo.missing", "to": "x"}])


def test_multiple_transforms_applied_in_order():
    rules = [
        {"op": "set", "field": "env", "value": "prod"},
        {"op": "copy", "from": "env", "to": "meta.environment"},
        {"op": "delete", "field": "env"},
    ]
    result = apply_transforms(SAMPLE, rules)
    assert result["meta"]["environment"] == "prod"
    assert "env" not in result


def test_original_payload_not_mutated():
    original = {"a": {"b": 1}}
    apply_transforms(original, [{"op": "set", "field": "a.b", "value": 999}])
    assert original["a"]["b"] == 1
