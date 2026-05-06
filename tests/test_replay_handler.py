"""Tests for hookpipe/replay_handler.py"""

import json
import io
from unittest.mock import MagicMock
import pytest
from hookpipe import replay
from hookpipe.replay_handler import ReplayHandler


def _make_handler(path: str) -> ReplayHandler:
    handler = ReplayHandler.__new__(ReplayHandler)
    handler.path = path
    handler.wfile = io.BytesIO()
    handler.send_response = MagicMock()
    handler.send_header = MagicMock()
    handler.end_headers = MagicMock()
    return handler


@pytest.fixture(autouse=True)
def setup_function():
    replay.reset()
    yield
    replay.reset()


def _read_body(handler: ReplayHandler) -> dict:
    handler.wfile.seek(0)
    return json.loads(handler.wfile.read())


def test_replay_endpoint_returns_200():
    h = _make_handler("/replay")
    h.do_GET()
    h.send_response.assert_called_once_with(200)


def test_replay_endpoint_returns_json_body():
    replay.store_event({"x": 1}, "r1")
    h = _make_handler("/replay")
    h.do_GET()
    body = _read_body(h)
    assert "events" in body
    assert body["count"] == 1


def test_replay_endpoint_filters_by_route_key():
    replay.store_event({"a": 1}, "r1")
    replay.store_event({"b": 2}, "r2")
    h = _make_handler("/replay?route_key=r1")
    h.do_GET()
    body = _read_body(h)
    assert body["count"] == 1
    assert body["events"][0]["route_key"] == "r1"


def test_replay_endpoint_fetch_by_key_found():
    key = replay.store_event({"z": 42}, "r-z")
    h = _make_handler(f"/replay?key={key}")
    h.do_GET()
    h.send_response.assert_called_once_with(200)
    body = _read_body(h)
    assert body["payload"] == {"z": 42}


def test_replay_endpoint_fetch_by_key_not_found():
    h = _make_handler("/replay?key=" + "0" * 64)
    h.do_GET()
    h.send_response.assert_called_once_with(404)
    body = _read_body(h)
    assert "error" in body


def test_replay_endpoint_unknown_path_returns_404():
    h = _make_handler("/not-replay")
    h.do_GET()
    h.send_response.assert_called_once_with(404)


def test_replay_endpoint_content_type_header():
    h = _make_handler("/replay")
    h.do_GET()
    calls = [str(c) for c in h.send_header.call_args_list]
    assert any("application/json" in c for c in calls)
