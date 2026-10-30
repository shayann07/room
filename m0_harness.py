"""Disposable, local-only M0 proof for Room.

This harness deliberately uses simulated participants. Its optional executable
probe invokes provider binaries only with ``--version`` and ``--help``; it never
starts a model turn or app-server session, reads credentials, or makes network
requests. Those probes are evidence about the local machine only, not connection
tests.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class Participant:
    id: str
    provider: str
    interface: str
    executable: str
    simulated: bool = True
    help_tokens: tuple[str, ...] = ()
    help_argv: tuple[str, ...] = ("--help",)


PARTICIPANTS = (
    Participant("claude", "Claude Code", "claude -p / stream-json", "claude", help_tokens=("--input-format", "--output-format", "stream-json", "--resume")),
    Participant("codex", "OpenAI Codex", "codex app-server (JSON-RPC)", "codex", help_tokens=("app-server", "--listen", "stdio://", "generate-json-schema"), help_argv=("app-server", "--help")),
    Participant("antigravity", "Google Antigravity", "agy -p / stream-json", "agy", help_tokens=("--input-format", "--output-format", "stream-json", "--conversation", "--continue")),
)
AGENT_IDS = frozenset(p.id for p in PARTICIPANTS)


ADAPTER_PLANS = {
    "claude": {
        "candidate_interface": "Claude Code print mode with stream-json",
        "launch_argv": ["claude", "-p", "<ROOM_PROMPT>", "--input-format", "stream-json", "--output-format", "stream-json"],
        "resume_argv": ["claude", "--resume", "<SESSION_ID>"],
        "transport": "stdin/stdout NDJSON",
        "evidence": "local help output for launch/resume flags; no provider turn started",
        "wake": "unverified; a connector cannot infer that an idle native session will start a turn",
    },
    "codex": {
        "candidate_interface": "Codex app-server",
        "launch_argv": ["codex", "app-server", "--listen", "stdio://"],
        "resume_method": "thread/resume",
        "turn_method": "turn/start",
        "transport": "JSON-RPC over stdio",
        "evidence": "local app-server help for transport/subcommand; method names are research leads and not live-verified",
        "wake": "unverified; requires a live app-server lifecycle test",
    },
    "antigravity": {
        "candidate_interface": "Antigravity CLI print mode with stream-json",
        "launch_argv": ["agy", "--print", "--input-format", "stream-json", "--output-format", "stream-json"],
        "resume_argv": ["agy", "--conversation", "<CONVERSATION_ID>"],
        "transport": "stdin/stdout NDJSON",
        "evidence": "local help output for launch/resume flags; no provider turn started",
        "wake": "unverified; requires a live continuation/idle test",
    },
}


def dry_run_plans():
    """Return adapter commands without executing any provider process."""
    return [
        {"participant": p.id, "provider": p.provider, **ADAPTER_PLANS[p.id], "executed": False}
        for p in PARTICIPANTS
    ]


class Room:
    """Small durable event log with at-least-once delivery and idempotent ack."""

    def __init__(self, path: Path):
        self.path = path
        self.events = []
        self.outbox = {}
        self.idempotency = {}
        self.next_id = 1
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            self.events = data["events"]
            self.outbox = data["outbox"]
            self.idempotency = data.get("idempotency", {})
            self.next_id = data["next_id"]
            if not self.idempotency:
                self.idempotency = {
                    event["idempotency_key"]: event["id"]
                    for event in self.events
                    if event.get("idempotency_key")
                }

    def _save(self):
        self.path.write_text(json.dumps({"events": self.events, "outbox": self.outbox, "idempotency": self.idempotency, "next_id": self.next_id}, indent=2), encoding="utf-8")

    def post(self, author: str, text: str, kind: str = "message", recipients=(), idempotency_key: str | None = None):
        if idempotency_key and idempotency_key in self.idempotency:
            event_id = self.idempotency[idempotency_key]
            existing = next(event for event in self.events if event["id"] == event_id)
            if (existing["author"], existing["text"], existing["kind"]) != (author, text, kind):
                raise ValueError(f"idempotency key reused with different payload: {idempotency_key}")
            return existing
        event = {"id": self.next_id, "author": author, "text": text, "kind": kind}
        if idempotency_key:
            event["idempotency_key"] = idempotency_key
            self.idempotency[idempotency_key] = event["id"]
        self.next_id += 1
        self.events.append(event)
        for recipient in recipients:
            self.outbox.setdefault(recipient, []).append({"event_id": event["id"], "state": "queued"})
        self._save()
        return event

    def post_agent(self, participant_id: str, text: str, kind: str = "message", recipients=(), idempotency_key: str | None = None):
        """Post using a connector-bound identity; callers cannot choose an arbitrary author."""
        if participant_id not in AGENT_IDS:
            raise PermissionError(f"unknown agent identity: {participant_id}")
        return self.post(participant_id, text, kind, recipients, idempotency_key)

    def deliver(self, participant: str, connected: bool = True):
        if not connected:
            return []
        deliveries = self.outbox.get(participant, [])
        for item in deliveries:
            if item["state"] == "queued":
                item["state"] = "delivered"
        self._save()
        return [item for item in deliveries if item["state"] == "delivered"]

    def acknowledge(self, participant: str, event_id: int):
        for item in self.outbox.get(participant, []):
            if item["event_id"] == event_id:
                item["state"] = "acknowledged"
        self._save()


def capability_matrix():
    rows = []
    for participant in PARTICIPANTS:
        executable = shutil.which(participant.executable)
        probe = {"status": "not run"}
        if executable:
            try:
                version = subprocess.run([executable, "--version"], capture_output=True, text=True, timeout=10)
                help_result = subprocess.run([executable, *participant.help_argv], capture_output=True, text=True, timeout=10)
                help_text = help_result.stdout + help_result.stderr
                probe = {
                    "status": "help/version only",
                    "version": (version.stdout + version.stderr).strip().splitlines()[:1],
                    "help_argv": [participant.executable, *participant.help_argv],
                    "help_exit_code": help_result.returncode,
                    "help_tokens_seen": [needle for needle in participant.help_tokens if needle in help_text],
                    "help_tokens_missing": [needle for needle in participant.help_tokens if needle not in help_text],
                }
            except (OSError, subprocess.TimeoutExpired) as exc:
                probe = {"status": "probe failed", "error": type(exc).__name__}
        rows.append({
            **asdict(participant),
            "local_executable": bool(executable),
            "local_executable_path": executable,
            "local_probe": probe,
            "launch_test": "not run (M0 is local-only and simulated)",
            "room_participation": "simulated pass",
            "mcp_enrollment": "help surface observed; no configuration change",
            "active_turn_delivery": "unverified",
            "idle_wake": "unverified; no claim",
            "account_path": "not inspected",
        })
    return rows


def run(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    db = out_dir / "room-events.json"
    # A proof run is a fresh fixture. Restart recovery is exercised inside it;
    # rerunning the command must not append to an old fixture and change IDs.
    if db.exists():
        db.unlink()
    room = Room(db)
    receipts = []
    checks = {}

    owner = room.post("nawaz", "Implement the checkout change and keep the auth decision.", "assignment", [p.id for p in PARTICIPANTS], "assignment:checkout:v1")
    duplicate_owner = room.post("nawaz", "Implement the checkout change and keep the auth decision.", "assignment", [p.id for p in PARTICIPANTS], "assignment:checkout:v1")
    receipts.append({"event": owner["id"], "type": "owner_assignment", "state": "posted"})
    receipts.append({"event": duplicate_owner["id"], "type": "owner_assignment", "state": "deduplicated_retry"})
    checks["duplicate_assignment_deduped"] = duplicate_owner["id"] == owner["id"] and len(room.events) == 1
    for p in PARTICIPANTS:
        delivered = room.deliver(p.id)
        ok = any(x["event_id"] == owner["id"] for x in delivered)
        if ok:
            room.acknowledge(p.id, owner["id"])
        checks[f"assignment_ack_{p.id}"] = ok
        receipts.append({"event": owner["id"], "recipient": p.id, "state": "acknowledged" if ok else "missing"})

    reply = room.post_agent("claude", "Accepted. I will preserve the authentication decision.", recipients=("nawaz",))
    question = room.post_agent("codex", "Should the existing order endpoint remain unchanged?", "question", recipients=("claude", "nawaz"))
    visual = room.post_agent("antigravity", "I will review the mobile layout while implementation is in progress.", recipients=("nawaz",))
    receipts.extend([
        {"event": reply["id"], "recipient": "nawaz", "state": "queued", "kind": "message"},
        {"event": question["id"], "recipient": "claude", "state": "queued", "kind": "question"},
        {"event": question["id"], "recipient": "nawaz", "state": "queued", "kind": "question"},
        {"event": visual["id"], "recipient": "nawaz", "state": "queued", "kind": "message"},
    ])
    checks["agent_reply"] = reply["id"] == 2
    checks["agent_to_agent_question"] = question["id"] == 3
    try:
        room.post_agent("forged-agent", "I am actually Claude.")
    except PermissionError:
        checks["unknown_agent_identity_rejected"] = True
    else:
        checks["unknown_agent_identity_rejected"] = False
    checks["delivery_during_work"] = bool(room.deliver("nawaz"))

    idle = room.post("nawaz", "Continue when Codex is available.", "idle_delivery", recipients=("codex",))
    checks["idle_delivery_queued"] = any(x["event_id"] == idle["id"] and x["state"] == "queued" for x in room.outbox["codex"])
    receipts.append({"event": idle["id"], "recipient": "codex", "state": "queued", "kind": "idle_delivery"})
    checks["idle_wake"] = False  # Explicitly unverified; queueing is the safe behavior.
    disconnected = room.post("nawaz", "Review the mobile layout when your session returns.", "disconnect_delivery", recipients=("antigravity",))
    checks["disconnect_queues"] = (
        not room.deliver("antigravity", connected=False)
        and any(x["event_id"] == disconnected["id"] and x["state"] == "queued" for x in room.outbox["antigravity"])
    )
    receipts.append({"event": disconnected["id"], "recipient": "antigravity", "state": "queued_disconnected", "kind": "disconnect_delivery"})

    restarted = Room(db)
    checks["restart_recovers_events"] = len(restarted.events) == len(room.events)
    checks["restart_recovers_outbox"] = restarted.outbox == room.outbox
    checks["restart_recovers_idempotency"] = restarted.idempotency == room.idempotency
    quota = restarted.post_agent("claude", "Provider limit reported; assignment remains queued for a supported replacement.", "quota_like_failure", recipients=("nawaz",))
    checks["quota_like_receipt"] = quota["kind"] == "quota_like_failure"
    receipts.append({"event": quota["id"], "recipient": "nawaz", "state": "queued", "kind": "quota_like_failure"})

    (out_dir / "capability-matrix.json").write_text(json.dumps(capability_matrix(), indent=2), encoding="utf-8")
    (out_dir / "receipts.json").write_text(json.dumps(receipts, indent=2), encoding="utf-8")
    (out_dir / "pass-fail.json").write_text(json.dumps(checks, indent=2), encoding="utf-8")
    (out_dir / "fixture-transcript.json").write_text(json.dumps(room.events, indent=2), encoding="utf-8")
    (out_dir / "dry-run-adapter-plans.json").write_text(json.dumps(dry_run_plans(), indent=2), encoding="utf-8")
    (out_dir / "account-path-findings.json").write_text(json.dumps([
        {
            "participant": p.id,
            "local_executable_path": shutil.which(p.executable),
            "finding": "Not inspected. The harness does not read credential stores, environment secret values, or provider account state.",
            "next_safe_test": "User-authorized disposable runtime test using the provider's own login/session.",
        }
        for p in PARTICIPANTS
    ], indent=2), encoding="utf-8")
    (out_dir / "donor-license-ledger.json").write_text(json.dumps([
        {"component": "Room M0 harness", "source": "new code", "license": "MIT (project-intended; confirm project license before release)", "copied_code": False},
        {"component": "Provider CLIs", "source": "local executable probes only", "license": "provider terms apply; no code vendored", "copied_code": False},
    ], indent=2), encoding="utf-8")
    return checks


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run Room's disposable M0 simulated proof")
    parser.add_argument("--out", type=Path, default=Path("artifacts/m0"))
    parser.add_argument("--dry-run", action="store_true", help="Print adapter plans without running the simulated room")
    args = parser.parse_args(argv)
    if args.dry_run:
        print(json.dumps(dry_run_plans(), indent=2))
        return 0
    checks = run(args.out)
    failed = [name for name, passed in checks.items() if not passed and name != "idle_wake"]
    print(json.dumps({"checks": checks, "idle_wake": "UNVERIFIED", "failed": failed}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
