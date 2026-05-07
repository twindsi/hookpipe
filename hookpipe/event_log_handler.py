"""HTTP handler exposing the event log via a simple GET endpoint."""

import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from hookpipe.event_log import query_events


class EventLogHandler(BaseHTTPRequestHandler):
    """Serves GET /events with optional ?route_key=&status=&limit= query params."""

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/events":
            self._respond(404, {"error": "not found"})
            return

        params = parse_qs(parsed.query)
        route_key = params.get("route_key", [None])[0]
        status = params.get("status", [None])[0]
        try:
            limit = int(params.get("limit", ["50"])[0])
        except ValueError:
            self._respond(400, {"error": "limit must be an integer"})
            return

        events = query_events(route_key=route_key, status=status, limit=limit)
        # Strip internal timestamp before returning
        public = [{k: v for k, v in e.items() if k != "_ts"} for e in events]
        self._respond(200, {"count": len(public), "events": public})

    def _respond(self, code: int, body: dict) -> None:
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt: str, *args: object) -> None:  # pragma: no cover
        pass
