"""Tests for hookpipe.webhook_validator."""

import pytest
from hookpipe.webhook_validator import validate_payload, ValidationError


def test_valid_payload_passes():
    schema = {"required": ["event"], "types": {"event": "string"}}
    validate_payload({"event": "push"}, schema)


def test_missing_required_field_raises():
    schema = {"required": ["event"]}
    with pytest.raises(ValidationError, match="Missing required field: 'event'"):
        validate_payload({"other": 1}, schema)


def test_missing_nested_required_field_raises():
    schema = {"required": ["repo.name"]}
    with pytest.raises(ValidationError, match="repo.name"):
        validate_payload({"repo": {}}, schema)


def test_nested_required_field_present_passes():
    schema = {"required": ["repo.name"]}
    validate_payload({"repo": {"name": "hookpipe"}}, schema)


def test_wrong_type_raises():
    schema = {"types": {"count": "number"}}
    with pytest.raises(ValidationError, match="expected type 'number'"):
        validate_payload({"count": "five"}, schema)


def test_correct_type_passes():
    schema = {"types": {"count": "number"}}
    validate_payload({"count": 5}, schema)


def test_boolean_type_check():
    schema = {"types": {"active": "boolean"}}
    validate_payload({"active": True}, schema)


def test_boolean_not_confused_with_number():
    schema = {"types": {"active": "boolean"}}
    with pytest.raises(ValidationError, match="expected type 'boolean'"):
        validate_payload({"active": 1}, schema)


def test_null_type_check():
    schema = {"types": {"ref": "null"}}
    validate_payload({"ref": None}, schema)


def test_type_check_skips_absent_field():
    schema = {"types": {"optional_field": "string"}}
    validate_payload({}, schema)  # should not raise


def test_allowed_values_pass():
    schema = {"allowed_values": {"status": ["open", "closed"]}}
    validate_payload({"status": "open"}, schema)


def test_allowed_values_fail_raises():
    schema = {"allowed_values": {"status": ["open", "closed"]}}
    with pytest.raises(ValidationError, match="not in allowed values"):
        validate_payload({"status": "pending"}, schema)


def test_allowed_values_skips_absent_field():
    schema = {"allowed_values": {"status": ["open", "closed"]}}
    validate_payload({}, schema)  # should not raise


def test_non_dict_payload_raises():
    with pytest.raises(ValidationError, match="JSON object"):
        validate_payload(["not", "a", "dict"], {})


def test_unsupported_type_constraint_raises():
    schema = {"types": {"field": "integer"}}
    with pytest.raises(ValidationError, match="Unsupported type constraint"):
        validate_payload({"field": 1}, schema)


def test_empty_schema_always_passes():
    validate_payload({"anything": True}, {})
