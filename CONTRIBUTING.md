# Contributing to Room

Room is being built as a local-first open-source project. The current code is
an M0 proof: it demonstrates durable room coordination, a disposable MCP-shaped
connector, and provider interface evidence. It is not a production connector
yet.

## Run the checks

From the repository root:

```powershell
python -m unittest -v
python mcp_preflight.py
python build_m0_report.py
```

The tests use simulated agents and local subprocesses. They do not register an
MCP server or change provider settings.

## Live provider tests

`live_smoke_runner.py` requires the explicit `--confirm LIVE_M0` argument. Do
not run it casually: a live turn can consume an existing subscription quota.
Never add API keys, rotate accounts, use bypass-permission flags, or register a
provider MCP server without an explicit user decision.

Raw provider transcripts, generated protocol dumps, local executable paths, and
runtime caches are intentionally excluded from Git. Commit redacted evidence
summaries instead.

The Windows registration helper is `scripts/register_room_mcp.ps1`. It supports
PowerShell `-WhatIf`; review its output before any real registration. Running it
without `-WhatIf` changes provider MCP configuration and requires an explicit
user decision.

After registration, the bounded native connector probe is guarded separately:
`python live_mcp_runner.py --confirm LIVE_MCP --provider codex` (or
`antigravity`).

## Design boundary

Keep the visual direction in `docs/room.html` intact. Coordination belongs in
ordinary software and durable state; Room should use connected agents when
reasoning is needed rather than introducing a fourth model.
