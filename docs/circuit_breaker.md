# Circuit Breaker

Hookpipe includes a per-target circuit breaker to prevent cascading failures
when a downstream webhook endpoint becomes unavailable.

## How It Works

Each delivery target is tracked independently using a string key (typically the
target URL or route name). The circuit has three states:

| State | Description |
|-----------|------------------------------------------------------|
| `closed` | Normal operation; requests pass through. |
| `open` | Target is failing; requests are blocked immediately. |
| `half_open` | Recovery probe; one request is allowed through. |

### State Transitions

```
closed ──(N failures)──► open ──(timeout elapsed)──► half_open
  ▲                                                       │
  └───────────────(success recorded)─────────────────────┘
```

## Configuration

| Parameter | Default | Description |
|----------------------|---------|---------------------------------------------|
| `failure_threshold` | `5` | Failures before the circuit opens. |
| `recovery_timeout` | `30` s | Seconds before transitioning to half-open. |

## Usage

```python
from hookpipe.circuit_breaker import (
    check_circuit, record_success, record_failure, CircuitBreakerError
)

key = "https://example.com/webhook"

try:
    check_circuit(key)          # raises if open
    deliver(payload, target)    # your delivery call
    record_success(key)
except CircuitBreakerError:
    # blocked — log and skip
    pass
except Exception:
    record_failure(key)         # counts toward threshold
    raise
```

## Integration with Pipeline

The `Pipeline` class automatically wraps each `_deliver` call with circuit
breaker checks. Failures recorded by the retry module propagate into the
circuit breaker so the two systems work in concert.

## Inspecting State

```python
from hookpipe.circuit_breaker import get_status
print(get_status("https://example.com/webhook"))  # "closed"
```

## Resetting

```python
from hookpipe.circuit_breaker import reset
reset("https://example.com/webhook")  # reset one target
reset()                                # reset all targets
```
