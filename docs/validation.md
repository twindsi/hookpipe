# Payload Validation

hookpipe supports rule-based schema validation for incoming webhook payloads before they are processed by the transform pipeline.

## Overview

Validation is performed by `hookpipe.webhook_validator.validate_payload`. It checks three categories of rules:

| Rule | Description |
|---|---|
| `required` | Fields that must be present in the payload |
| `types` | Expected JSON type for a field |
| `allowed_values` | Enumerated set of acceptable values for a field |

Nested fields are referenced with dot notation, e.g. `repo.name`.

## Supported Types

`string`, `number`, `boolean`, `object`, `array`, `null`

## Example Schema

```python
schema = {
    "required": ["event", "repo.name"],
    "types": {
        "event": "string",
        "payload.size": "number",
        "draft": "boolean"
    },
    "allowed_values": {
        "event": ["push", "pull_request", "release"]
    }
}
```

## Direct Usage

```python
from hookpipe.webhook_validator import validate_payload, ValidationError

try:
    validate_payload(payload, schema)
except ValidationError as exc:
    print(f"Invalid payload: {exc}")
```

## Pipeline Integration

Use `with_validation` to create a validation step for the transform pipeline:

```python
from hookpipe.validation_middleware import with_validation
from hookpipe.transform_pipeline import run_transform_pipeline

steps = [
    {"fn": with_validation(schema)},
    {"transforms": [{"op": "set", "field": "processed", "value": True}]},
]

result = run_transform_pipeline(payload, steps)
```

If validation fails, a `ValidationError` is raised and pipeline execution stops (unless the step is marked `optional: true`, in which case the step is skipped).

## Errors

`ValidationError` is raised with a descriptive message indicating which field failed and why.
