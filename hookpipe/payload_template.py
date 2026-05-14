"""Payload templating: render outgoing payloads from a Jinja2-style template."""

import re
from typing import Any


class TemplateError(Exception):
    """Raised when template rendering fails."""


_PLACEHOLDER = re.compile(r"\{\{\s*([\w.]+)\s*\}\}")


def _get_nested(payload: dict, key: str) -> Any:
    """Resolve a dotted key path against *payload*.

    Raises :class:`TemplateError` if any segment is missing.
    """
    parts = key.split(".")
    node: Any = payload
    for part in parts:
        if not isinstance(node, dict) or part not in node:
            raise TemplateError(f"Template key not found in payload: '{key}'")
        node = node[part]
    return node


def _render_value(value: Any, payload: dict) -> Any:
    """Recursively render *value* against *payload*.

    Strings containing ``{{ key }}`` placeholders are interpolated.
    Dicts and lists are traversed recursively.
    All other types are returned unchanged.
    """
    if isinstance(value, str):
        # Full-match shortcut: preserve the original type when the whole
        # string is a single placeholder.
        full = _PLACEHOLDER.fullmatch(value)
        if full:
            return _get_nested(payload, full.group(1))

        def _replace(m: re.Match) -> str:  # type: ignore[type-arg]
            resolved = _get_nested(payload, m.group(1))
            return str(resolved)

        return _PLACEHOLDER.sub(_replace, value)

    if isinstance(value, dict):
        return {k: _render_value(v, payload) for k, v in value.items()}

    if isinstance(value, list):
        return [_render_value(item, payload) for item in value]

    return value


def render_template(template: dict, payload: dict) -> dict:
    """Return a new dict produced by rendering *template* with values from *payload*.

    Parameters
    ----------
    template:
        A dict (possibly nested) whose string values may contain
        ``{{ dotted.key }}`` placeholders.
    payload:
        The source event payload used to resolve placeholders.

    Raises
    ------
    TemplateError
        If *template* or *payload* is not a dict, or a placeholder key
        cannot be resolved.
    """
    if not isinstance(template, dict):
        raise TemplateError("template must be a dict")
    if not isinstance(payload, dict):
        raise TemplateError("payload must be a dict")

    return _render_value(template, payload)  # type: ignore[return-value]
