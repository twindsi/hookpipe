# Event Filter Chain

The **event filter chain** lets you define an ordered sequence of named filter
steps that are evaluated against an incoming payload. Each step can be
required or optional, and any matching step can optionally stop further
processing.

## Concepts

| Term | Description |
|---|---|
| **step** | A named unit containing a list of filter rules |
| **optional** | When `true`, a mismatch on this step is silently skipped |
| **stop_on_match** | When `true`, processing halts after this step matches |

## Configuration

A chain is a list of step objects:

```yaml
filter_chain:
  - name: type_check
    filters:
      - field: type
        op: eq
        value: push
  - name: branch_check
    optional: true
    filters:
      - field: ref
        op: contains
        value: main
  - name: repo_guard
    stop_on_match: true
    filters:
      - field: repo
        op: eq
        value: acme/core
```

## Usage

```python
from hookpipe.event_filter_chain import build_chain, run_filter_chain

steps = build_chain(config["filter_chain"])

# Returns list of step names that matched.
# Raises FilterChainError if a required step does not match.
matched = run_filter_chain(payload, steps)
```

### Suppressing errors

Pass `raise_on_mismatch=False` to collect partial matches without raising:

```python
matched = run_filter_chain(payload, steps, raise_on_mismatch=False)
```

## Errors

- `FilterChainError` — raised for invalid chain configuration or a required
  step mismatch.

## Notes

- Step names must be unique within a chain.
- An empty `filters` list always matches (catch-all step).
- Steps are evaluated in declaration order.
