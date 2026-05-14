"""Middleware for enriching outgoing webhook request headers before delivery."""

from typing import Any, Callable, Dict, Optional


class HeaderEnricherError(Exception):
    """Raised when header enrichment configuration is invalid."""


_RESERVED_HEADERS = frozenset({
    "content-length",
    "transfer-encoding",
    "host",
})


def _normalise_key(key: str) -> str:
    """Return header key lowercased and stripped."""
    return key.strip().lower()


def _validate_static_headers(headers: Dict[str, str]) -> None:
    """Raise HeaderEnricherError if any static header key is reserved or empty."""
    for key, value in headers.items():
        normalised = _normalise_key(key)
        if not normalised:
            raise HeaderEnricherError("Header key must not be empty.")
        if normalised in _RESERVED_HEADERS:
            raise HeaderEnricherError(
                f"Header '{key}' is reserved and cannot be overridden."
            )
        if not isinstance(value, str):
            raise HeaderEnricherError(
                f"Header value for '{key}' must be a string, got {type(value).__name__}."
            )


def build_enricher(
    static_headers: Optional[Dict[str, str]] = None,
    dynamic_headers: Optional[Dict[str, Callable[[Dict[str, Any]], str]]] = None,
) -> Callable[[Dict[str, Any], Dict[str, str]], Dict[str, str]]:
    """Return an enricher function that merges static and dynamic headers.

    Args:
        static_headers: Fixed key/value pairs added to every request.
        dynamic_headers: Mapping of header name to a callable that receives
            the current payload and returns a string value.

    Returns:
        A callable ``enrich(payload, existing_headers) -> merged_headers``.
    """
    static = dict(static_headers or {})
    _validate_static_headers(static)
    dynamic = dict(dynamic_headers or {})

    for key in dynamic:
        normalised = _normalise_key(key)
        if not normalised:
            raise HeaderEnricherError("Dynamic header key must not be empty.")
        if normalised in _RESERVED_HEADERS:
            raise HeaderEnricherError(
                f"Dynamic header '{key}' is reserved and cannot be overridden."
            )

    def enrich(
        payload: Dict[str, Any],
        existing_headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        merged: Dict[str, str] = dict(existing_headers or {})
        merged.update(static)
        for key, fn in dynamic.items():
            merged[key] = fn(payload)
        return merged

    return enrich
