"""HMAC signature verification for incoming webhook requests."""

import hashlib
import hmac
from typing import Optional


class SignatureError(Exception):
    """Raised when signature verification fails."""


def _compute_hmac(secret: str, payload: bytes, algorithm: str = "sha256") -> str:
    """Compute HMAC digest for the given payload and secret."""
    algo = getattr(hashlib, algorithm, None)
    if algo is None:
        raise SignatureError(f"Unsupported hash algorithm: {algorithm}")
    digest = hmac.new(secret.encode(), payload, algo).hexdigest()
    return f"{algorithm}={digest}"


def verify_signature(
    payload: bytes,
    secret: str,
    provided_signature: str,
    algorithm: str = "sha256",
    header_prefix: Optional[str] = None,
) -> bool:
    """Return True if provided_signature matches the computed HMAC.

    Args:
        payload: Raw request body bytes.
        secret: Shared secret string.
        provided_signature: Signature value from the request header.
        algorithm: Hash algorithm name (default: sha256).
        header_prefix: Optional prefix to strip from provided_signature before
            comparison (e.g. 'sha256=').
    """
    if header_prefix and provided_signature.startswith(header_prefix):
        provided_signature = provided_signature[len(header_prefix):]
        expected = _compute_hmac(secret, payload, algorithm)
        # Re-strip prefix from expected for comparison
        expected = expected[len(header_prefix):]
    else:
        expected = _compute_hmac(secret, payload, algorithm)
        if "=" in expected:
            expected = expected.split("=", 1)[1]
        if "=" in provided_signature:
            provided_signature = provided_signature.split("=", 1)[1]

    return hmac.compare_digest(expected, provided_signature)


def require_signature(
    payload: bytes,
    secret: str,
    provided_signature: Optional[str],
    algorithm: str = "sha256",
) -> None:
    """Verify signature and raise SignatureError if invalid or missing."""
    if not provided_signature:
        raise SignatureError("Missing signature header")
    if not verify_signature(payload, secret, provided_signature, algorithm):
        raise SignatureError("Signature mismatch: request could not be verified")
