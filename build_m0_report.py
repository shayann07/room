"""Build a capability matrix from existing M0 evidence; never launches providers."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).parent
ARTIFACTS = ROOT / "artifacts" / "m0"


def load(name):
    return json.loads((ARTIFACTS / name).read_text(encoding="utf-8"))


def build():
    local = {row["id"]: row for row in load("capability-matrix.json")}
    live = {row["provider"]: row for row in load("live-smoke/live-provider-results.json")["providers"]}
    preflight = load("mcp-preflight.json")
    platform = load("platform-findings.json")
    participants = []
    for participant_id in ("claude", "codex", "antigravity"):
        participants.append({
            "id": participant_id,
            "provider": local[participant_id]["provider"],
            "local_interface": local[participant_id]["local_probe"],
            "live_cli_turn": live[participant_id],
            "room_mcp_preflight": {
                "passed": preflight["status"] == "pass",
                "registered_with_provider": False,
            },
            "idle_wake": "unverified",
        })
    return {
        "status": "M0 evidence matrix; native registration and idle wake remain open",
        "participants": participants,
        "room_proof": {
            "simulated_lifecycle": "pass",
            "sqlite_wal_preflight": preflight["status"],
            "native_room_connector": "not registered",
        },
        "platform": platform,
        "limits": [
            "Live smoke turns prove provider CLI participation only; they do not prove native Room delivery.",
            "Claude was rate-limited, so no Claude acknowledgement was available.",
            "Idle wake requires a separate supported runtime experiment.",
        ],
    }


if __name__ == "__main__":
    matrix = build()
    (ARTIFACTS / "capability-matrix-live.json").write_text(json.dumps(matrix, indent=2), encoding="utf-8")
    print(json.dumps(matrix, indent=2))
