"""Payload transformation rules for hookpipe."""

import re
from typing import Any


class TransformError(Exception):
    """Raised when a transformation cannot be applied."""


def _set_nested(payload: dict, key_path: str, value: Any) -> None:
    """Set a value in a nested dict using dot-notation key path."""
    keys = key_path.split(".")
    target = payload
    for key in keys[:-1]:
        if key not in target or not isinstance(target[key], dict):
            target[key] = {}
        target = target[key]
    target[keys[-1]] = value


def _get_nested(payload: dict, key_path: str) -> Any:
    """Get a value from a nested dict using dot-notation key path."""
    keys = key_path.split(".")
    target = payload
    for key in keys:
        if not isinstance(target, dict) or key not in target:
            raise TransformError(f"Key path '{key_path}' not found in payload")
        target = target[key]
    return target


def apply_transforms(payload: dict, transforms: list[dict]) -> dict:
    """Apply a list of transform rules to a payload copy.

    Supported operations:
      - set:    set field to a static value
      - copy:   copy value from one field to another
      - delete: remove a field
      - rename: rename a field (move)
      - regex:  apply regex substitution on a string field
    """
    import copy
    result = copy.deepcopy(payload)

    for rule in transforms:
        op = rule.get("op")
        if op == "set":
            _set_nested(result, rule["field"], rule["value"])

        elif op == "copy":
            value = _get_nested(result, rule["from"])
            _set_nested(result, rule["to"], value)

        elif op == "delete":
            keys = rule["field"].split(".")
            target = result
            for key in keys[:-1]:
                if not isinstance(target, dict) or key not in target:
                    raise TransformError(f"Key path '{rule['field']}' not found")
                target = target[key]
            target.pop(keys[-1], None)

        elif op == "rename":
            value = _get_nested(result, rule["from"])
            _set_nested(result, rule["to"], value)
            keys = rule["from"].split(".")
            target = result
            for key in keys[:-1]:
                target = target[key]
            target.pop(keys[-1], None)

        elif op == "regex":
            value = _get_nested(result, rule["field"])
            if not isinstance(value, str):
                raise TransformError(
                    f"regex op requires a string field, got {type(value).__name__}"
                )
            new_value = re.sub(rule["pattern"], rule["replacement"], value)
            _set_nested(result, rule["field"], new_value)

        else:
            raise TransformError(f"Unknown transform operation: '{op}'")

    return result
