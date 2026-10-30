"""Run the explicitly authorized, bounded M0 provider smoke test.

The command requires ``--confirm LIVE_M0`` so it cannot be started by an
accidental default harness run. It uses an empty disposable working directory,
never registers MCP, never uses bypass flags, and records stdout/stderr/status
without reading credentials.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


PROMPT = "Reply exactly ROOM_M0_ACK. Do not edit files, run shell commands, use MCP tools, or access the network."


def command_for(provider: str, workdir: Path):
    if provider == "claude":
        return [
            "claude", "-p", PROMPT,
            "--verbose", "--output-format", "stream-json",
            "--permission-mode", "dontAsk", "--permission-prompts", "none",
            "--no-session-persistence", "--disable-slash-commands",
        ]
    if provider == "codex":
        return [
            "codex", "exec", "--json", "--ephemeral", "--sandbox", "read-only",
            "--skip-git-repo-check", "--cd", str(workdir), PROMPT,
        ]
    if provider == "antigravity":
        return [
            "agy", "--output-format", "stream-json", "--mode", "plan",
            "--disable-slash-commands", "--print-timeout", "60s", "--print", PROMPT,
        ]
    raise ValueError(provider)


def snapshot(workdir: Path):
    result = {}
    for path in sorted(workdir.rglob("*")):
        if path.is_file():
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            result[str(path.relative_to(workdir))] = {"bytes": path.stat().st_size, "sha256": digest}
    return result


def run_one(provider: str, root: Path, timeout: int):
    workdir = (root / "workspaces" / provider).resolve()
    outdir = root / "results" / provider
    workdir.mkdir(parents=True, exist_ok=True)
    outdir.mkdir(parents=True, exist_ok=True)
    before = snapshot(workdir)
    argv = command_for(provider, workdir)
    started = datetime.now(timezone.utc).isoformat()
    timed_out = False
    environment = None
    auth_environment_sanitized = False
    if provider == "claude":
        # The live test is intended to exercise the existing Claude login, not
        # an accidentally inherited separately billed API-key path. Remove only
        # these variables from the child process; do not edit account settings.
        environment = os.environ.copy()
        removed = [key for key in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL") if key in environment]
        for key in removed:
            environment.pop(key, None)
        auth_environment_sanitized = True
    try:
        completed = subprocess.run(argv, cwd=workdir, env=environment, capture_output=True, text=True, timeout=timeout)
        returncode = completed.returncode
        stdout, stderr = completed.stdout, completed.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        returncode = None
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
    after = snapshot(workdir)
    (outdir / "stdout.txt").write_text(stdout, encoding="utf-8", errors="replace")
    (outdir / "stderr.txt").write_text(stderr, encoding="utf-8", errors="replace")
    record = {
        "provider": provider,
        "started_at": started,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "command": ["<prompt>" if arg == PROMPT else arg for arg in argv],
        "returncode": returncode,
        "timed_out": timed_out,
        "working_tree_before": before,
        "working_tree_after": after,
        "file_changes": before != after,
        "auth_environment_sanitized": auth_environment_sanitized,
        "structured_json_lines": sum(1 for line in stdout.splitlines() if _is_json(line)),
        "ack_text_seen": "ROOM_M0_ACK" in stdout,
        "interpretation": "provider process result only; Room delivery and idle wake require separate adapter evidence",
    }
    (outdir / "result.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record


def _is_json(line: str):
    try:
        json.loads(line)
        return True
    except (TypeError, ValueError):
        return False


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run the authorized M0 live smoke test")
    parser.add_argument("--confirm", required=True, help="must be exactly LIVE_M0")
    parser.add_argument("--provider", choices=["claude", "codex", "antigravity", "all"], default="all")
    parser.add_argument("--out", type=Path, default=Path("artifacts/m0/live-smoke"))
    parser.add_argument("--timeout", type=int, default=90)
    args = parser.parse_args(argv)
    if args.confirm != "LIVE_M0":
        parser.error("refusing to run without --confirm LIVE_M0")
    args.out.mkdir(parents=True, exist_ok=True)
    providers = ("claude", "codex", "antigravity") if args.provider == "all" else (args.provider,)
    records = [run_one(provider, args.out, args.timeout) for provider in providers]
    run_record = {"prompt": PROMPT, "records": records}
    (args.out / "run.json").write_text(json.dumps(run_record, indent=2), encoding="utf-8")
    with (args.out / "run-history.jsonl").open("a", encoding="utf-8") as history:
        history.write(json.dumps({"recorded_at": time.time(), **run_record}) + "\n")
    print(json.dumps(records, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
