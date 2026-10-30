# Room Baton: the simple coordination design

Room is a shared project conversation, not an agent manager. The product's
job is to prevent context drift when the person changes which existing tool is
working on the project.

## The new idea

Every project has one **baton**: a small, signed, machine-readable record at
the top of the room that says who leads, what is currently assigned, which
decisions are binding, and what the next agent must do. The chat is the human
conversation; the baton is the part an agent must not reinterpret.

An agent connector performs the same four-step turn on every check-in:

1. Read the baton and messages after its cursor.
2. Acknowledge the current baton revision, or state a conflict.
3. Do work only inside its assignment and post progress/questions.
4. Propose a new baton revision when its part is complete.

The owner or appointed lead accepts baton revisions. A provider cannot silently
rewrite the plan by starting a new session.

## Why this solves the actual problem

When Claude reaches its weekly limit, the baton remains valid. Codex sees the
same lead decision, assignment boundaries, unanswered questions, and latest
verified progress. It does not receive a prose handoff and does not need Room
to start a new Codex project. When Claude returns, it reads the newer baton
revision before acting and must reconcile any changes.

The design uses no fourth LLM. Lead authority is a role held by one of the
existing participants. If the lead is unavailable, Room can mark the lead
seat unavailable and the owner can appoint Codex or Antigravity for the same
bounded feature. That is an explicit authority change, not an invisible model
swap.

## Message types

The initial product needs only these typed messages:

- `charter`: project goal, constraints, acceptance criteria, owner
- `assignment`: recipient, scope, dependencies, baton revision, due condition
- `progress`: observed work and evidence links
- `question`: addressed to a role or participant; unanswered questions block
  only the affected assignment
- `decision`: proposal, impact, approver, revision
- `receipt`: check-in, acknowledgement, completion, quota, permission, crash
- `baton`: the compact current state, generated from the event log

Plain chat remains available, but only typed messages can change authority or
assignment state.

## Edge cases the baton handles

| Situation | Room behavior |
|---|---|
| Claude quota exhausted | Record `receipt/quota`; keep baton; mark Claude seat unavailable; leave assignment resumable. |
| Codex starts from an old session | Reject claim against an old baton revision; show the missing revision and preserve its draft. |
| Two agents claim the same work | One transactional claim wins; the other receives a conflict and cannot submit. |
| Agent says “done” without evidence | Completion stays proposed until the required receipt/evidence arrives. |
| Lead gives a new instruction in plain chat | Treat it as discussion until it becomes an accepted baton revision. |
| Agent returns after a week | Require a fresh check-in and current baton acknowledgement before new work. |
| Provider wakes unexpectedly | It can read and post, but cannot regain a lease without a current claim. |
| Network/process dies during a post | Idempotency key makes retry safe; the outbox reveals whether delivery was observed. |
| A decision changes mid-task | Increment baton revision; affected assignments become `needs-revalidate`, while unrelated work continues. |
| No provider is available | Keep the assignment queued with a concrete reason; never show “working.” |

## Connector strategy

Room exposes one local authenticated API with three operations:

```text
room.check_in(project, participant, cursor) -> baton + relevant messages
room.post(project, participant, typed_message, idempotency_key)
room.claim(project, participant, assignment, baton_revision)
```

Provider-specific connectors translate that API into the supported interface:

- Codex app-server or an active-turn MCP tool when available.
- Claude Code's documented CLI/session hooks and MCP tool surface.
- Antigravity's CLI/MCP connector under its explicit permission rules.

MCP is therefore a plug-in transport for `check_in`/`post`, not the authority
model, scheduler, or wake mechanism. The UI displays the room and baton only;
private provider session history remains private.

## Small implementation path

1. Add `baton`, typed messages, revision checks, and stale-claim rejection to
   the existing SQLite store.
2. Build a local web chat that renders the baton above the message stream.
3. Add simulated Claude/Codex/Antigravity connectors that check in, ask a
   question, receive an assignment, and survive a quota receipt.
4. Test one real active-turn connector at a time. Treat idle wake as an
   optional capability, never as a product promise.

This is smaller than a general orchestration platform and directly targets the
failure mode: the agents may change, but the project's authority and shared
conversation do not.
