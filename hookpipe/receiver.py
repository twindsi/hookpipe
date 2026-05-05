"""HTTP receiver: parse and validate incoming webhook requests."""

import json
from typing import Any, Dict, Optional, Tuple

from hookpipe.secrets import SignatureError, require_signature


class ReceiverError(Exception):
    """Raised when an incoming request cannot be accepted."""


class IncomingRequest:
    """Minimal representation of an incoming HTTP request."""

    def __init__(
        self,
        body: bytes,
        headers: Optional[Dict[str, str]] = None,
        method: str = "POST",
        content_type: str = "application/json",
    ) -> None:
        self.body = body
        self.headers: Dict[str, str] = {k.lower(): v for k, v in (headers or {}).items()}
        self.method = method.upper()
        self.content_type = content_type


def parse_payload(request: IncomingRequest) -> Dict[str, Any]:
    """Decode and return the JSON payload from an IncomingRequest.

    Raises:
        ReceiverError: If the body is not valid JSON.
    """
    try:
        return json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ReceiverError(f"Invalid JSON payload: {exc}") from exc


def validate_request(
    request: IncomingRequest,
    secret: Optional[str] = None,
    signature_header: str = "x-hub-signature-256",
    algorithm: str = "sha256",
    allowed_methods: Tuple[str, ...] = ("POST",),
) -> Dict[str, Any]:
    """Validate an incoming request and return its parsed payload.

    Args:
        request: The IncomingRequest to validate.
        secret: Optional shared secret for HMAC verification.
        signature_header: Header name carrying the HMAC signature.
        algorithm: Hash algorithm used for HMAC.
        allowed_methods: HTTP methods accepted by this endpoint.

    Raises:
        ReceiverError: For method, content-type, or signature issues.
    """
    if request.method not in allowed_methods:
        raise ReceiverError(
            f"Method {request.method!r} not allowed; expected one of {allowed_methods}"
        )

    if "json" not in request.content_type:
        raise ReceiverError(
            f"Unsupported content-type: {request.content_type!r}; expected JSON"
        )

    if secret is not None:
        provided = request.headers.get(signature_header.lower())
        try:
            require_signature(request.body, secret, provided, algorithm=algorithm)
        except SignatureError as exc:
            raise ReceiverError(str(exc)) from exc

    return parse_payload(request)
