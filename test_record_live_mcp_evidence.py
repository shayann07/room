import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from record_live_mcp_evidence import run


class RegisteredMcpEvidenceTests(unittest.TestCase):
    def test_host_mediated_codex_pass_is_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for provider in ("codex", "antigravity"):
                (root / "results" / provider).mkdir(parents=True)
                (root / "results" / provider / "result.json").write_text(json.dumps({"returncode": 0, "mcp_server_marker_seen": True, "tool_ack_seen": False, "file_changes": False}))
                (root / "results" / provider / "stdout.txt").write_text(json.dumps({"method": "room_post"}) + "\n")
            (root / "results" / "codex" / "result.json").write_text(json.dumps({"returncode": 0, "mcp_server_marker_seen": True, "tool_ack_seen": True, "file_changes": False}))
            db = root / "room.sqlite3"
            connection = sqlite3.connect(db)
            connection.executescript("CREATE TABLE events(id INTEGER, author TEXT, text TEXT, kind TEXT, idempotency_key TEXT); INSERT INTO events VALUES (1, 'codex', 'LIVE_MCP_ACK', 'live_mcp_ack', 'live-mcp:codex-appserver:1');")
            connection.commit()
            connection.close()
            (root / "codex-appserver-result.json").write_text(json.dumps({"persistent_policy_amendment": False, "bypass_flags_used": False, "room_events": [{"author": "codex", "kind": "live_mcp_ack"}]}))
            summary = run(root, db)
            self.assertEqual(summary["codex_appserver_host_mediated"]["status"], "delivery_pass")
            self.assertIn("Codex app-server", summary["native_room_delivery"])
            self.assertEqual(summary["room_events_after_test"][0]["author"], "codex")


if __name__ == "__main__":
    unittest.main()
