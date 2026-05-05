"""Payload filtering rules for hookpipe.

Filters determine whether an incoming webhook payload should be
forwarded based on configurable conditions.
"""

from __future__ import annotations

from typing import Any


class FilterError(Exception):
    """Raised when a filter rule is misconfigured."""


def _get_nested(data: dict, key_path: str) -> Any:
    """Retrieve a value from a nested dict using dot-notation key path."""
    keys = key_path.split(".")
    current = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def apply_filters(payload: dict, rules: list[dict]) -> bool:
    """Return True if the payload passes all filter rules.

    Each rule is a dict with:
      - field  (str):  dot-notation path into the payload
      - op     (str):  one of 'eq', 'neq', 'contains', 'exists'
      - value  (Any):  expected value (not required for 'exists')

    All rules are AND-ed together.
    """
    for rule in rules:
        field = rule.get("field")
        op = rule.get("op")
        expected = rule.get("value")

        if not field or not op:
            raise FilterError(f"Invalid filter rule (missing 'field' or 'op'): {rule}")

        actual = _get_nested(payload, field)

        if op == "eq":
            if actual != expected:
                return False
        elif op == "neq":
            if actual == expected:
                return False
        elif op == "contains":
            if not isinstance(actual, str) or expected not in actual:
                return False
        elif op == "exists":
            if actual is None:
                return False
        else:
            raise FilterError(f"Unknown filter operator: '{op}'")

    return True
