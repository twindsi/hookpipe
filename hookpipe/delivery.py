"""HTTP delivery module for forwarding transformed payloads to target URLs."""

import json
import urllib.request
import urllib.error
from typing import Any, Dict, Optional


class DeliveryError(Exception):
    """Raised when delivery to a target URL fails."""
    pass


def deliver(
    url: str,
    payload: Dict[str, Any],
    method: str = "POST",
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 10,
) -> Dict[str, Any]:
    """Send a payload as JSON to the given URL.

    Args:
        url: Target URL to deliver the payload to.
        payload: Dictionary to serialize as JSON body.
        method: HTTP method to use (default: POST).
        headers: Optional additional HTTP headers.
        timeout: Request timeout in seconds (default: 10).

    Returns:
        Dict with keys 'status_code' and 'body'.

    Raises:
        DeliveryError: If the request fails or returns a non-2xx status.
    """
    default_headers = {"Content-Type": "application/json"}
    if headers:
        default_headers.update(headers)

    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, headers=default_headers, method=method.upper()
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status_code = resp.status
            response_body = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        raise DeliveryError(
            f"HTTP {exc.code} delivering to {url}: {exc.reason}"
        ) from exc
    except urllib.error.URLError as exc:
        raise DeliveryError(
            f"Failed to reach {url}: {exc.reason}"
        ) from exc

    if not (200 <= status_code < 300):
        raise DeliveryError(
            f"Non-2xx response {status_code} from {url}"
        )

    return {"status_code": status_code, "body": response_body}
