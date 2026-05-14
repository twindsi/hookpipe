# Payload Templating

The `hookpipe.payload_template` module lets you define a **static template dict** for outgoing webhook bodies and have it populated at runtime from the incoming event payload.

## Quick start

```python
from hookpipe.payload_template import render_template

payload = {
    "repository": {"full_name": "acme/hookpipe"},
    "action": "opened",
    "pull_request": {"number": 42},
}

template = {
    "text": "PR #{{ pull_request.number }} {{ action }} on {{ repository.full_name }}",
    "metadata": {
        "repo": "{{ repository.full_name }}",
        "pr": "{{ pull_request.number }}",
    },
}

result = render_template(template, payload)
# {
#   "text": "PR #42 opened on acme/hookpipe",
#   "metadata": {"repo": "acme/hookpipe", "pr": 42},
# }
```

## Placeholder syntax

Use `{{ key }}` or `{{ parent.child }}` (dot notation for nested fields) anywhere inside a string value.

| Pattern | Behaviour |
|---|---|
| Whole string is one placeholder | Original type preserved (e.g. `int`, `bool`, `list`) |
| Placeholder embedded in a longer string | Value coerced to `str` and interpolated |
| Multiple placeholders in one string | Each resolved independently and concatenated |

## Nested templates

Templates may contain arbitrarily nested dicts and lists — every string leaf is rendered recursively.

```python
template = {
    "blocks": [
        {"type": "section", "text": "Actor: {{ sender.login }}"},
    ]
}
```

## Error handling

`render_template` raises `TemplateError` when:

- `template` or `payload` is not a `dict`.
- A placeholder key (or any segment of a dotted path) cannot be found in the payload.

```python
from hookpipe.payload_template import TemplateError

try:
    result = render_template(template, payload)
except TemplateError as exc:
    # log / skip / raise HTTP 500
    ...
```

## Integration with the transform pipeline

Call `render_template` as the last step of a `run_transform_pipeline` chain to produce the final request body before `deliver` is called:

```python
body = render_template(target["template"], processed_payload)
await deliver(target["url"], body, headers=headers)
```
