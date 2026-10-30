# Room implementation plan

This plan turns Room into a durable shared project room for Nawaz, Claude Code,
Codex, and Antigravity. The room owns coordination state; provider sessions
remain owned by their existing tools.

## Product boundary

Room must preserve the project's current plan when a provider reaches a quota,
crashes, or returns with stale context. It must let another approved agent
continue safely, while keeping the owner in control of decisions and final
integration.

Room does not promise to wake an idle provider, recover ungenerated model
thoughts, sandbox a native application running with the user's full Windows
identity, or replace provider authentication.

## Architecture

- **Room UI:** shared project chat, active plan, decisions, assignments,
  questions, evidence, provider status, and acceptance controls.
- **SQLite authority store:** append-only events, fencing epochs, sessions,
  tasks, leases, decisions, questions, receipts, and WIP references.
- **Room CLI:** local commands used by the UI, hooks, tests, and agents.
- **Provider adapters:** thin integrations into documented provider surfaces;
  no adapter owns authority or project truth.
- **Git recovery layer:** complete dirty-tree snapshots and isolated Windows
  worktrees for handoff.

## M0 — local authority and recovery proof

Status: lifecycle proof implemented; provider hooks not yet accepted as
production capabilities.

Deliverables:

- SQLite schema for epochs, sessions, tasks, leases, decisions, questions,
  receipts, and WIP snapshots.
- Write-ahead task intent and file-scope leases.
- Separate chat sequence from fencing epoch.
- Stale-session pulse/ack fence.
- Locked decisions and steward challenge flow.
- Complete WIP snapshot covering tracked, staged, untracked, deleted, binary,
  and executable-mode changes.
- Detached Windows-safe steward worktree.
- Simulated Claude quota → Codex continuation lifecycle.

Exit gate:

- The local lifecycle test passes repeatedly on Windows.
- A stale Claude session is rejected before Room-authorized mutation.
- Codex can continue from the exact WIP tree in a separate worktree.
- No test depends on a model call, API key, account rotation, or MCP.

## M1 — real Room UI and project initialization

Deliverables:

- Local browser UI following `docs/room.html`.
- `room init` creates `.room/`, database, owner identity, project charter,
  and reversible provider instruction templates.
- Chat, assignment, decision, question, receipt, and evidence views.
- Human actions: accept plan, appoint lead, transfer steward, resolve
  challenge, accept candidate, request changes, pause.
- Backup/export of Room state and safe recovery after process restart.

Exit gate:

- Two simulated agents and the owner can complete a full feature thread.
- Refreshing or restarting Room preserves all state.
- UI never labels unverified provider work as complete.

## M2 — connector contract and provider probes

Define one connector contract:

```text
check_in(session, cursor)
post(event, idempotency_key)
claim(task, epoch)
report(status, evidence)
```

For each provider, record a capability manifest with version, platform,
interface, approval behavior, active-turn delivery, resume, cancellation,
quota classification, and idle-wake result.

Verification order:

1. Claude: inspect installed hook contracts and prove prompt injection plus
   pre-tool denial with a no-file-change fixture.
2. Codex: test documented instruction loading, app-server or CLI integration,
   and safe worktree routing. Do not assume a pre-edit hook.
3. Antigravity: test the installed hook contract and permission behavior on
   Windows. Keep any allow rule exact and reversible.

Exit gate:

- Every supported capability has a reproducible test and evidence file.
- Unsupported capabilities are visible as unsupported.
- No provider account settings are changed without explicit approval.

## M3 — provider participation

Implement one provider at a time:

- connector check-in before a turn;
- current Room state injection;
- structured progress, question, blocked, stopped, and submitted receipts;
- idempotent posting;
- cursor recovery after connector restart;
- quota and permission failure classification.

Start with simulated providers, then run one bounded live smoke per provider.
The live prompt must prohibit repository changes and unrelated tool calls.

Exit gate:

- A real provider can read the room and post an authoritative receipt.
- A model acknowledgement without a Room receipt is not delivery evidence.
- Raw transcripts and local paths stay out of the public repository.

## M4 — handoff and stale-session protection

Deliverables:

- Human-confirmed `limit` flow and provider-stop receipts.
- Complete WIP capture before reassignment.
- Steward worktree creation from the captured ref.
- Locked-decision protection during continuation.
- Returning-session rebase/pulse/ack flow.
- Provider hook enforcement where verified.
- Commit gate and explicit warnings where hard enforcement is impossible.

Exit gate:

- Simulated Claude quota handoff passes for at least two consecutive runs.
- Codex and Antigravity cannot silently supersede an owner decision.
- A returning Claude session must rebase before it can claim or submit work.
- Windows worktree cleanup is safe and idempotent.

## M5 — feature acceptance and integration

Deliverables:

- Candidate evidence bundle: base SHA, candidate SHA, changed files, tests,
  decision revisions, and provider receipts.
- Owner acceptance becomes stale if the candidate, decision, or verification
  revision changes.
- Integration runs only after owner acceptance and current-head verification.
- Recovery from failed integration never loses the accepted candidate.

Exit gate:

- Owner can accept, request changes, pause, or reject a feature from Room.
- Room never merges or deploys merely because an agent says “done.”

## M6 — reliability and release hardening

Test:

- process crash during every SQLite transaction;
- concurrent claims and duplicate idempotency keys;
- database restart and WAL recovery;
- Windows path case, spaces, long paths, and file-mode limitations;
- dirty worktrees with untracked/binary/deleted files;
- provider output truncation and malformed hook JSON;
- connector timeout and reconnect;
- stale sessions and late receipts;
- permission denial and quota reset classification;
- backup restore and schema migration.

Release requirements:

- MIT-compatible dependency/license ledger;
- no credentials, raw provider logs, or machine paths in Git;
- documented uninstall and configuration rollback;
- reproducible local test command;
- capability matrix generated from evidence, not assumptions.

## Decision rules

- Prefer ordinary local software over model reasoning.
- Prefer existing subscriptions and documented provider interfaces.
- Keep MCP optional compatibility only; it is not a core requirement.
- Never use a passive chat message as authority when a typed event is needed.
- Never call a process alive because it exists; require a receipt.
- Never call work complete without evidence.
- Never let a stale session mutate current Room state.
- Never hide an unavailable or unverified provider behind a green avatar.

## First implementation queue

1. Move the lifecycle proof's state tables into the main SQLite backend.
2. Add durable baton/epoch/session/task/decision tables and migrations.
3. Add Windows-safe worktree cleanup and failure recovery tests.
4. Build the local Room UI around the approved HTML direction.
5. Add simulated provider connectors and the complete quota-handoff scenario.
6. Verify Claude, Codex, and Antigravity hooks independently.
7. Run only bounded live smoke tests after the local gates pass.
