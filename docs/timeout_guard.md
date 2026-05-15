# Timeout Guard

The `timeout_guard` module enforces a wall-clock deadline on any delivery
callable. If the wrapped function does not return within the allowed window a
`TimeoutError` is raised, preventing slow or unresponsive downstream services
from blocking the relay indefinitely.

> **Platform note** — the guard relies on `signal.SIGALRM` / `setitimer` and
> therefore requires a **POSIX** environment (Linux, macOS). It is not
> available on Windows.

---

## API

### `check_timeout(seconds, route_key)`

Validates that `seconds` is a positive finite number.  
Raises `ValueError` if the value is invalid, including the `route_key` in the
error message for easy diagnosis.

```python
check_timeout(5.0, "github")
```

---

### `with_timeout(fn, *, route_key, timeout)`

Wraps `fn` and enforces the given `timeout` (in seconds).

| Parameter   | Type       | Description                              |
|-------------|------------|------------------------------------------|
| `fn`        | `Callable` | The delivery function to wrap.           |
| `route_key` | `str`      | Route identifier used in error messages. |
| `timeout`   | `float`    | Maximum allowed execution time (s).      |

Returns a new callable with two extra attributes:
- `_route_key` — the route identifier supplied at wrap time.
- `_timeout`   — the timeout value supplied at wrap time.

Raises `TimeoutError` if `fn` runs longer than `timeout` seconds.

```python
from hookpipe.timeout_guard import with_timeout
from hookpipe.delivery import deliver

guarded_deliver = with_timeout(deliver, route_key="stripe", timeout=5.0)
result = guarded_deliver(payload, headers)
```

---

## Integration with the pipeline

Wrap the `_deliver` step inside `Pipeline` before passing it to
`with_circuit_breaker` or `with_retry`:

```python
fn = with_timeout(deliver, route_key=route_key, timeout=cfg["timeout"])
fn = with_circuit_breaker(fn, route_key=route_key)
fn = with_retry(fn, **retry_cfg)
fn(payload, headers)
```

---

## Error reference

| Exception      | Module          | Meaning                                     |
|----------------|-----------------|---------------------------------------------|
| `TimeoutError` | `timeout_guard` | Callable exceeded its wall-clock deadline.  |
| `ValueError`   | built-in        | Invalid `timeout` value passed to the API.  |
