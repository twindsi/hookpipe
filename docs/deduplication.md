# Payload Deduplication

`hookpipe` can suppress duplicate webhook deliveries within a configurable
time window, preventing the same event from being forwarded more than once.

## How it works

Each incoming payload is assigned a stable **event ID**.  The ID is stored
in an in-memory sliding window keyed by a monotonic timestamp.  When a new
payload arrives:

1. Expired entries (older than `ttl` seconds) are evicted.
2. The event ID of the new payload is computed.
3. If the ID already exists in the window the payload is **dropped**;
   otherwise it is recorded and processing continues.

## Event ID strategies

### Field-based (recommended)

Set `id_field` to a dot-separated path inside the payload:

```yaml
routes:
  - path: /hooks/github
    dedup:
      id_field: "event.id"
      ttl: 600
```

The value at that path is coerced to a string and used as the ID.

### Hash-based (default)

When `id_field` is omitted a SHA-256 digest of the canonicalised JSON
payload is used.  Two payloads are considered identical only when every
field matches.

## Configuration reference

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `id_field` | string | — | Dot-path to the unique ID field in the payload. |
| `ttl` | integer (seconds) | `300` | How long to remember a seen event. |

## API

```python
from hookpipe.dedup import is_duplicate, reset

# Returns True when the payload was already seen within the TTL window.
if is_duplicate(payload, id_field="id", ttl=300):
    return  # drop
```

## Limitations

- The window is **in-process only**; it is not shared across multiple
  worker processes or restarts.
- For high-throughput deployments consider an external store (Redis, etc.).
