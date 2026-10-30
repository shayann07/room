"""Convert captured live smoke output into bounded Room evidence.

This script never starts a provider. It reads the already captured result files,
classifies the provider outcome, and records a clearly labelled local bridge
event. The bridge is not evidence of native MCP connectivity.
"""
from __future__ import annotations

import json
from pathlib import Path

from m0_harness import Room


PROVIDERS = ("claude", "codex", "antigravity")


def json_lines(path: Path):
    records = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            records.append(json.loads(line))
        except ValueError:
            continue
    return records


def classify(provider: str, result: dict, stdout: list[dict]):
    if provider == "claude":
        limited = any(
            item.get("type") == "rate_limit_event"
            and item.get("rate_limit_info", {}).get("status") == "rejected"
            for item in stdout
        ) or any(item.get("api_error") == "usage_limit_reached" for item in stdout)
        if limited:
            return "weekly_limit", "structured seven-day limit rejection; no provider acknowledgement"
    if result.get("returncode") == 0 and result.get("ack_text_seen") and not result.get("file_changes"):
        return "acknowledged", "provider returned ROOM_M0_ACK with no disposable workspace changes"
    return "failed", "provider did not produce a bounded acknowledgement"


def auth_observation(provider: str, result: dict, stdout: list[dict]):
    if provider == "claude":
        init = next((item for item in stdout if item.get("type") == "system" and item.get("subtype") == "init"), {})
        return {
            "child_auth_environment_sanitized": result.get("auth_environment_sanitized", False),
            "api_key_source": init.get("apiKeySource", "not observed"),
        }
    return {"child_auth_environment_sanitized": result.get("auth_environment_sanitized", False)}


def record(root: Path):
    summaries = []
    for provider in PROVIDERS:
        result_path = root / "results" / provider / "result.json"
        stdout_path = root / "results" / provider / "stdout.txt"
        result = json.loads(result_path.read_text(encoding="utf-8"))
        stdout = json_lines(stdout_path)
        status, explanation = classify(provider, result, stdout)
        summaries.append({
            "provider": provider,
            "status": status,
            "explanation": explanation,
            "returncode": result.get("returncode"),
            "timed_out": result.get("timed_out"),
            "structured_json_lines": result.get("structured_json_lines"),
            "ack_text_seen": result.get("ack_text_seen"),
            "file_changes": result.get("file_changes"),
            "provider_session_observed": bool(stdout),
            "auth_observation": auth_observation(provider, result, stdout),
            "source": "captured provider CLI output",
        })

    summary = {
        "evidence_scope": "one authorized bounded CLI turn per provider",
        "native_room_connector": "not used",
        "idle_wake": "not tested",
        "account_or_mcp_changes": False,
        "limit_handoff": {
            "old_provider": "claude",
            "old_status": next((p["status"] for p in summaries if p["provider"] == "claude"), "unknown"),
            "replacement_candidate": "codex",
            "controller_policy": "keep the assignment queued and allow a supported replacement candidate",
            "continuation_verified": False,
            "reason": "The smoke prompt was an acknowledgement probe, not a coding task, and no cross-provider task context was transferred.",
        },
        "providers": summaries,
    }
    (root / "live-provider-results.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    bridge_db = root / "live-room-events.json"
    if bridge_db.exists():
        bridge_db.unlink()
    room = Room(bridge_db)
    assignment = room.post(
        "nawaz",
        "Authorized M0 live smoke test; do not edit files or use tools.",
        "live_smoke_assignment",
        [p["provider"] for p in summaries],
        "live-smoke:assignment:v1",
    )
    bridge_receipts = [{"event": assignment["id"], "state": "recorded", "source": "local controller"}]
    for item in summaries:
        if item["status"] == "acknowledged":
            event = room.post_agent(
                item["provider"],
                "ROOM_M0_ACK (captured from the provider CLI).",
                "live_smoke_ack",
                ("nawaz",),
                f"live-smoke:{item['provider']}:ack:v1",
            )
        elif item["status"] == "weekly_limit":
            event = room.post(
                "system",
                "Claude reached its weekly provider limit. No acknowledgement was received; keep the assignment queued for a supported replacement.",
                "provider_limit",
                ("nawaz",),
                "live-smoke:claude:weekly-limit:v1",
            )
        else:
            event = room.post("system", f"{item['provider']} did not complete the bounded smoke test.", "provider_failure", ("nawaz",), f"live-smoke:{item['provider']}:failure:v1")
        delivered = room.deliver("nawaz")
        bridge_receipts.append({
            "event": event["id"],
            "provider": item["provider"],
            "state": "ingested_by_local_bridge" if any(d["event_id"] == event["id"] for d in delivered) else "not_delivered",
            "source": "captured provider CLI output; not native MCP",
        })
    (root / "live-bridge-receipts.json").write_text(json.dumps(bridge_receipts, indent=2), encoding="utf-8")
    return summary


if __name__ == "__main__":
    print(json.dumps(record(Path("artifacts/m0/live-smoke")), indent=2))
