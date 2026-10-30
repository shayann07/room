"""Bounded Codex app-server MCP probe with host-mediated approval."""
from __future__ import annotations

import argparse
import json
import queue
import sqlite3
import subprocess
import threading
import time
from pathlib import Path


PROMPT = "Use the Room MCP tool room_post exactly once with text LIVE_MCP_ACK, kind live_mcp_ack, idempotency_key live-mcp:codex-appserver:1, and recipients [nawaz]. Do not use shell or file tools. After the tool call, reply exactly ROOM_MCP_TOOL_ACK."


class JsonProcess:
    def __init__(self, cwd: Path):
        self.process = subprocess.Popen(["codex", "app-server", "--listen", "stdio://"], cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.lines = queue.Queue()
        self.stderr = []
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()
        self.err_reader = threading.Thread(target=self._read_err, daemon=True)
        self.err_reader.start()

    def _read(self):
        for line in self.process.stdout:
            try:
                self.lines.put(json.loads(line))
            except ValueError:
                self.lines.put({"_raw": line})

    def _read_err(self):
        for line in self.process.stderr:
            self.stderr.append(line)

    def send(self, message):
        self.process.stdin.write(json.dumps(message) + "\n")
        self.process.stdin.flush()

    def close(self):
        try:
            self.process.stdin.close()
        except Exception:
            pass
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=5)

    def wait_for_id(self, request_id, timeout=30):
        deadline = time.monotonic() + timeout
        pending = []
        while time.monotonic() < deadline:
            try:
                message = self.lines.get(timeout=0.2)
            except queue.Empty:
                continue
            if message.get("id") == request_id:
                return message, pending
            pending.append(message)
        raise TimeoutError(f"timed out waiting for response {request_id}; pending={pending[-3:]}")


def run(out: Path):
    workdir = (out / "workspace").resolve()
    workdir.mkdir(parents=True, exist_ok=True)
    db = Path("artifacts/m0/registered-room.sqlite3")
    client = JsonProcess(workdir)
    events = []
    approvals = []
    status = "failed"
    error = None
    turn_completed = False
    try:
        client.send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"clientInfo": {"name": "room-m0-host", "version": "0.1.0"}, "capabilities": {}}})
        init, pending = client.wait_for_id(1)
        events.extend([init, *pending])
        client.send({"jsonrpc": "2.0", "method": "initialized", "params": {}})
        client.send({"jsonrpc": "2.0", "id": 2, "method": "thread/start", "params": {"cwd": str(workdir), "approvalPolicy": "on-request", "approvalsReviewer": "user", "sandbox": "read-only", "ephemeral": True}})
        thread_response, pending = client.wait_for_id(2)
        events.extend([thread_response, *pending])
        thread_id = thread_response.get("result", {}).get("thread", {}).get("id")
        if not thread_id:
            raise RuntimeError(f"thread/start failed: {thread_response}")
        client.send({"jsonrpc": "2.0", "id": 3, "method": "turn/start", "params": {"threadId": thread_id, "input": [{"type": "text", "text": PROMPT}]}})
        turn_response, pending = client.wait_for_id(3)
        events.extend([turn_response, *pending])
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            try:
                message = client.lines.get(timeout=0.2)
            except queue.Empty:
                continue
            events.append(message)
            method = message.get("method", "")
            if method == "item/permissions/requestApproval":
                approvals.append({"method": method, "decision": "grant_for_turn_only", "persistent_amendment": False})
                client.send({"jsonrpc": "2.0", "id": message["id"], "result": {"permissions": {"fileSystem": None, "network": None}, "scope": "turn", "strictAutoReview": True}})
            elif method == "mcpServer/elicitation/request":
                approvals.append({"method": method, "decision": "accept_for_this_request", "persistent_amendment": False, "server": message.get("params", {}).get("serverName"), "tool": message.get("params", {}).get("_meta", {}).get("tool_params")})
                client.send({"jsonrpc": "2.0", "id": message["id"], "result": {"action": "accept", "content": {}}})
            elif method == "item/commandExecution/requestApproval":
                approvals.append({"method": method, "decision": "decline"})
                client.send({"jsonrpc": "2.0", "id": message["id"], "result": {"decision": "decline"}})
            elif method == "item/fileChange/requestApproval":
                approvals.append({"method": method, "decision": "decline"})
                client.send({"jsonrpc": "2.0", "id": message["id"], "result": {"decision": "decline"}})
            if method == "turn/completed" or message.get("type") == "turn.completed":
                turn_completed = True
                break
        status = "completed" if turn_completed else "timeout"
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    finally:
        client.close()
    db_events = []
    if db.exists():
        connection = sqlite3.connect(db)
        connection.row_factory = sqlite3.Row
        db_events = [dict(row) for row in connection.execute("select id, author, text, kind, idempotency_key from events order by id")]
        connection.close()
    summary = {
        "status": status,
        "error": error,
        "server_initialize_ok": any(message.get("id") == 1 and "result" in message for message in events),
        "mcp_tool_markers": [message for message in events if "mcp" in json.dumps(message).lower() or "room_post" in json.dumps(message)],
        "approvals": approvals,
        "room_events": db_events,
        "bypass_flags_used": False,
        "persistent_policy_amendment": False,
        "idle_wake": "not tested",
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "codex-appserver-result.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0 if status == "completed" else 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", required=True)
    parser.add_argument("--out", type=Path, default=Path("artifacts/m0/live-mcp"))
    args = parser.parse_args()
    if args.confirm != "LIVE_APPSERVER_MCP":
        parser.error("refusing to run without --confirm LIVE_APPSERVER_MCP")
    return run(args.out)


if __name__ == "__main__":
    raise SystemExit(main())
