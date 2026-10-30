"""Disposable stdio MCP connector for the Room M0 proof.

This speaks the JSON-RPC shape used by MCP over stdin/stdout. It is a local
fixture server, not an authenticated production connector; the participant
identity is fixed when the process starts and cannot be selected per tool call.
It is intentionally not registered with any provider by this project.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from m0_harness import AGENT_IDS, Room
from room_sqlite import SQLiteRoom


SERVER_INFO = {"name": "room-m0-mcp", "version": "0.1.0"}
MCP_PROTOCOL_VERSION = "2025-06-18"


TOOLS = [
    {
        "name": "room_sync",
        "description": "Read durable Room events after an event cursor.",
        "inputSchema": {"type": "object", "properties": {"after": {"type": "integer", "minimum": 0}}, "additionalProperties": False},
    },
    {
        "name": "room_post",
        "description": "Post a message using this connector's fixed participant identity.",
        "inputSchema": {
            "type": "object",
            "required": ["text"],
            "properties": {
                "text": {"type": "string", "minLength": 1},
                "kind": {"type": "string"},
                "recipients": {"type": "array", "items": {"type": "string"}},
                "idempotency_key": {"type": "string"},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "question_raise",
        "description": "Raise a bounded question using this connector's fixed identity.",
        "inputSchema": {"type": "object", "required": ["text"], "properties": {"text": {"type": "string", "minLength": 1}, "recipients": {"type": "array", "items": {"type": "string"}}, "idempotency_key": {"type": "string"}}, "additionalProperties": False},
    },
    {
        "name": "assignment_claim",
        "description": "Claim an existing assignment by event id.",
        "inputSchema": {"type": "object", "required": ["assignment_id"], "properties": {"assignment_id": {"type": "integer", "minimum": 1}, "idempotency_key": {"type": "string"}}, "additionalProperties": False},
    },
    {
        "name": "assignment_checkpoint",
        "description": "Record a checkpoint for an existing assignment.",
        "inputSchema": {"type": "object", "required": ["assignment_id", "summary"], "properties": {"assignment_id": {"type": "integer", "minimum": 1}, "summary": {"type": "string", "minLength": 1}, "idempotency_key": {"type": "string"}}, "additionalProperties": False},
    },
    {
        "name": "assignment_submit",
        "description": "Submit a bounded result for an existing assignment; owner acceptance remains separate.",
        "inputSchema": {"type": "object", "required": ["assignment_id", "summary"], "properties": {"assignment_id": {"type": "integer", "minimum": 1}, "summary": {"type": "string", "minLength": 1}, "idempotency_key": {"type": "string"}}, "additionalProperties": False},
    },
    {
        "name": "decision_propose",
        "description": "Propose a decision; this does not approve or replace the owner's decision.",
        "inputSchema": {"type": "object", "required": ["statement"], "properties": {"statement": {"type": "string", "minLength": 1}, "affected_scope": {"type": "string"}, "idempotency_key": {"type": "string"}}, "additionalProperties": False},
    },
    {
        "name": "room_wait",
        "description": "Wait briefly for durable room events; it never claims to wake an idle provider.",
        "inputSchema": {"type": "object", "properties": {"after": {"type": "integer", "minimum": 0}, "timeout_ms": {"type": "integer", "minimum": 0, "maximum": 2000}}, "additionalProperties": False},
    },
]


class McpError(Exception):
    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code


class RoomMcp:
    def __init__(self, db_path: Path, participant: str, store: str = "json"):
        if participant not in AGENT_IDS:
            raise ValueError(f"unknown participant: {participant}")
        self.db_path = db_path
        if store not in {"json", "sqlite"}:
            raise ValueError(f"unknown store: {store}")
        self.store = store
        self.room = self._new_room(initialize=True)
        self.participant = participant

    def _new_room(self, initialize=False):
        return SQLiteRoom(self.db_path, initialize=initialize) if self.store == "sqlite" else Room(self.db_path)

    def refresh(self):
        close = getattr(self.room, "close", None)
        if close:
            close()
        self.room = self._new_room(initialize=False)

    def call(self, name: str, arguments: dict):
        self.refresh()
        if name == "room_sync":
            after = arguments.get("after", 0)
            if not isinstance(after, int) or after < 0:
                raise McpError(-32602, "after must be a non-negative integer")
            return {"events": [e for e in self.room.events if e["id"] > after]}
        if name == "room_wait":
            after = arguments.get("after", 0)
            timeout_ms = arguments.get("timeout_ms", 0)
            if not isinstance(after, int) or after < 0:
                raise McpError(-32602, "after must be a non-negative integer")
            if not isinstance(timeout_ms, int) or timeout_ms < 0 or timeout_ms > 2000:
                raise McpError(-32602, "timeout_ms must be between 0 and 2000")
            deadline = time.monotonic() + timeout_ms / 1000
            while True:
                self.refresh()
                events = [e for e in self.room.events if e["id"] > after]
                if events or time.monotonic() >= deadline:
                    return {"events": events, "waited": timeout_ms > 0, "timed_out": not bool(events)}
                time.sleep(0.025)
        if name in {"room_post", "question_raise"}:
            text = arguments.get("text")
            if not isinstance(text, str) or not text.strip():
                raise McpError(-32602, "text must be a non-empty string")
            recipients = tuple(arguments.get("recipients", ()))
            if name == "question_raise":
                kind = "question"
            else:
                kind = arguments.get("kind", "message")
            event = self.room.post_agent(self.participant, text, kind, recipients, arguments.get("idempotency_key"))
            return {"event": event, "author": self.participant}
        if name in {"assignment_claim", "assignment_checkpoint", "assignment_submit"}:
            assignment_id = arguments.get("assignment_id")
            if not isinstance(assignment_id, int) or assignment_id < 1:
                raise McpError(-32602, "assignment_id must be a positive integer")
            assignment = next((event for event in self.room.events if event["id"] == assignment_id and event["kind"] == "assignment"), None)
            if assignment is None:
                raise McpError(-32602, "assignment_id must reference an assignment event")
            if name == "assignment_claim":
                kind = "assignment_claim"
                text = f"Claimed assignment {assignment_id}."
            elif name == "assignment_checkpoint":
                kind = "assignment_checkpoint"
                text = f"Assignment {assignment_id} checkpoint: {arguments.get('summary', '')}"
            else:
                kind = "assignment_submit"
                text = f"Assignment {assignment_id} submitted: {arguments.get('summary', '')}"
            key = arguments.get("idempotency_key") or f"{kind}:{self.participant}:{assignment_id}"
            event = self.room.post_agent(self.participant, text, kind, ("nawaz",), key)
            return {"event": event, "author": self.participant, "owner_acceptance_required": name == "assignment_submit"}
        if name == "decision_propose":
            statement = arguments.get("statement")
            if not isinstance(statement, str) or not statement.strip():
                raise McpError(-32602, "statement must be a non-empty string")
            scope = arguments.get("affected_scope", "")
            text = statement if not scope else f"{statement} (scope: {scope})"
            key = arguments.get("idempotency_key") or f"decision-proposal:{self.participant}:{statement}"
            event = self.room.post_agent(self.participant, text, "decision_proposal", ("nawaz",), key)
            return {"event": event, "author": self.participant, "owner_approval_required": True}
        raise McpError(-32601, f"unknown tool: {name}")


def result(request_id, payload):
    return {"jsonrpc": "2.0", "id": request_id, "result": payload}


def error(request_id, code, message):
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def handle(server: RoomMcp, request: dict):
    method = request.get("method")
    request_id = request.get("id")
    if method == "initialize":
        return result(request_id, {"protocolVersion": MCP_PROTOCOL_VERSION, "capabilities": {"tools": {}}, "serverInfo": SERVER_INFO})
    if method == "notifications/initialized":
        return None
    if method == "ping":
        return result(request_id, {})
    if method == "tools/list":
        return result(request_id, {"tools": TOOLS})
    if method == "tools/call":
        params = request.get("params") or {}
        try:
            payload = server.call(params.get("name"), params.get("arguments") or {})
            return result(request_id, {"content": [{"type": "text", "text": json.dumps(payload)}], "structuredContent": payload, "isError": False})
        except McpError as exc:
            return error(request_id, exc.code, str(exc))
        except (TypeError, ValueError, KeyError) as exc:
            return error(request_id, -32602, str(exc))
    return error(request_id, -32601, f"unknown method: {method}")


def serve_stdio(db_path: Path, participant: str, store: str = "json"):
    server = RoomMcp(db_path, participant, store)
    try:
        for line in sys.stdin:
            if not line.strip():
                continue
            try:
                request = json.loads(line)
                response = handle(server, request)
            except (ValueError, json.JSONDecodeError) as exc:
                response = error(None, -32700, str(exc))
            if response is not None:
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
    finally:
        close = getattr(server.room, "close", None)
        if close:
            close()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run the disposable Room M0 stdio MCP server")
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--participant", choices=sorted(AGENT_IDS), required=True)
    parser.add_argument("--store", choices=("json", "sqlite"), default="json")
    args = parser.parse_args(argv)
    serve_stdio(args.db, args.participant, args.store)


if __name__ == "__main__":
    main()
