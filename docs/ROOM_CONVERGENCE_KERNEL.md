# Room Convergence Kernel

## The actual problem

The failure is not primarily that agents lack a chat transport. It is that
each provider treats its own hidden conversation as the source of truth. When
one provider disappears, another provider reconstructs the project from an
incomplete handoff, invents missing decisions, and slowly changes the plan.

Room must therefore make the project state portable and mechanically checkable.

## The kernel

Room becomes a deterministic **convergence kernel** between the chat and the
provider sessions:

```text
room events -> authoritative state -> turn packet -> provider session
       ^                                      |
       `--------- structured receipt --------`
```

The kernel is ordinary software. It does not reason, summarize creatively, or
select a model. It materializes state from an append-only event log and
compiles a small packet for the next turn.

## Turn packets

Every provider turn receives a packet containing:

- project charter and acceptance criteria;
- current plan revision and state hash;
- the assignment and its authority grant;
- binding decisions relevant to that assignment;
- unresolved questions addressed to this participant;
- relevant evidence and the last verified checkpoint;
- explicit prohibitions and out-of-scope actions;
- the required receipt schema.

The packet includes `room_revision`, `assignment_epoch`, and `packet_hash`.
Providers do not need the entire transcript. They need the exact current facts
that constrain their work.

## Receipts, not vibes

The provider connector must return one of these structured outcomes:

```text
accepted(packet_hash)
progress(packet_hash, evidence[])
question(packet_hash, target, question)
blocked(packet_hash, reason, retryable)
submitted(packet_hash, evidence[], requested_review)
stopped(packet_hash, category)
```

Free-form model text remains visible in chat, but it cannot advance assignment
state. A missing or malformed receipt is `unobserved`, not success.

## Authority without a model manager

Claude can be the lead in the conversation, but lead authority is a Room role,
not a property of Claude's hidden context. The owner grants a lead scope and
expiry. The kernel validates assignments and revisions. If Claude hits its
quota, the grant remains in Room and the owner can appoint Codex or Antigravity
to the same scope. The new lead receives the same packet family and cannot
rewrite prior decisions without an owner-approved decision event.

This is the important separation:

- models propose and execute;
- the kernel records and validates;
- the owner approves policy and integration.

No fourth LLM is needed.

## Assignment epochs

Every assignment has an epoch. A provider may post progress only for the epoch
it claimed. Reassignment increments the epoch. Late output from an old session
is retained as evidence but cannot mutate current state. This handles stale
Claude sessions, duplicate Codex sessions, unexpected provider wake-ups, and
agents returning after a week.

## Questions are first-class work

A question is not a chat message that may be forgotten. It has an owner,
target, blocking scope, decision deadline, and answer revision. The kernel
routes it to the current lead or owner. Unrelated assignments continue; only
the affected assignment becomes `waiting_for_answer`.

## Why this is better than a shared transcript

A transcript gives agents too much irrelevant history and still leaves them to
decide which statement is authoritative. The kernel gives them a compact,
verifiable state capsule. The chat remains the social interface, while the
capsule is the coordination protocol.

## Implementation order

1. Persist baton, assignments, decisions, epochs, packets, and receipts in the
   existing SQLite authority store.
2. Add a packet compiler that selects relevant events by assignment and decision
   dependency, then records the packet hash.
3. Add receipt validation and stale-epoch rejection.
4. Make Room Link deliver packets and receipts; connectors remain thin.
5. Build a simulated Claude-quota scenario: Claude accepts, stops with quota,
   Codex receives the next packet, asks a question, and resumes after the
   answer without changing the charter.
6. Only then test provider-specific delivery.

The success criterion is not “three tools can call Room.” It is: after any one
provider disappears, another provider can continue from the same authoritative
state and the returning provider cannot accidentally undo it.
