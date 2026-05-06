# Metrics

hookpipe exposes lightweight **in-memory metrics** that can be scraped via a
built-in HTTP endpoint or inspected programmatically.

## Counters

| Counter | Description |
|---|---|
| `requests_received` | Total incoming webhook requests parsed |
| `requests_rejected` | Requests rejected by signature or filter rules |
| `deliveries_attempted` | Total delivery attempts (including retries) |
| `deliveries_succeeded` | Deliveries that received a 2xx response |
| `deliveries_failed` | Deliveries that exhausted all retries |
| `retries_total` | Total retry attempts across all deliveries |

## Timings

| Metric | Description |
|---|---|
| `delivery_duration_seconds` | Elapsed time for each outbound HTTP request |

Each timing metric exposes `count`, `sum`, `min`, `max`, and `avg`.

## Programmatic access

```python
from hookpipe.metrics import increment, record_timing, snapshot, reset

# Record an event
increment("requests_received")

# Record a timed delivery
import time
start = time.monotonic()
# ... perform delivery ...
record_timing("delivery_duration_seconds", time.monotonic() - start)

# Read current state
data = snapshot()
print(data["counters"]["deliveries_succeeded"])
```

## HTTP endpoint

Mount `MetricsHandler` on a port (e.g. 9090) to expose a `GET /metrics`
endpoint that returns a JSON snapshot:

```python
from http.server import HTTPServer
from hookpipe.metrics_handler import MetricsHandler

server = HTTPServer(("0.0.0.0", 9090), MetricsHandler)
server.serve_forever()
```

Example response:

```json
{
  "uptime_seconds": 42.1,
  "counters": {
    "requests_received": 100,
    "deliveries_succeeded": 98
  },
  "timings": {
    "delivery_duration_seconds": {
      "count": 98,
      "sum": 12.34,
      "min": 0.05,
      "max": 1.2,
      "avg": 0.126
    }
  }
}
```
