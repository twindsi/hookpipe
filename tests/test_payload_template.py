"""Tests for hookpipe.payload_template."""

import pytest

from hookpipe.payload_template import TemplateError, render_template


# ---------------------------------------------------------------------------
# Basic rendering
# ---------------------------------------------------------------------------

def test_static_values_unchanged():
    result = render_template({"event": "push"}, {"ignored": True})
    assert result == {"event": "push"}


def test_top_level_placeholder_resolved():
    result = render_template({"repo": "{{ name }}"}, {"name": "hookpipe"})
    assert result == {"repo": "hookpipe"}


def test_dotted_placeholder_resolved():
    payload = {"repo": {"full_name": "acme/hookpipe"}}
    result = render_template({"slug": "{{ repo.full_name }}"}, payload)
    assert result == {"slug": "acme/hookpipe"}


def test_placeholder_preserves_non_string_type():
    """A lone placeholder whose value is an int should stay an int."""
    payload = {"count": 42}
    result = render_template({"total": "{{ count }}"}, payload)
    assert result["total"] == 42
    assert isinstance(result["total"], int)


def test_inline_placeholder_coerces_to_string():
    payload = {"count": 7}
    result = render_template({"msg": "items: {{ count }}"}, payload)
    assert result["msg"] == "items: 7"


def test_multiple_placeholders_in_one_string():
    payload = {"first": "Jane", "last": "Doe"}
    result = render_template({"name": "{{ first }} {{ last }}"}, payload)
    assert result["name"] == "Jane Doe"


# ---------------------------------------------------------------------------
# Nested template structures
# ---------------------------------------------------------------------------

def test_nested_dict_rendered():
    payload = {"action": "opened", "pr": {"number": 5}}
    template = {"event": {"type": "{{ action }}", "pr_id": "{{ pr.number }}"}}
    result = render_template(template, payload)
    assert result == {"event": {"type": "opened", "pr_id": 5}}


def test_list_values_rendered():
    payload = {"env": "prod"}
    template = {"tags": ["{{ env }}", "hookpipe"]}
    result = render_template(template, payload)
    assert result == {"tags": ["prod", "hookpipe"]}


def test_non_string_leaf_values_pass_through():
    result = render_template({"flag": True, "count": 0}, {})
    assert result == {"flag": True, "count": 0}


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

def test_missing_key_raises():
    with pytest.raises(TemplateError, match="not found"):
        render_template({"x": "{{ missing }}"}, {})


def test_missing_nested_key_raises():
    with pytest.raises(TemplateError, match="repo.name"):
        render_template({"x": "{{ repo.name }}"}, {"repo": {}})


def test_non_dict_template_raises():
    with pytest.raises(TemplateError, match="template must be a dict"):
        render_template("not a dict", {})  # type: ignore[arg-type]


def test_non_dict_payload_raises():
    with pytest.raises(TemplateError, match="payload must be a dict"):
        render_template({}, "not a dict")  # type: ignore[arg-type]


def test_original_payload_not_mutated():
    payload = {"a": {"b": 1}}
    render_template({"v": "{{ a.b }}"}, payload)
    assert payload == {"a": {"b": 1}}
