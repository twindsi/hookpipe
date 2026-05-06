# Rate Limiting

Hookpipe includes a lightweight in-memory rate limiter that can be applied
per-route to protect downstream targets from traffic spikes.

## How it works

A **rolling window** algorithm tracks the timestamps of recent requests for
each route key.  When a new request arrives the limiter:

1. Evicts timestamps older than `window_seconds`.
2. Checks whether the remaining count is already at `max_requests`.
3. If so, raises `RateLimitError` with a `retry_after` hint (seconds).
4. Otherwise records the current timestamp and allows the request.

State is stored in a module-level dictionary (`_windows`) — suitable for
single-process deployments.  For multi-process or distributed setups,
replace the backing store with Redis or similar.

## API

```python
from hookpipe.rate_limit import check_rate_limit, RateLimitError

try:
    check_rate_limit(
        route_key="github-push",
        max_requests=100,
        window_seconds=60.0,
    )
except RateLimitError as exc:
    # Return HTTP 429 to the caller
    print(exc)
```

### `check_rate_limit(route_key, max_requests, window_seconds)`

| Parameter        | Type    | Description                                  |
|------------------|---------|----------------------------------------------|
| `route_key`      | `str`   | Unique key identifying the route or source.  |
| `max_requests`   | `int`   | Maximum allowed requests in the window.      |
| `window_seconds` | `float` | Rolling window length in seconds.            |

Raises `RateLimitError` when the limit is exceeded.

### `current_count(route_key, window_seconds) -> int`

Returns the number of requests currently recorded within the window.
Useful for metrics and debugging.

### `reset(route_key=None)`

Clears rate-limit state.  Omit `route_key` (or pass `None`) to reset
all routes — handy in tests.

## Configuration example

In your `hookpipe` YAML config you can annotate each route with rate-limit
parameters and call `check_rate_limit` inside the pipeline before forwarding:

```yaml
routes:
  - match:
      source: github
    rate_limit:
      max_requests: 200
      window_seconds: 60
    targets:
      - url: https://internal.example.com/hooks/github
```

## Notes

- State is **not** persisted across restarts.
- The limiter is **not** thread-safe by default; wrap calls with a lock
  if running in a multi-threaded WSGI server.
