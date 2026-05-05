"""Tests for hookpipe.delivery module."""

import json
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from hookpipe.delivery import DeliveryError, deliver


def _make_response(status: int, body: str):
    """Helper to create a mock urllib response context manager."""
    mock_resp = MagicMock()
    mock_resp.status = status
    mock_resp.read.return_value = body.encode("utf-8")
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


@patch("hookpipe.delivery.urllib.request.urlopen")
def test_deliver_success(mock_urlopen):
    mock_urlopen.return_value = _make_response(200, '{"ok": true}')
    result = deliver("http://example.com/hook", {"event": "push"})
    assert result["status_code"] == 200
    assert result["body"] == '{"ok": true}'


@patch("hookpipe.delivery.urllib.request.urlopen")
def test_deliver_sends_json_body(mock_urlopen):
    mock_urlopen.return_value = _make_response(201, "")
    payload = {"key": "value", "num": 42}
    deliver("http://example.com/hook", payload)

    call_args = mock_urlopen.call_args
    req = call_args[0][0]
    assert req.data == json.dumps(payload).encode("utf-8")
    assert req.get_header("Content-type") == "application/json"


@patch("hookpipe.delivery.urllib.request.urlopen")
def test_deliver_custom_headers(mock_urlopen):
    mock_urlopen.return_value = _make_response(200, "")
    deliver(
        "http://example.com/hook",
        {"x": 1},
        headers={"X-Secret": "abc123"},
    )
    req = mock_urlopen.call_args[0][0]
    assert req.get_header("X-secret") == "abc123"


@patch("hookpipe.delivery.urllib.request.urlopen")
def test_deliver_custom_method(mock_urlopen):
    mock_urlopen.return_value = _make_response(200, "")
    deliver("http://example.com/hook", {}, method="PUT")
    req = mock_urlopen.call_args[0][0]
    assert req.get_method() == "PUT"


@patch("hookpipe.delivery.urllib.request.urlopen")
def test_deliver_http_error_raises(mock_urlopen):
    import urllib.error
    mock_urlopen.side_effect = urllib.error.HTTPError(
        url="http://example.com/hook",
        code=404,
        msg="Not Found",
        hdrs=None,
        fp=None,
    )
    with pytest.raises(DeliveryError, match="HTTP 404"):
        deliver("http://example.com/hook", {})


@patch("hookpipe.delivery.urllib.request.urlopen")
def test_deliver_url_error_raises(mock_urlopen):
    import urllib.error
    mock_urlopen.side_effect = urllib.error.URLError(reason="Connection refused")
    with pytest.raises(DeliveryError, match="Failed to reach"):
        deliver("http://unreachable.local/hook", {})


@patch("hookpipe.delivery.urllib.request.urlopen")
def test_deliver_non_2xx_raises(mock_urlopen):
    mock_urlopen.return_value = _make_response(500, "Internal Server Error")
    with pytest.raises(DeliveryError, match="Non-2xx response 500"):
        deliver("http://example.com/hook", {})
