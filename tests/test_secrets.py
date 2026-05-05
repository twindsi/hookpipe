"""Tests for hookpipe.secrets HMAC verification utilities."""

import hashlib
import hmac

import pytest

from hookpipe.secrets import (
    SignatureError,
    _compute_hmac,
    require_signature,
    verify_signature,
)

SECRET = "mysecret"
PAYLOAD = b'{"event": "push"}'


def _raw_hmac(secret: str, payload: bytes, algo: str = "sha256") -> str:
    return hmac.new(secret.encode(), payload, getattr(hashlib, algo)).hexdigest()


# --- _compute_hmac ---

def test_compute_hmac_returns_prefixed_hex():
    result = _compute_hmac(SECRET, PAYLOAD)
    assert result.startswith("sha256=")
    assert result == f"sha256={_raw_hmac(SECRET, PAYLOAD)}"


def test_compute_hmac_sha1():
    result = _compute_hmac(SECRET, PAYLOAD, algorithm="sha1")
    assert result.startswith("sha1=")


def test_compute_hmac_unsupported_algorithm():
    with pytest.raises(SignatureError, match="Unsupported hash algorithm"):
        _compute_hmac(SECRET, PAYLOAD, algorithm="md999")


# --- verify_signature ---

def test_verify_signature_valid():
    sig = f"sha256={_raw_hmac(SECRET, PAYLOAD)}"
    assert verify_signature(PAYLOAD, SECRET, sig) is True


def test_verify_signature_invalid():
    assert verify_signature(PAYLOAD, SECRET, "sha256=deadbeef") is False


def test_verify_signature_wrong_secret():
    sig = f"sha256={_raw_hmac('wrongsecret', PAYLOAD)}"
    assert verify_signature(PAYLOAD, SECRET, sig) is False


def test_verify_signature_with_header_prefix():
    raw = _raw_hmac(SECRET, PAYLOAD)
    provided = f"sha256={raw}"
    assert verify_signature(PAYLOAD, SECRET, provided, header_prefix="sha256=") is True


def test_verify_signature_no_prefix_in_provided():
    raw = _raw_hmac(SECRET, PAYLOAD)
    assert verify_signature(PAYLOAD, SECRET, raw) is True


# --- require_signature ---

def test_require_signature_passes_for_valid():
    sig = f"sha256={_raw_hmac(SECRET, PAYLOAD)}"
    require_signature(PAYLOAD, SECRET, sig)  # should not raise


def test_require_signature_raises_on_none():
    with pytest.raises(SignatureError, match="Missing signature header"):
        require_signature(PAYLOAD, SECRET, None)


def test_require_signature_raises_on_empty_string():
    with pytest.raises(SignatureError, match="Missing signature header"):
        require_signature(PAYLOAD, SECRET, "")


def test_require_signature_raises_on_mismatch():
    with pytest.raises(SignatureError, match="Signature mismatch"):
        require_signature(PAYLOAD, SECRET, "sha256=badhash")
