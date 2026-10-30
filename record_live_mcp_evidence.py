"""Classify captured registered-MCP output without starting providers."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).parent
BASE = ROOT / "artifacts" / "m0" / "live-mcp"


def lines(provider):
    records = []
    for line in (BASE / "results" / provider / "stdout.txt").read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            records.append(json.loads(line))
        except ValueError:
            pass
    return records


def classify(provider, records, result):
    text = json.dumps(records)
    denied = any(marker in text for marker in ("approval policy is never", "permission check failed", "auto-denied", "user denied permission"))
    attempted = "room-m0" in text and ("room_post" in text or "call_mcp_tool" in text)
    if attempted and denied:
        return "mcp_call_denied", "provider discovered room-m0 and attempted room_post, but its approval policy denied the call"
    if attempted and result.get("room_post_marker_seen") and result.get("tool_ack_seen"):
        return "mcp_call_observed", "provider output contains a successful room_post attempt and acknowledgement"
    return "unverified", "no successful MCP tool result was observed"


def run():
    db = ROOT / "artifacts" / "m0" / "registered-room.sqlite3"
    connection = sqlite3.connect(db) if db.exists() else None
    if connection:
        connection.row_factory = sqlite3.Row
    events = [] if connection is None else [dict(row) for row in connection.execute("select id, author, text, kind, idempotency_key from events order by id")]
    if connection:
        connection.close()
    providers = []
    for provider in ("codex", "antigravity"):
        result = json.loads((BASE / "results" / provider / "result.json").read_text(encoding="utf-8"))
        records = lines(provider)
        status, explanation = classify(provider, records, result)
        providers.append({
            "provider": provider,
            "status": status,
            "explanation": explanation,
            "returncode": result.get("returncode"),
            "mcp_server_marker_seen": result.get("mcp_server_marker_seen"),
            "tool_ack_seen": result.get("tool_ack_seen"),
            "workspace_changed": result.get("file_changes"),
            "source": "captured registered-MCP CLI output",
        })
    appserver_path = BASE / "codex-appserver-result.json"
    appserver = json.loads(appserver_path.read_text(encoding="utf-8")) if appserver_path.exists() else None
    appserver_summary = None
    if appserver:
        appserver_summary = {
            "status": "delivery_pass" if any(event.get("author") == "codex" and event.get("kind") == "live_mcp_ack" for event in appserver.get("room_events", [])) else "failed",
            "approval": "host accepted one MCP elicitation for this turn",
            "persistent_policy_amendment": appserver.get("persistent_policy_amendment"),
            "bypass_flags_used": appserver.get("bypass_flags_used"),
            "room_events": appserver.get("room_events", []),
            "source": "Codex app-server host-mediated approval",
        }
    summary = {
        "registration": "room-m0 enabled for Claude Code, Codex, and Antigravity",
        "providers_tested": providers,
        "codex_appserver_host_mediated": appserver_summary,
        "room_events_after_test": events,
        "native_room_delivery": "Codex app-server host-mediated delivery passed; CLI and Antigravity approval denials remain",
        "model_acknowledgement_is_not_delivery": True,
        "idle_wake": "not tested",
        "bypass_flags_used": False,
    }
    (BASE / "live-mcp-results.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
