"""HTTP handler that exposes the /metrics endpoint as JSON."""

import json
from http.server import BaseHTTPRequestHandler
from hookpipe.metrics import snapshot


class MetricsHandler(BaseHTTPRequestHandler):
    """Minimal HTTP request handler that serves live metrics at GET /metrics."""

    def do_GET(self) -> None:  # noqa: N802
        if self.path != "/metrics":
            self._respond(404, {"error": "not found"})
            return
        data = snapshot()
        self._respond(200, data)

    def _respond(self, status: int, body: dict) -> None:
        payload = json.dumps(body, indent=2).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, fmt: str, *args) -> None:  # pragma: no cover
        """Suppress default access log output."""
