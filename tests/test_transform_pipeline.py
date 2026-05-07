"""Tests for hookpipe.transform_pipeline."""

import pytest

from hookpipe.transform_pipeline import (
    TransformPipelineError,
    run_transform_pipeline,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BASE_PAYLOAD = {"event": "push", "repo": "acme/app", "ref": "refs/heads/main"}


# ---------------------------------------------------------------------------
# run_transform_pipeline
# ---------------------------------------------------------------------------


def test_empty_steps_returns_payload_unchanged():
    result = run_transform_pipeline(BASE_PAYLOAD, [])
    assert result == BASE_PAYLOAD


def test_single_transform_step():
    steps = [{"transforms": [{"op": "set", "field": "processed", "value": True}]}]
    result = run_transform_pipeline(BASE_PAYLOAD, steps)
    assert result["processed"] is True
    assert result["event"] == "push"


def test_filter_passes_and_transform_applied():
    steps = [
        {
            "filters": [{"field": "event", "op": "eq", "value": "push"}],
            "transforms": [{"op": "set", "field": "tag", "value": "ci"}],
        }
    ]
    result = run_transform_pipeline(BASE_PAYLOAD, steps)
    assert result["tag"] == "ci"


def test_filter_fails_raises_pipeline_error():
    steps = [
        {
            "filters": [{"field": "event", "op": "eq", "value": "release"}],
            "transforms": [{"op": "set", "field": "tag", "value": "ci"}],
        }
    ]
    with pytest.raises(TransformPipelineError, match="Step 0 filter failed"):
        run_transform_pipeline(BASE_PAYLOAD, steps)


def test_optional_step_filter_fail_skips_step():
    steps = [
        {
            "filters": [{"field": "event", "op": "eq", "value": "release"}],
            "transforms": [{"op": "set", "field": "tag", "value": "ci"}],
            "optional": True,
        }
    ]
    result = run_transform_pipeline(BASE_PAYLOAD, steps)
    assert "tag" not in result


def test_multiple_steps_applied_in_order():
    steps = [
        {"transforms": [{"op": "set", "field": "step", "value": 1}]},
        {"transforms": [{"op": "set", "field": "step", "value": 2}]},
    ]
    result = run_transform_pipeline(BASE_PAYLOAD, steps)
    assert result["step"] == 2


def test_delete_field_in_step():
    steps = [{"transforms": [{"op": "delete", "field": "ref"}]}]
    result = run_transform_pipeline(BASE_PAYLOAD, steps)
    assert "ref" not in result


def test_copy_field_in_step():
    steps = [
        {"transforms": [{"op": "copy", "src": "event", "dst": "event_copy"}]}
    ]
    result = run_transform_pipeline(BASE_PAYLOAD, steps)
    assert result["event_copy"] == "push"


def test_invalid_steps_type_raises():
    with pytest.raises(TransformPipelineError, match="'steps' must be a list"):
        run_transform_pipeline(BASE_PAYLOAD, "not-a-list")  # type: ignore[arg-type]


def test_original_payload_not_mutated():
    original = {"event": "push", "ref": "main"}
    steps = [{"transforms": [{"op": "set", "field": "new_key", "value": 99}]}]
    run_transform_pipeline(original, steps)
    assert "new_key" not in original
