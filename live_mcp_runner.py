"""Run an authorized bounded provider turn through the registered Room MCP."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).parent


def prompt_for(provider):
    return (
        f"Use the Room MCP tool room_post exactly once with text LIVE_MCP_ACK, "
        f"kind live_mcp_ack, idempotency_key live-mcp:{provider}:1, and recipients [nawaz]. "
        "Do not use any other tools, edit files, run commands, or access the network. "
        "After the tool call, reply exactly ROOM_MCP_TOOL_ACK."
    )


def command_for(provider, workdir):
    prompt = prompt_for(provider)
    if provider == "claude":
        return ["claude", "-p", prompt, "--verbose", "--output-format", "stream-json", "--permission-mode", "dontAsk", "--permission-prompts", "none", "--no-session-persistence", "--disable-slash-commands"]
    if provider == "codex":
        return ["codex", "exec", "--json", "--ephemeral", "--sandbox", "read-only", "--skip-git-repo-check", "--cd", str(workdir), prompt]
    if provider == "antigravity":
        return ["agy", "--output-format", "stream-json", "--mode", "plan", "--disable-slash-commands", "--print-timeout", "60s", "--print", prompt]
    raise ValueError(provider)


def snapshot(path):
    return {str(p.relative_to(path)): hashlib.sha256(p.read_bytes()).hexdigest() for p in path.rglob("*") if p.is_file()}


def run_one(provider, root, timeout):
    workdir = (root / "workspaces" / provider).resolve()
    outdir = root / "results" / provider
    workdir.mkdir(parents=True, exist_ok=True)
    outdir.mkdir(parents=True, exist_ok=True)
    before = snapshot(workdir)
    env = None
    if provider == "claude":
        env = os.environ.copy()
        for key in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL"):
            env.pop(key, None)
    started = datetime.now(timezone.utc).isoformat()
    timed_out = False
    try:
        result = subprocess.run(command_for(provider, workdir), cwd=workdir, env=env, capture_output=True, text=True, timeout=timeout)
        stdout, stderr, returncode = result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired as exc:
        stdout, stderr, returncode, timed_out = exc.stdout or "", exc.stderr or "", None, True
    after = snapshot(workdir)
    (outdir / "stdout.txt").write_text(stdout, encoding="utf-8", errors="replace")
    (outdir / "stderr.txt").write_text(stderr, encoding="utf-8", errors="replace")
    record = {
        "provider": provider,
        "started_at": started,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "returncode": returncode,
        "timed_out": timed_out,
        "file_changes": before != after,
        "room_post_marker_seen": "LIVE_MCP_ACK" in stdout,
        "tool_ack_seen": "ROOM_MCP_TOOL_ACK" in stdout,
        "mcp_server_marker_seen": "room-m0" in stdout or "room_post" in stdout,
        "auth_environment_sanitized": env is not None,
        "interpretation": "registered MCP integration result; idle wake remains separate",
    }
    (outdir / "result.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", required=True)
    parser.add_argument("--provider", choices=("claude", "codex", "antigravity", "all"), default="all")
    parser.add_argument("--out", type=Path, default=Path("artifacts/m0/live-mcp"))
    parser.add_argument("--timeout", type=int, default=90)
    args = parser.parse_args(argv)
    if args.confirm != "LIVE_MCP":
        parser.error("refusing to run without --confirm LIVE_MCP")
    args.out.mkdir(parents=True, exist_ok=True)
    providers = ("claude", "codex", "antigravity") if args.provider == "all" else (args.provider,)
    records = [run_one(provider, args.out, args.timeout) for provider in providers]
    summary = {"registered_server": "room-m0", "records": records, "idle_wake": "not tested"}
    (args.out / "run.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
