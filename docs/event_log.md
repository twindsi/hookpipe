# Event Log

The event log provides an in-memory record of every webhook event processed by hookpipe, with TTL-based eviction and a queryable HTTP endpoint.

## Overview

Each time a webhook is processed — whether successfully delivered, filtered out, or failed — an entry is appended to the event log. Entries expire automatically after one hour and the store is capped at 10 000 entries.

## Appending Events

```python
from hookpipe.event_log import append_event

entry = append_event(
    route_key="github/push",
    payload={"ref": "refs/heads/main"},
    status="success",
    target_url="https://hooks.example.com/deploy",
)
```

### Valid Statuses

| Status     | Meaning                                      |
|------------|----------------------------------------------|
| `success`  | Delivered successfully                       |
| `failure`  | Delivery failed after all retries            |
| `filtered` | Dropped by a filter rule                     |
| `retried`  | Delivery succeeded after one or more retries |

## Querying Events

```python
from hookpipe.event_log import query_events

# All recent events
events = query_events()

# Filter by route and status
events = query_events(route_key="github/push", status="failure", limit=20)
```

Results are returned newest-first.

## HTTP Endpoint

Mount `EventLogHandler` to expose events over HTTP:

```
GET /events
GET /events?route_key=github%2Fpush
GET /events?status=failure
GET /events?limit=50
```

### Response

```json
{
  "events": [
    {
      "event_id": "a3f1c9d2e4b07812",
      "route_key": "github/push",
      "status": "success",
      "timestamp": 1718000000.123,
      "target_url": "https://hooks.example.com/deploy"
    }
  ],
  "count": 1
}
```

## Configuration

| Parameter      | Default | Description                        |
|----------------|---------|------------------------------------|
| `_TTL_SECONDS` | 3600    | Seconds before an entry is evicted |
| `_MAX_ENTRIES` | 10 000  | Maximum entries kept in memory     |
