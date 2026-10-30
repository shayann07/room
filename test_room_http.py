import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from room_http import create_server


def request_json(base, method, path, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    request = Request(base + path, data=data, method=method, headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=3) as response:
        return response.status, json.loads(response.read())


class LocalRoomHttpTests(unittest.TestCase):
    def start(self, db):
        server = create_server(db)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server, thread, f"http://127.0.0.1:{server.server_port}"

    def test_two_local_clients_share_durable_room(self):
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / "room.json"
            server, thread, base = self.start(db)
            try:
                payload = {"author": "nawaz", "text": "Build checkout", "kind": "assignment", "recipients": ["claude", "codex", "antigravity"], "idempotency_key": "checkout:1"}
                status, first = request_json(base, "POST", "/rooms/checkout/messages", payload)
                self.assertEqual(status, 200)
                status, retry = request_json(base, "POST", "/rooms/checkout/messages", payload)
                self.assertEqual(status, 200)
                self.assertEqual(retry["event"]["id"], first["event"]["id"])

                _, visible = request_json(base, "GET", "/rooms/checkout/events?after=0")
                self.assertEqual(len(visible["events"]), 1)
                event_id = visible["events"][0]["id"]
                _, ack = request_json(base, "POST", "/rooms/checkout/ack", {"participant": "claude", "event_id": event_id})
                self.assertEqual(ack["state"], "acknowledged")

                _, agent = request_json(base, "POST", "/rooms/checkout/messages", {"author": "codex", "text": "I received it."})
                self.assertEqual(agent["event"]["author"], "codex")
                with self.assertRaises(HTTPError) as forged:
                    request_json(base, "POST", "/rooms/checkout/messages", {"author": "forged", "text": "I am Claude"})
                self.assertEqual(forged.exception.code, 403)
            finally:
                server.shutdown()
                thread.join(timeout=3)
                server.server_close()

            restarted, thread, base = self.start(db)
            try:
                _, recovered = request_json(base, "GET", "/rooms/checkout/events?after=0")
                self.assertEqual([e["author"] for e in recovered["events"]], ["nawaz", "codex"])
            finally:
                restarted.shutdown()
                thread.join(timeout=3)
                restarted.server_close()

    def test_server_rejects_non_local_bind(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                create_server(Path(d) / "room.json", host="0.0.0.0")


if __name__ == "__main__":
    unittest.main()
