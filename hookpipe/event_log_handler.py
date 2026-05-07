import json
from http.server import BaseHTTPRequestHandler
from hookpipe.event_log import query_events, EventLogError


class EventLogHandler(BaseHTTPRequestHandler):
    """HTTP handler exposing the event log query endpoint."""

    def do_GET(self):
        from urllib.parse import urlparse, parse_qs

        parsed = urlparse(self.path)
        if parsed.path != "/events":
            self._respond(404, {"error": "not found"})
            return

        params = parse_qs(parsed.query)
        route_key = params.get("route_key", [None])[0]
        status = params.get("status", [None])[0]
        limit_raw = params.get("limit", ["100"])[0]

        try:
            limit = int(limit_raw)
        except ValueError:
            self._respond(400, {"error": "invalid limit parameter"})
            return

        try:
            entries = query_events(route_key=route_key, status=status, limit=limit)
        except EventLogError as exc:
            self._respond(400, {"error": str(exc)})
            return

        self._respond(200, {"events": entries, "count": len(entries)})

    def _respond(self, code: int, body: dict) -> None:
        payload = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, fmt, *args):  # silence default stderr logging
        pass
