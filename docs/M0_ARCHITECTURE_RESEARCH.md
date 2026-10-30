# M0 architecture research: one project room, provider connectors

## Finding

Room should be one durable project conversation and authority layer. The three
existing provider projects remain where agents do their work. Connectors only
bring the shared room into those projects and return messages to it. MCP may be
one connector implementation, but it is not the product and it must not be
responsible for session lifecycle or provider wake.

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

## Proposed room model

```text
User + Room chat (charter, assignments, decisions, questions, updates)
    |
SQLite event log + durable cursors + authority rules
    |-- Claude project connector
    |-- Codex project connector
    `-- Antigravity project connector
```

Room owns assignments, decisions, questions, lead authority, and receipts.
Connectors report facts; they do not invent liveness or claim that a provider
was woken. Room does not expose private provider sessions in the UI.

## Why this is better

1. A quota hit becomes a room event (`provider_stopped: quota`). The lead or
   user can assign the next available agent, which reads the same authoritative
   conversation instead of receiving a lossy handoff.
2. A provider that cannot be woken remains visibly queued with a reason. An
   active MCP wait can reduce latency, but it is never mistaken for a wake API.
3. Each provider uses its strongest supported connector instead of forcing all
   three through MCP's weakest common denominator.
4. The room can test coordination, routing, and recovery without spending model
   quota. Live calls are only conformance checks.
5. Approval policy stays outside Room. The broker can request a host-mediated
   approval, but it cannot bypass provider policy or silently change accounts.

## M1 implementation boundary

The next implementation should add a connector contract and chat behavior:

- `Connector.read_since(cursor)` returns the room messages relevant to one
  provider project.
- `Connector.post(event)` writes authenticated updates, questions, decisions,
  and receipts; the provider cannot choose another author's identity.
- `LeadAuthority` records who may assign work, answer questions, and revise a
  bounded plan; owner approval remains separate.
- `room_mcp.py` stays as one optional connector. It is not used as a scheduler
  or session-control protocol.

No provider is currently proven to support automatic idle wake on this Windows
machine. That remains an explicit capability value, not an assumption.
