"""Run a clean local preflight for the unregistered Room MCP connector."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).parent
EXPECTED_TOOLS = {"room_sync", "room_post", "assignment_claim", "assignment_checkpoint", "assignment_submit", "decision_propose", "question_raise", "room_wait"}


class Client:
    def __init__(self, db: Path, participant: str):
        self.process = subprocess.Popen(
            [sys.executable, str(ROOT / "room_mcp.py"), "--db", str(db), "--store", "sqlite", "--participant", participant],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )

    def request(self, request_id, method, params=None):
        self.process.stdin.write(json.dumps({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params or {}}) + "\n")
        self.process.stdin.flush()
        return json.loads(self.process.stdout.readline())

    def close(self):
        self.process.stdin.close()
        self.process.wait(timeout=3)
        self.process.stdout.close()
        self.process.stderr.close()


def validate_enrollment_plan():
    plan = json.loads((ROOT / "artifacts/m0/mcp-enrollment-plan.json").read_text(encoding="utf-8"))
    results = {}
    for provider, registration in plan["registrations"].items():
        command = registration["add"]
        results[provider] = {
            "has_add_command": command[1:3] == ["mcp", "add"],
            "uses_sqlite": "--store" in command and "sqlite" in command,
            "contains_bypass_flag": any("dangerously" in item for item in command),
            "has_remove_command": registration["remove"][1:3] == ["mcp", "remove"],
        }
    return results


def run():
    with tempfile.TemporaryDirectory() as directory:
        db = Path(directory) / "preflight.sqlite3"
        first = Client(db, "claude")
        second = Client(db, "codex")
        try:
            initialized = first.request(1, "initialize")
            tools = first.request(2, "tools/list")["result"]["tools"]
            posted = first.request(3, "tools/call", {"name": "room_post", "arguments": {"text": "PREFLIGHT", "recipients": ["codex"], "idempotency_key": "preflight:1"}})
            visible = second.request(4, "tools/call", {"name": "room_sync", "arguments": {"after": 0}})
            tool_names = {tool["name"] for tool in tools}
            visible_texts = {event["text"] for event in visible["result"]["structuredContent"]["events"]}
            result = {
                "status": "pass" if initialized.get("result", {}).get("serverInfo", {}).get("name") == "room-m0-mcp" and EXPECTED_TOOLS == tool_names and posted["result"]["structuredContent"]["author"] == "claude" and "PREFLIGHT" in visible_texts else "fail",
                "handshake": initialized.get("result", {}).get("serverInfo", {}),
                "tool_count": len(tool_names),
                "expected_tools_present": EXPECTED_TOOLS == tool_names,
                "cross_process_sqlite_visibility": "PREFLIGHT" in visible_texts,
                "provider_configuration_changed": False,
                "enrollment_templates": validate_enrollment_plan(),
            }
        finally:
            first.close()
            second.close()
    output = ROOT / "artifacts/m0/mcp-preflight.json"
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(run())
