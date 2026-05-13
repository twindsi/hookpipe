"""Webhook payload schema validation using simple rule-based checks."""

from typing import Any


class ValidationError(Exception):
    """Raised when a payload fails schema validation."""


_SUPPORTED_TYPES = {"string", "number", "boolean", "object", "array", "null"}


def _json_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    return "unknown"


def _get_nested(payload: dict, key: str) -> Any:
    parts = key.split(".")
    node = payload
    for part in parts:
        if not isinstance(node, dict) or part not in node:
            raise KeyError(key)
        node = node[part]
    return node


def validate_payload(payload: dict, schema: dict) -> None:
    """Validate *payload* against *schema*.

    Schema format::

        {
            "required": ["field", "nested.field"],
            "types": {"field": "string", "count": "number"},
            "allowed_values": {"status": ["open", "closed"]}
        }

    Raises ValidationError on the first violation found.
    """
    if not isinstance(payload, dict):
        raise ValidationError("Payload must be a JSON object")

    for field in schema.get("required", []):
        try:
            _get_nested(payload, field)
        except KeyError:
            raise ValidationError(f"Missing required field: '{field}'")

    for field, expected_type in schema.get("types", {}).items():
        if expected_type not in _SUPPORTED_TYPES:
            raise ValidationError(f"Unsupported type constraint '{expected_type}' for field '{field}'")
        try:
            value = _get_nested(payload, field)
        except KeyError:
            continue
        actual = _json_type(value)
        if actual != expected_type:
            raise ValidationError(
                f"Field '{field}' expected type '{expected_type}', got '{actual}'"
            )

    for field, allowed in schema.get("allowed_values", {}).items():
        try:
            value = _get_nested(payload, field)
        except KeyError:
            continue
        if value not in allowed:
            raise ValidationError(
                f"Field '{field}' value {value!r} not in allowed values {allowed}"
            )
