"""event_filter_chain.py — Composable chain of named filter steps applied to a payload.

Each step in the chain has a name, a set of filter rules, and an optional
`stop_on_match` flag that halts further processing when the step matches.
"""

from typing import Any, Dict, List, Optional
from hookpipe.filters import apply_filters, FilterError


class FilterChainError(Exception):
    """Raised when the filter chain cannot be built or executed."""


def _validate_step(step: Any) -> None:
    if not isinstance(step, dict):
        raise FilterChainError(f"Each chain step must be a dict, got {type(step).__name__}")
    if "name" not in step:
        raise FilterChainError("Each chain step must have a 'name' field")
    if not isinstance(step["name"], str) or not step["name"].strip():
        raise FilterChainError("Step 'name' must be a non-empty string")
    if "filters" not in step:
        raise FilterChainError(f"Step '{step['name']}' must have a 'filters' field")
    if not isinstance(step["filters"], list):
        raise FilterChainError(f"Step '{step['name']}' filters must be a list")


def build_chain(steps: List[Dict]) -> List[Dict]:
    """Validate and return a normalised list of chain steps."""
    if not isinstance(steps, list):
        raise FilterChainError("steps must be a list")
    for step in steps:
        _validate_step(step)
    names = [s["name"] for s in steps]
    if len(names) != len(set(names)):
        raise FilterChainError("Duplicate step names are not allowed in a filter chain")
    return [
        {
            "name": s["name"],
            "filters": s["filters"],
            "stop_on_match": bool(s.get("stop_on_match", False)),
            "optional": bool(s.get("optional", False)),
        }
        for s in steps
    ]


def run_filter_chain(
    payload: Dict,
    steps: List[Dict],
    *,
    raise_on_mismatch: bool = True,
) -> List[str]:
    """Run *payload* through each step in *steps*.

    Returns a list of names of steps that matched.
    Raises FilterChainError when a non-optional step does not match and
    *raise_on_mismatch* is True.
    """
    matched: List[str] = []
    for step in steps:
        try:
            apply_filters(payload, step["filters"])
            matched.append(step["name"])
            if step["stop_on_match"]:
                break
        except FilterError:
            if not step["optional"] and raise_on_mismatch:
                raise FilterChainError(
                    f"Payload did not match required filter step '{step['name']}'"
                )
    return matched
