"""Tiny localhost-only HTTP facade for the disposable M0 room proof.

This is intentionally not a production server: it has no network auth and is
bound to 127.0.0.1 by default. It exists to prove that two local clients can
share the durable Room event/outbox behavior without a model provider.
"""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from m0_harness import AGENT_IDS, Room


class RoomService:
    def __init__(self, db_path: Path):
        self.room = Room(db_path)
        self.lock = threading.RLock()

    def events_after(self, event_id: int = 0):
        with self.lock:
            return [event for event in self.room.events if event["id"] > event_id]

    def post(self, payload: dict):
        author = payload.get("author")
        text = payload.get("text")
        if not isinstance(author, str) or not isinstance(text, str) or not text.strip():
            raise ValueError("author and non-empty text are required")
        kind = payload.get("kind", "message")
        recipients = tuple(payload.get("recipients", ()))
        idempotency_key = payload.get("idempotency_key")
        with self.lock:
            if author in AGENT_IDS:
                return self.room.post_agent(author, text, kind, recipients, idempotency_key)
            if author == "nawaz":
                return self.room.post(author, text, kind, recipients, idempotency_key)
            raise PermissionError("unknown actor identity")

    def acknowledge(self, payload: dict):
        participant = payload.get("participant")
        event_id = payload.get("event_id")
        if participant not in AGENT_IDS or not isinstance(event_id, int):
            raise PermissionError("known participant and integer event_id required")
        with self.lock:
            self.room.acknowledge(participant, event_id)
            return {"participant": participant, "event_id": event_id, "state": "acknowledged"}


class _Handler(BaseHTTPRequestHandler):
    server_version = "RoomM0/0.1"

    @property
    def service(self) -> RoomService:
        return self.server.room_service  # type: ignore[attr-defined]

    def _send(self, status: int, payload: dict):
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Room-Mode", "local-fixture-unauthenticated")
        self.end_headers()
        self.wfile.write(data)

    def _json_body(self):
        length = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(length) or b"{}")

    def do_GET(self):  # noqa: N802 - stdlib handler API
        parsed = urlparse(self.path)
        if parsed.path != "/rooms/checkout/events":
            self._send(404, {"error": "not found"})
            return
        try:
            after = int(parse_qs(parsed.query).get("after", ["0"])[0])
            self._send(200, {"events": self.service.events_after(after)})
        except (TypeError, ValueError):
            self._send(400, {"error": "after must be an integer"})

    def do_POST(self):  # noqa: N802 - stdlib handler API
        parsed = urlparse(self.path)
        try:
            payload = self._json_body()
            if parsed.path == "/rooms/checkout/messages":
                self._send(200, {"event": self.service.post(payload)})
            elif parsed.path == "/rooms/checkout/ack":
                self._send(200, self.service.acknowledge(payload))
            else:
                self._send(404, {"error": "not found"})
        except PermissionError as exc:
            self._send(403, {"error": str(exc)})
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            self._send(400, {"error": str(exc)})

    def log_message(self, *_args):
        return


def create_server(db_path: Path, host: str = "127.0.0.1", port: int = 0):
    if host not in {"127.0.0.1", "localhost"}:
        raise ValueError("M0 server must remain localhost-only")
    server = ThreadingHTTPServer((host, port), _Handler)
    server.room_service = RoomService(db_path)  # type: ignore[attr-defined]
    return server


def serve(db_path: Path, host: str = "127.0.0.1", port: int = 8787):
    server = create_server(db_path, host, port)
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    serve(Path("artifacts/m0/live-room-events.json"))
