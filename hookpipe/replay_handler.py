"""HTTP handler exposing the replay buffer via a simple GET endpoint."""

import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from hookpipe import replay


class ReplayHandler(BaseHTTPRequestHandler):
    """Serves GET /replay and GET /replay?route_key=<key> requests."""

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/replay":
            self._respond(404, {"error": "not found"})
            return
        params = parse_qs(parsed.query)
        route_key = params.get("route_key", [None])[0]
        event_key = params.get("key", [None])[0]
        try:
            if event_key is not None:
                event = replay.get_event_by_key(event_key)
                if event is None:
                    self._respond(404, {"error": "event not found"})
                else:
                    self._respond(200, event)
            else:
                events = replay.get_events(route_key=route_key)
                self._respond(200, {"events": events, "count": len(events)})
        except Exception as exc:  # pragma: no cover
            self._respond(500, {"error": str(exc)})

    def _respond(self, status: int, body: dict) -> None:
        encoded = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, fmt: str, *args) -> None:  # pragma: no cover
        pass
