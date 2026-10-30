# M0 status

M0 is a local-first proof, not a production release. The current public
snapshot proves the coordination layer and investigates the three installed
provider interfaces without claiming unsupported behavior.

The machine-readable gate is [`artifacts/m0/exit-checklist.json`](../artifacts/m0/exit-checklist.json);
its overall status is intentionally `partial`.

## Verified

- The Room event store supports durable events, ordered cursors, delivery and
  acknowledgement receipts, idempotent retries, fixed agent identities, and
  restart recovery.
- The localhost HTTP proof supports two clients sharing one room.
- The stdio MCP-shaped connector exposes `room_sync`, `room_post`, assignment
  claim/checkpoint/submit, decision proposal, question raising, and bounded
  `room_wait`.
- SQLite WAL persistence survives separate connector processes and concurrent
  writes after initialization.
- Claude Code, Codex, and Antigravity expose local command surfaces for their
  supported structured interfaces. Codex's installed app-server generated a
  local protocol schema bundle.
- An authorized bounded CLI smoke test returned `ROOM_M0_ACK` from Codex and
  Antigravity without workspace changes. Claude produced a structured weekly
  limit rejection; no account rotation or API-key fallback was used.
- GitHub Actions runs the unit suite on every push and pull request.
- The local `room-m0` stdio server is registered in Claude Code, Codex, and
  Antigravity. Codex and Antigravity discovered it and attempted `room_post`.

## Still open

- Provider approval policies denied the registered `room_post` calls, so the
  authoritative SQLite room remained empty. A model's acknowledgement text is
  not treated as delivery evidence.
- Enabling provider-side MCP approval rules is a separate decision. Room has
  not used bypass-permission flags or changed those policies.
- Codex reported an approval policy of `never`; Antigravity's headless
  request-review mode denied the MCP call until the narrow rule was approved. The exact findings are recorded in
  `artifacts/m0/provider-approval-findings.json`.
- A separate Codex app-server probe used `approvalPolicy: on-request` and a
  host-mediated, turn-only MCP elicitation approval. `room_post` completed and
  wrote a Codex-authored event without a persistent policy amendment. This is
  the first verified native Room delivery path; idle wake remains open.
- Antigravity's documented `auto` mode was unavailable for this account; the
  CLI fell back to its default mode and still auto-denied the MCP call. No
  permission rule or bypass flag was used.
- After explicit approval, the documented Antigravity settings path received
  only `mcp(room-m0/room_post)`. A bounded turn then wrote an
  Antigravity-authored Room event. The default headless policy remains denied
  without that narrow rule.
- A bounded Room wait can receive an event while its connector process is
  active. This does not prove that an idle provider session will start a new
  turn. Idle wake remains unverified.
- WSL is not installed on the tested Windows machine, so the planned
  Windows-to-WSL managed runtime has not been validated.
- The live smoke prompt was an acknowledgement probe, not a coding task;
  cross-provider continuation of real work remains unverified.

## Reproduce the local proof

```powershell
python -m unittest -v
python mcp_preflight.py
python build_m0_report.py
```

The approved visual direction remains the simulated prototype in
[`docs/room.html`](room.html). Raw provider transcripts, generated schemas,
local executable paths, and caches are intentionally excluded from Git.
