"""Tests for hookpipe.receiver request parsing and validation."""

import hashlib
import hmac
import json

import pytest

from hookpipe.receiver import IncomingRequest, ReceiverError, parse_payload, validate_request

SECRET = "topsecret"
PAYLOAD_DICT = {"action": "opened", "number": 42}
PAYLOAD_BYTES = json.dumps(PAYLOAD_DICT).encode()


def _sign(payload: bytes, secret: str = SECRET, algo: str = "sha256") -> str:
    digest = hmac.new(secret.encode(), payload, getattr(hashlib, algo)).hexdigest()
    return f"{algo}={digest}"


def _make_request(body=PAYLOAD_BYTES, headers=None, method="POST", ct="application/json"):
    return IncomingRequest(body=body, headers=headers, method=method, content_type=ct)


# --- parse_payload ---

def test_parse_payload_valid_json():
    req = _make_request()
    assert parse_payload(req) == PAYLOAD_DICT


def test_parse_payload_invalid_json():
    req = _make_request(body=b"not-json")
    with pytest.raises(ReceiverError, match="Invalid JSON"):
        parse_payload(req)


def test_parse_payload_empty_body():
    req = _make_request(body=b"")
    with pytest.raises(ReceiverError):
        parse_payload(req)


# --- validate_request ---

def test_validate_request_no_secret():
    req = _make_request()
    result = validate_request(req)
    assert result == PAYLOAD_DICT


def test_validate_request_with_valid_signature():
    sig = _sign(PAYLOAD_BYTES)
    req = _make_request(headers={"x-hub-signature-256": sig})
    result = validate_request(req, secret=SECRET)
    assert result["action"] == "opened"


def test_validate_request_missing_signature_raises():
    req = _make_request()
    with pytest.raises(ReceiverError, match="Missing signature"):
        validate_request(req, secret=SECRET)


def test_validate_request_bad_signature_raises():
    req = _make_request(headers={"x-hub-signature-256": "sha256=badhash"})
    with pytest.raises(ReceiverError, match="Signature mismatch"):
        validate_request(req, secret=SECRET)


def test_validate_request_wrong_method():
    req = _make_request(method="GET")
    with pytest.raises(ReceiverError, match="Method"):
        validate_request(req)


def test_validate_request_wrong_content_type():
    req = _make_request(ct="text/plain")
    with pytest.raises(ReceiverError, match="content-type"):
        validate_request(req)


def test_validate_request_custom_allowed_methods():
    req = _make_request(method="PUT")
    result = validate_request(req, allowed_methods=("PUT", "POST"))
    assert result == PAYLOAD_DICT


def test_incoming_request_lowercases_headers():
    req = IncomingRequest(PAYLOAD_BYTES, headers={"X-Hub-Signature-256": "abc"})
    assert "x-hub-signature-256" in req.headers
