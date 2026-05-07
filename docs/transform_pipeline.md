# Transform Pipeline

The **transform pipeline** lets you chain multiple filter+transform steps
against an incoming webhook payload. Each step can optionally guard itself
with filters so that its transforms only run when the payload matches.

## Concepts

| Term | Description |
|------|-------------|
| **step** | A dict with optional `filters`, `transforms`, and `optional` keys. |
| **filters** | Applied first; if any filter fails the step is skipped (optional) or raises an error (required). |
| **transforms** | Applied after filters pass; mutate or enrich the payload. |
| **optional** | When `true`, a failing filter or transform silently skips the step instead of aborting. |

## Step schema

```json
{
  "filters": [
    { "field": "event", "op": "eq", "value": "push" }
  ],
  "transforms": [
    { "op": "set", "field": "processed", "value": true }
  ],
  "optional": false
}
```

## Usage

```python
from hookpipe.transform_pipeline import run_transform_pipeline

payload = {"event": "push", "repo": "acme/app"}

steps = [
    {
        "filters": [{"field": "event", "op": "eq", "value": "push"}],
        "transforms": [
            {"op": "set", "field": "ci_triggered", "value": True},
            {"op": "copy", "src": "repo", "dst": "source_repo"},
        ],
    },
    {
        "transforms": [{"op": "delete", "field": "repo"}],
        "optional": True,
    },
]

result = run_transform_pipeline(payload, steps)
# result == {"event": "push", "ci_triggered": True, "source_repo": "acme/app"}
```

## Error handling

- `TransformPipelineError` is raised when a required step's filter or
  transform fails.
- Set `"optional": true` on a step to silently skip it on failure and
  continue processing subsequent steps.
- Skipped steps are logged via `log_event` for observability.

## Integration with routes

Attach a `transform_pipeline` block to any route in your config:

```yaml
routes:
  - match: "push"
    transform_pipeline:
      - filters:
          - field: ref
            op: contains
            value: main
        transforms:
          - op: set
            field: branch
            value: main
    targets:
      - url: https://ci.example.com/hook
```
