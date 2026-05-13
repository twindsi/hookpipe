"""Tests for hookpipe.validation_middleware."""

import pytest
from hookpipe.validation_middleware import with_validation
from hookpipe.webhook_validator import ValidationError


def test_returns_callable():
    step = with_validation({})
    assert callable(step)


def test_valid_payload_returned_unchanged():
    schema = {"required": ["event"], "types": {"event": "string"}}
    step = with_validation(schema)
    payload = {"event": "push", "extra": 42}
    result = step(payload)
    assert result == payload


def test_invalid_payload_raises_validation_error():
    schema = {"required": ["event"]}
    step = with_validation(schema)
    with pytest.raises(ValidationError):
        step({"no_event": True})


def test_wrong_type_raises():
    schema = {"types": {"count": "number"}}
    step = with_validation(schema)
    with pytest.raises(ValidationError):
        step({"count": "not-a-number"})


def test_multiple_schemas_are_independent():
    step_a = with_validation({"required": ["a"]})
    step_b = with_validation({"required": ["b"]})
    step_a({"a": 1})  # ok
    step_b({"b": 2})  # ok
    with pytest.raises(ValidationError):
        step_a({"b": 2})  # missing 'a'


def test_function_name_is_set():
    step = with_validation({})
    assert step.__name__ == "with_validation"
