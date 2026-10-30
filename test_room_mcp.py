import json
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

from m0_harness import Room

ROOT = Path(__file__).parent


class McpProcess:
    def __init__(self, db, participant, store="json"):
        self.process = subprocess.Popen(
            [sys.executable, str(ROOT / "room_mcp.py"), "--db", str(db), "--participant", participant, "--store", store],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    def request(self, method, request_id, params=None):
        self.process.stdin.write(json.dumps({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params or {}}) + "\n")
        self.process.stdin.flush()
        return json.loads(self.process.stdout.readline())

    def notify_initialized(self):
        self.process.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}) + "\n")
        self.process.stdin.flush()

    def close(self):
        self.process.stdin.close()
        self.process.wait(timeout=3)
        self.process.stdout.close()
        self.process.stderr.close()


class RoomMcpTests(unittest.TestCase):
    def test_two_stdio_connectors_share_events_and_identity_is_fixed(self):
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / "room.json"
            Room(db).post("nawaz", "Implement checkout", "assignment", ("claude", "codex"), "assignment:1")
            claude = McpProcess(db, "claude")
            codex = McpProcess(db, "codex")
            try:
                tool_names = {t["name"] for t in claude.request("tools/list", 1)["result"]["tools"]}
                self.assertEqual(tool_names, {"room_sync", "room_post", "question_raise", "room_wait", "assignment_claim", "assignment_checkpoint", "assignment_submit", "decision_propose"})
                claude.notify_initialized()
                codex.notify_initialized()
                posted = claude.request("tools/call", 2, {"name": "room_post", "arguments": {"text": "ROOM_MCP_FIXTURE", "recipients": ["codex"], "idempotency_key": "fixture:1"}})
                self.assertEqual(posted["result"]["structuredContent"]["event"]["author"], "claude")
                seen = codex.request("tools/call", 3, {"name": "room_sync", "arguments": {"after": 0}})
                self.assertIn("ROOM_MCP_FIXTURE", {event["text"] for event in seen["result"]["structuredContent"]["events"]})
                waited = codex.request("tools/call", 31, {"name": "room_wait", "arguments": {"after": 0, "timeout_ms": 50}})
                self.assertFalse(waited["result"]["structuredContent"]["timed_out"])
                question = codex.request("tools/call", 4, {"name": "question_raise", "arguments": {"text": "Can you confirm?", "recipients": ["claude"]}})
                self.assertEqual(question["result"]["structuredContent"]["author"], "codex")
                checkpoint = codex.request("tools/call", 5, {"name": "assignment_checkpoint", "arguments": {"assignment_id": 1, "summary": "Reviewing the flow."}})
                self.assertEqual(checkpoint["result"]["structuredContent"]["event"]["kind"], "assignment_checkpoint")
                proposal = claude.request("tools/call", 6, {"name": "decision_propose", "arguments": {"statement": "Keep the existing auth.", "affected_scope": "checkout"}})
                self.assertTrue(proposal["result"]["structuredContent"]["owner_approval_required"])
                submitted = codex.request("tools/call", 7, {"name": "assignment_submit", "arguments": {"assignment_id": 1, "summary": "Ready for review."}})
                self.assertTrue(submitted["result"]["structuredContent"]["owner_acceptance_required"])
                duplicate = claude.request("tools/call", 8, {"name": "room_post", "arguments": {"text": "ROOM_MCP_FIXTURE", "recipients": ["codex"], "idempotency_key": "fixture:1"}})
                self.assertEqual(duplicate["result"]["structuredContent"]["event"]["id"], posted["result"]["structuredContent"]["event"]["id"])
            finally:
                claude.close()
                codex.close()

    def test_room_wait_reports_a_bounded_timeout(self):
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / "room.json"
            process = McpProcess(db, "codex")
            try:
                waited = process.request("tools/call", 1, {"name": "room_wait", "arguments": {"after": 0, "timeout_ms": 25}})
                payload = waited["result"]["structuredContent"]
                self.assertTrue(payload["waited"])
                self.assertTrue(payload["timed_out"])
                self.assertEqual(payload["events"], [])
            finally:
                process.close()

    def test_room_wait_receives_event_during_active_wait_without_claiming_idle_wake(self):
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / "room.sqlite3"
            waiting = McpProcess(db, "codex", "sqlite")
            poster = McpProcess(db, "claude", "sqlite")
            result = {}
            try:
                def wait_for_event():
                    result["response"] = waiting.request("tools/call", 1, {"name": "room_wait", "arguments": {"after": 0, "timeout_ms": 1000}})

                thread = threading.Thread(target=wait_for_event)
                thread.start()
                time.sleep(0.1)
                poster.request("tools/call", 2, {"name": "room_post", "arguments": {"text": "WAIT_DELIVERY", "recipients": ["codex"], "idempotency_key": "wait:1"}})
                thread.join(timeout=3)
                self.assertIn("result", result["response"], result["response"])
                payload = result["response"]["result"]["structuredContent"]
                self.assertFalse(payload["timed_out"])
                self.assertIn("WAIT_DELIVERY", {event["text"] for event in payload["events"]})
            finally:
                waiting.close()
                poster.close()

    def test_sqlite_store_is_available_to_separate_connectors(self):
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / "room.sqlite3"
            seed = McpProcess(db, "claude", "sqlite")
            codex = McpProcess(db, "codex", "sqlite")
            try:
                seed.request("tools/call", 1, {"name": "room_post", "arguments": {"text": "SQLITE_MCP_FIXTURE", "recipients": ["codex"], "idempotency_key": "sqlite:1"}})
                seen = codex.request("tools/call", 2, {"name": "room_sync", "arguments": {"after": 0}})
                self.assertIn("SQLITE_MCP_FIXTURE", {event["text"] for event in seen["result"]["structuredContent"]["events"]})
            finally:
                seed.close()
                codex.close()

    def test_invalid_participant_is_rejected_before_start(self):
        with tempfile.TemporaryDirectory() as d:
            process = subprocess.run([sys.executable, str(ROOT / "room_mcp.py"), "--db", str(Path(d) / "room.json"), "--participant", "forged"], capture_output=True, text=True)
            self.assertNotEqual(process.returncode, 0)


if __name__ == "__main__":
    unittest.main()
