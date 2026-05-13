"""Middleware that applies schema validation within a transform pipeline step."""

from typing import Any

from hookpipe.webhook_validator import validate_payload, ValidationError


def with_validation(schema: dict):
    """Return a callable that validates a payload against *schema*.

    Intended to be used as a pipeline step function::

        step = with_validation({"required": ["event"], "types": {"event": "string"}})
        step(payload)  # raises ValidationError on invalid payload

    Returns the payload unchanged on success.
    """
    def _validate(payload: Any) -> Any:
        validate_payload(payload, schema)
        return payload

    _validate.__name__ = "with_validation"
    return _validate
