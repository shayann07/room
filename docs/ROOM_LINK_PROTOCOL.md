# Room Link Protocol

Room should not depend on MCP. MCP is a useful ecosystem adapter, but it is a
poor foundation for a shared project chat: the model must choose to call a
tool, every client applies different approval rules, and a tool call does not
mean that a provider session is alive or listening.

Room Link is the product's canonical connector protocol.

## Shape

Room Link is deliberately boring:

```text
provider sidecar  <-- authenticated localhost HTTP/JSONL -->  Room service
                           |
                           `-- optional SSE event stream
```

The service exposes four operations:

```text
POST /v1/projects/{project}/check-ins
GET  /v1/projects/{project}/events?after={cursor}
POST /v1/projects/{project}/messages
POST /v1/projects/{project}/claims
```

Each request carries a short-lived per-project connector token, provider
identity, session identity, cursor, baton revision, and idempotency key. The
server authenticates the connector identity; the caller cannot select an
arbitrary author.

## Why it is better than MCP

- The room can deliver context before a model turn instead of waiting for a
  model tool decision.
- A provider adapter can use its strongest native interface: Codex app-server,
  Claude's JSON CLI/session hooks, or Antigravity's stream/CLI surface.
- One event contract works across providers without exposing the room as a
  random collection of model tools.
- Approval prompts for shell/file work remain provider concerns; posting a
  room message is a local connector operation with its own narrow token.
- The same API works for the browser UI, simulated agents, tests, and future
  desktop/mobile clients.
- Room can prove delivery from server receipts instead of trusting model text.

## Provider sidecars

Each sidecar is a small ordinary process, not another model:

1. Check in and receive the current baton plus messages since its cursor.
2. Add a compact `ROOM CONTEXT` block to the next provider turn.
3. Parse explicit structured output markers or provider events for progress,
   questions, receipts, and completion proposals.
4. Post those events to Room with an idempotency key.
5. Keep the cursor locally and recover from the durable server cursor after a
   crash or restart.

The sidecar never edits the repository, chooses an assignment, or changes
provider permissions. It only translates between a provider's supported host
interface and Room Link.

## Delivery and authority

Room Link is at-least-once. Every event has a server sequence, baton revision,
provider identity, session identity, and idempotency key. Claims are
transactional and require the current baton revision. A stale sidecar receives
the current baton and cannot post a completion for an old claim.

The event stream is a latency optimization, not a wake promise. If a sidecar
or provider is offline, the event remains durable and the room shows queued
work. A connector's heartbeat proves only that the sidecar is alive.

## First implementation

Room already has the beginnings of this protocol in `room_http.py`. M1 should
turn that proof into the canonical API, add SSE or long-poll cursors, and build
three sidecar shims:

- `room-link-codex`: app-server notifications and turn input/output;
- `room-link-claude`: documented JSON CLI/session invocation and output events;
- `room-link-antigravity`: stream-JSON CLI events and explicit permission
  reporting.

The existing `room_mcp.py` can remain as an optional compatibility bridge for
users who already have MCP configured. It must not appear in onboarding,
capability requirements, or the core product design.
