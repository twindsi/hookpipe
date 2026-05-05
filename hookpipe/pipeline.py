"""Pipeline: combines filtering and transformation for a single webhook rule."""

from typing import Any

from hookpipe.filters import apply_filters, FilterError
from hookpipe.transforms import apply_transforms, TransformError


class PipelineError(Exception):
    """Raised when a pipeline rule is misconfigured or fails to execute."""


class Pipeline:
    """Applies a named set of filter + transform rules to an incoming payload.

    A rule dict is expected to have the shape::

        {
            "name": "my-rule",          # optional, for logging
            "filters": [...],            # list of filter dicts (see filters.py)
            "transforms": [...]          # list of transform dicts (see transforms.py)
        }
    """

    def __init__(self, rules: list[dict]) -> None:
        self.rules = rules

    def process(self, payload: dict) -> list[dict[str, Any]]:
        """Run payload through all matching rules.

        Returns a list of transformed payloads — one per matching rule.
        If no rules match, returns an empty list.
        """
        results = []
        for rule in self.rules:
            name = rule.get("name", "<unnamed>")
            filters = rule.get("filters", [])
            transforms = rule.get("transforms", [])

            try:
                matched = apply_filters(payload, filters)
            except FilterError as exc:
                raise PipelineError(f"Rule '{name}' filter error: {exc}") from exc

            if not matched:
                continue

            try:
                transformed = apply_transforms(payload, transforms)
            except TransformError as exc:
                raise PipelineError(f"Rule '{name}' transform error: {exc}") from exc

            results.append({"rule": name, "payload": transformed})

        return results


def pipeline_from_config(config: dict) -> "Pipeline":
    """Build a Pipeline from a loaded config dict.

    Expects config to contain a 'rules' key with a list of rule dicts.
    """
    rules = config.get("rules")
    if rules is None:
        raise PipelineError("Config must contain a 'rules' key")
    if not isinstance(rules, list):
        raise PipelineError("'rules' must be a list")
    return Pipeline(rules)
