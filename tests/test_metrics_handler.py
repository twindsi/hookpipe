"""Tests for hookpipe.metrics_handler."""

import json
import io
from unittest.mock import MagicMock, patch
from hookpipe.metrics_handler import MetricsHandler
from hookpipe.metrics import reset


def _make_handler(path: str) -> MetricsHandler:
    """Construct a MetricsHandler without a real socket."""
    handler = MetricsHandler.__new__(MetricsHandler)
    handler.path = path
    handler.wfile = io.BytesIO()
    handler.send_response = MagicMock()
    handler.send_header = MagicMock()
    handler.end_headers = MagicMock()
    return handler


def setup_function():
    reset()


def test_metrics_endpoint_returns_200():
    handler = _make_handler("/metrics")
    handler.do_GET()
    handler.send_response.assert_called_once_with(200)


def test_metrics_endpoint_returns_json_body():
    handler = _make_handler("/metrics")
    handler.do_GET()
    handler.wfile.seek(0)
    body = json.loads(handler.wfile.read())
    assert "counters" in body
    assert "timings" in body
    assert "uptime_seconds" in body


def test_metrics_endpoint_content_type_header():
    handler = _make_handler("/metrics")
    handler.do_GET()
    calls = [str(c) for c in handler.send_header.call_args_list]
    assert any("application/json" in c for c in calls)


def test_unknown_path_returns_404():
    handler = _make_handler("/healthz")
    handler.do_GET()
    handler.send_response.assert_called_once_with(404)


def test_unknown_path_returns_error_json():
    handler = _make_handler("/unknown")
    handler.do_GET()
    handler.wfile.seek(0)
    body = json.loads(handler.wfile.read())
    assert body.get("error") == "not found"
