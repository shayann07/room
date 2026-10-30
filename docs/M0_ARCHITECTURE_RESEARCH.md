# M0 architecture research: broker first, MCP as an adapter

## Finding

Room should use one local coordination broker as its control plane. MCP remains
an optional, narrowly scoped tool surface for an agent that is already in an
active turn. It must not be responsible for session lifecycle, provider wake,
quota handling, or task ownership.

This is a correction to the first M0 prototype, which used an MCP-shaped
stdio connector as the main live path. That connector is still useful as a
conformance fixture, but it is not sufficient as the product architecture.

## Evidence

- Codex publishes a bidirectional `codex app-server` JSONL protocol for rich
  clients, including conversation history, approvals, and streamed events.
  The official implementation and protocol are in
  [openai/codex app-server](https://github.com/openai/codex/tree/main/codex-rs/app-server).
  Room's bounded probe verified one host-mediated MCP delivery through this
  protocol without changing persistent approval policy.
- Claude Code documents `--print`, JSON output, and `--resume`/`--continue`.
  Those are session invocation/resumption controls, not a provider wake API.
  See the [Claude CLI reference](https://docs.anthropic.com/en/docs/claude-code/cli-usage).
  Claude's current subscription limit is a classified provider stop; it must
  create a resumable handoff and replacement assignment, not stop the room.
- Antigravity documents MCP as a permissioned tool namespace. Unconfigured
  calls default to Ask, and exact rules such as `mcp(server/tool)` can be
  allowed. See [Antigravity permissions](https://antigravity.google/docs/cli-permissions).
  Room verified both the default denial and a narrowly approved `room_post`
  delivery. This proves permissioned active-turn use, not idle wake.

## Proposed control plane

```text
Room UI/API
    |
Local broker (SQLite journal + outbox + leases + capability registry)
    |-- Codex adapter: app-server JSONL, host-mediated approvals
    |-- Claude adapter: CLI/SDK invocation and resume, quota classifier
    |-- Antigravity adapter: CLI/session invocation, permission-aware MCP
    `-- MCP adapter: active-turn room_sync/post/wait only
```

The broker owns assignments, decisions, leases, checkpoints, receipts,
provider stop classification, and replacement routing. Adapters report facts;
they do not invent liveness or claim that a provider was woken.

## Why this is better

1. A quota hit becomes an event (`provider_stopped: quota`) and the scheduler
   can continue with an eligible agent using the saved checkpoint.
2. A provider that cannot be woken remains visibly queued with a reason. An
   active MCP wait can reduce latency, but it is never mistaken for a wake API.
3. Each provider uses its strongest supported interface instead of forcing all
   three through MCP's weakest common denominator.
4. The room can test coordination, routing, and recovery without spending model
   quota. Live calls are only conformance checks.
5. Approval policy stays outside Room. The broker can request a host-mediated
   approval, but it cannot bypass provider policy or silently change accounts.

## M1 implementation boundary

The next implementation should add an adapter contract and a broker loop:

- `AdapterCapabilities` declares active-turn delivery, resume, idle wake,
  cancellation, approval mode, quota classification, and platform.
- `Adapter.run(assignment, context)` returns structured lifecycle events and a
  checkpoint reference; it does not write directly to the room database.
- `Scheduler` consumes durable events and leases, chooses only an eligible
  adapter, and records `queued`, `started`, `stopped`, `handoff`, and `wake`
  outcomes.
- `room_mcp.py` stays behind `McpActiveTurnAdapter` and is tested as an
  optional integration. It is not used for scheduler-to-provider control.

No provider is currently proven to support automatic idle wake on this Windows
machine. That remains an explicit capability value, not an assumption.
