"""Chained transform and filter pipeline with per-step error isolation."""

from typing import Any, Dict, List

from hookpipe.filters import apply_filters, FilterError
from hookpipe.transforms import apply_transforms, TransformError
from hookpipe.logging_utils import log_event


class TransformPipelineError(Exception):
    """Raised when a transform pipeline step fails fatally."""


def _run_step(
    step: Dict[str, Any],
    payload: Dict[str, Any],
    step_index: int,
) -> Dict[str, Any]:
    """Execute a single pipeline step (filter + transforms).

    Returns the (possibly mutated) payload, or raises TransformPipelineError
    if a non-optional step fails.
    """
    filters = step.get("filters", [])
    transforms = step.get("transforms", [])
    optional = step.get("optional", False)

    try:
        if filters:
            apply_filters(payload, filters)
    except FilterError as exc:
        if optional:
            log_event(
                "transform_pipeline.step_skipped",
                {"step": step_index, "reason": str(exc)},
            )
            return payload
        raise TransformPipelineError(
            f"Step {step_index} filter failed: {exc}"
        ) from exc

    try:
        if transforms:
            payload = apply_transforms(payload, transforms)
    except TransformError as exc:
        if optional:
            log_event(
                "transform_pipeline.step_transform_skipped",
                {"step": step_index, "reason": str(exc)},
            )
            return payload
        raise TransformPipelineError(
            f"Step {step_index} transform failed: {exc}"
        ) from exc

    return payload


def run_transform_pipeline(
    payload: Dict[str, Any],
    steps: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Run all pipeline steps in order against *payload*.

    Args:
        payload: The incoming webhook payload dict.
        steps:   Ordered list of step dicts, each containing optional
                 ``filters``, ``transforms``, and ``optional`` keys.

    Returns:
        The transformed payload after all steps have been applied.

    Raises:
        TransformPipelineError: If a non-optional step fails.
    """
    if not isinstance(steps, list):
        raise TransformPipelineError("'steps' must be a list")

    current = dict(payload)
    for index, step in enumerate(steps):
        current = _run_step(step, current, index)

    return current
