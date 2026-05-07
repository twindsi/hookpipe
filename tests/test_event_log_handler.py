import json
import io
from unittest.mock import patch, MagicMock
from hookpipe.event_log_handler import EventLogHandler
from hookpipe import event_log


def _make_handler(path: str) -> EventLogHandler:
    handler = EventLogHandler.__new__(EventLogHandler)
    handler.path = path
    handler.wfile = io.BytesIO()
    handler.send_response = MagicMock()
    handler.send_header = MagicMock()
    handler.end_headers = MagicMock()
    return handler


def setup_function():
    event_log.reset()


def _read_body(handler: EventLogHandler) -> dict:
    handler.wfile.seek(0)
    return json.loads(handler.wfile.read())


def test_event_log_endpoint_returns_200():
    handler = _make_handler("/events")
    handler.do_GET()
    handler.send_response.assert_called_once_with(200)


def test_event_log_endpoint_returns_json_body():
    event_log.append_event("route/a", {"x": 1}, "success")
    handler = _make_handler("/events")
    handler.do_GET()
    body = _read_body(handler)
    assert "events" in body
    assert "count" in body


def test_event_log_endpoint_filters_by_route_key():
    event_log.append_event("route/a", {"x": 1}, "success")
    event_log.append_event("route/b", {"y": 2}, "failure")
    handler = _make_handler("/events?route_key=route%2Fa")
    handler.do_GET()
    body = _read_body(handler)
    assert body["count"] == 1
    assert body["events"][0]["route_key"] == "route/a"


def test_event_log_endpoint_filters_by_status():
    event_log.append_event("route/a", {"x": 1}, "success")
    event_log.append_event("route/a", {"x": 2}, "failure")
    handler = _make_handler("/events?status=failure")
    handler.do_GET()
    body = _read_body(handler)
    assert body["count"] == 1
    assert body["events"][0]["status"] == "failure"


def test_event_log_endpoint_limit_parameter():
    for i in range(5):
        event_log.append_event("route/a", {"i": i}, "success")
    handler = _make_handler("/events?limit=3")
    handler.do_GET()
    body = _read_body(handler)
    assert body["count"] == 3


def test_event_log_endpoint_invalid_limit_returns_400():
    handler = _make_handler("/events?limit=abc")
    handler.do_GET()
    handler.send_response.assert_called_once_with(400)


def test_event_log_endpoint_unknown_path_returns_404():
    handler = _make_handler("/unknown")
    handler.do_GET()
    handler.send_response.assert_called_once_with(404)


def test_event_log_endpoint_content_type_header():
    handler = _make_handler("/events")
    handler.do_GET()
    calls = [str(c) for c in handler.send_header.call_args_list]
    assert any("application/json" in c for c in calls)
