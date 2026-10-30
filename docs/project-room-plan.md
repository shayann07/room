# Project Room — product and engineering plan

Planning baseline v1 • 30 October 2026 • Owner: Nawaz

Working title only; naming and trademark checks are deferred. This document plans a new open-source product. No product code, installation, account connection, or repository changes have been performed.

## 1. The product we are building

A persistent project group chat where Nawaz, Claude Code, Codex, and Antigravity can discuss work, receive assignments, coordinate changes, and retain decisions across sessions. The room is the primary interface. Tasks, evidence, previews, and decisions are objects inside the conversation, with optional views alongside it. The convergence kernel compiles authoritative room state into a small, hashed turn packet for each provider attempt; a private provider session is context, never the project source of truth.

The distinguishing behavior is that messages can cause durable, authorized work. The system records who issued an instruction, what it authorizes, which agent accepted it, what changed, and what evidence supports completion. The project does not depend on one model remembering everything or acting as its permanent manager.

Product promise: **Say it once in the room. Preserve the decision. Keep the assignment moving. Show what actually happened.**

“Full authority” means authority over assignments, project policy, acceptance, and integration within the configured environment. It cannot mean overriding provider restrictions, forcing an unavailable model to run, or guaranteeing obedience to every sentence. The system must expose unsupported actions promptly and prevent unsupported claims of progress.

### Confirmed user decisions

- Build our own open-source product with our own interface and domain model; reuse verified components where appropriate.
- Group chat is central. A runner or task board by itself does not meet the request.
- Agents should communicate and stay current without Nawaz manually forwarding messages.
- Build, check, repair, and change workers automatically within approved scope; Nawaz accepts the final feature before integration.
- Subscriptions first. No automatic transition to separately billed APIs.
- Nawaz delegated platform and integration design choices; avoid more abstract configuration questions.

### Design decisions made here

- Room Link connectors under one room: a local authenticated HTTP/event protocol is the control plane; provider-specific sidecars translate native interfaces. MCP is historical compatibility only, never a product requirement.
- Windows-friendly browser UI first, backed by a Linux service through WSL2 for the first managed runtime. Native Windows agent participation remains a connector path. Do not silently move or convert existing repositories.
- One authoritative SQLite store, one scheduler, one integration authority. No combination of competing orchestration databases.
- New React/TypeScript UI; proposed Go service for storage, Room Link, and the browser API. Pin libraries only after small compatibility and licensing tests. Provider SDKs are optional adapter dependencies, never the authority store.
- Start with one user and one repository per room. Multiple rooms are supported without cross-project data leakage; cross-repository transactions are deferred.

## 2. The everyday experience

### Opening a project

Select a repository. The app inspects its branch, dirty state, instruction files, test commands, and installed tools without executing repository setup scripts. It shows a concise proposed project brief: purpose, current goal, constraints, and the agents it can connect.

If old chats or research are imported, they are evidence for proposed decisions, not automatic policy. Nawaz confirms a short baseline once. Conflicting instructions are surfaced with their origin. Missing tests are shown as missing, rather than inferred to pass.

Each native tool receives an individually scoped room connection and a setup test. The user completes provider authentication in the provider's own interface. The room never collects provider session tokens. Configuration changes are backed up and removable. Setup ends with each agent sending a real introduction and acknowledging a test instruction—not a fake avatar appearing online.

### Assigning work

Nawaz writes: “Claude, build checkout. Codex, review it. Antigravity, check the UI. Keep the current auth system.”

The room creates one feature thread with linked assignments, the protected authentication decision, and a compact interpretation of the request. Explicit instructions authorize ordinary work within existing policy. A broad request that needs a new feature plan produces a compact plan card for approval, after which routine subtasks do not ask again.

An agent can ask another agent a question in that thread. Replies can be informational or proposals. A peer cannot rewrite Nawaz's decision, expand another agent's authority, or accept its own output. A delegated lead may allocate subtasks within a bounded feature grant. The role can move to another model.

### Following progress

The main room shows meaningful events: an assignment accepted, a question, a changed interface, a blocker, a provider switch, or a feature ready for inspection. Tool logs are collapsed. A side panel shows the current goal, decisions, and agents' exact activity.

Example system notice: “Claude stopped because of its limit. Codex is continuing checkout from the saved work. Authentication decision remains unchanged.” That notice is emitted only when a classified stop, saved snapshot, and accepted replacement assignment exist.

### Accepting a feature

The feature thread presents a working preview when the project supports one, the behavior changed, requirement-by-requirement evidence, unresolved concerns, and a diff on demand. Primary actions: **Accept**, **Request changes**, **Pause**.

Accept authorizes integration of the specific verified candidate. It does not deploy production, approve payments, or authorize unrelated future changes. If the candidate or relevant decision changes, acceptance becomes stale and the room explains why another check is required.

### Returning after a week

Nawaz sees “Since you were away”: accepted features, remaining work, decisions requiring attention, and current blockers. A returning agent receives its own scoped catch-up packet before it can claim or submit work. It does not restart the plan simply because it is Claude again.

## 3. UX specification

### Primary layout

- Left rail: projects, current feature threads, and unread decisions. No mandatory enterprise organization hierarchy.
- Center: project group chat with genuine agent identities and attributed system receipts.
- Right drawer: selected feature, approved decisions, preview, or evidence. Closed by default on small screens.
- Composer: ordinary text, @agent, @team, attachments, and optional “Discuss / Assign” intent control. Natural language remains the default; shortcuts are optional.
- Top strip: current goal, overall state, and Pause all. Agent details are available without filling the header with telemetry.

### Conversation objects

| Object | What the user sees | What it does |
|---|---|---|
| Assignment | Owner, outcome, state, next checkpoint | Creates versioned work within an authorization grant |
| Decision | Short statement, origin, who approved it | Binds relevant tasks until superseded |
| Proposal | Suggested change and impact | Requests a decision; does not alter policy |
| Question | Recommendation and two or three choices | Blocks only dependent work |
| Change receipt | What changed and who needs it | Distributes a durable update |
| Feature preview | Working result plus evidence | Lets Nawaz assess the actual behavior |
| Switch receipt | Previous agent, replacement, preserved state | Makes continuity visible |

### Presence that tells the truth

Track transport connection, native host availability, active turn, and assignment progress separately. Display states such as Ready, Working, Catching up, Waiting for input, Limit reached, Disconnected, and Needs native resume.

Message states are Queued, Delivered to connector, Included in agent context, and Acknowledged. An acknowledgement proves a receipt, not understanding. Only evidence proves a task result. Never display “everyone knows” because a server accepted a broadcast.

### Interaction details

- @team discussion invokes a bounded review round, not an endless debate.
- Agent responses appear under their true tool/session identity. The coordinator never fabricates statements attributed to another agent.
- Default limit: one initial contribution and one follow-up per requested reviewer, then a consolidated open question if disagreement remains.
- Coalesce routine progress; urgent decision changes interrupt at the next supported safe boundary.
- Selecting a message reveals its task and decision links. “Why is this blocked?” shows the concrete cause and available next action.
- Feedback on a preview stays attached to that feature and the exact candidate revision.
- Support keyboard navigation, readable contrast, reduced motion, persistent drafts, scroll-position retention, and visible connection recovery.
- Use plain labels and real status text. No decorative typing when a provider has not produced activity. No invented percent-complete estimates.
- The app remains usable for reading and planning when every provider is unavailable.

## 4. What makes this more than a shared chat

### A. Instructions become work with receipts

A planner proposes structured commands from the owner's message; the server validates them against existing grants. The original message remains linked to every assignment. This removes the need for the user to re-authorize the same work inside several chats.

The server distinguishes user-origin instructions, delegated assignments, peer suggestions, and imported text. It never labels another agent's message as if Nawaz wrote it. Grants contain project, scope, expiry or completion boundary, permitted delegation, and policy revision. They cannot override vendor/system controls.

### B. Shared awareness with revision barriers

Every relevant decision, accepted interface change, reassignment, and evidence update advances a room event sequence. A routing index maps decisions and interfaces to affected tasks. A worker's context includes required decision revisions and its last processed event cursor.

Before claiming, submitting, or integrating work, the broker checks that the worker is operating against the applicable revisions. A stale worker receives the missing facts and a request to revalidate. Work on unrelated components can continue. Existing drafts are preserved.

This makes “stay updated” operational without sending the entire room transcript through every model on every turn. It cannot prove comprehension, so verification still checks the output.

### C. A durable seat for each responsibility

An assignment has a stable identity; model sessions are replaceable occupants. Planner, implementer, and reviewer are temporary roles, not fixed brands. A new worker inherits the approved outcome, relevant decisions, actual workspace snapshot, evidence, and outstanding requirements.

### D. Decisions have an impact preview

When an agent proposes replacing a database library, the room identifies affected features, interfaces, test baselines, and pending acceptance. Nawaz can see the likely disruption before approving it. Initial impact detection uses declared dependencies and file/import rules; later semantic indexing may improve coverage. It is not presented as exhaustive.

### E. A saved context packet for every run

Record the exact task and decision revisions, source event range, evidence links, and bounded summary supplied to a worker. Summaries are labeled derived and link back to original facts. This makes disagreements diagnosable: outdated context, ignored instruction, or insufficient test.

## 5. Connection and delivery architecture

The room service owns authorization, persistent messages, task transitions, and integration. Small connectors translate provider interfaces. The frontend is an ordinary client with no execution credentials.

### One shared room, several provider connectors

1. **Shared room:** the user creates the same project in each provider app. Room does not replace those projects, display their private sessions, or copy their repositories. It stores the common conversation and the authoritative project charter.
2. **Provider connector:** each provider gets a small Room Link sidecar that lets its existing session read relevant room messages and post updates, questions, proposals, and receipts through the same local API. The sidecar may use a native protocol or documented CLI hook internally.
3. **Lead coordination:** the user can appoint Claude (or another participant) as lead for a bounded project or feature. The lead interprets the approved request, assigns work in the room, answers agent questions, and keeps the plan current. Room records this authority; it does not invent a fourth manager model.

Room Link delivery does not claim to wake an idle model. Notifications are not universally fresh turns. A sidecar may be offline or a provider may reject a turn; reconnection must recover from the durable cursor.

### Adapter capability manifest

Each tested tool/version declares: room read/write, structured events, context injection, active-turn delivery, idle wake, resume, cancel, approvals, quota classification, sandbox support, account path, and platform. Unsupported fields are explicit. “Supported” is derived from a test result for a version/platform, not a brand-wide assumption.

### Delivery contract

- Durable outbox with ordered per-room event IDs and per-recipient delivery state.
- At-least-once delivery; idempotency keys deduplicate commands, acknowledgements, and receipts.
- Critical changes require acknowledgement of specific revisions; chat messages do not automatically invalidate work.
- Reconnect sends missing relevant events, not a full replay into the model prompt.
- Connector heartbeat proves liveness only; a task lease requires progress or explicit renewal under policy.
- Retry delivery without model calls when possible. No paid polling loop for presence.
- A task that cannot wake its recipient is visibly queued with a reason, not “working.”

### Room Link API

Keep the canonical connector surface small: `check-in`, `events`, `messages`,
and `claims`. Short-lived per-project connector tokens determine participant
identity; callers cannot choose their author ID. Provider sidecars use this API
and the durable outbox. An MCP bridge may be added later for compatibility,
but it is excluded from onboarding and capability requirements.

### Coordination contract

The Room service owns the project charter, assignments, decisions, questions,
and message history. Each connector implements only `read_since(cursor)`,
`post(event)`, and `presence/health` reporting. A provider is never shown as
online because its process exists; it must emit a verified message or receipt.

The room is not a generic task runner. It does not create competing sessions,
move files between agents, or pretend that one provider can wake another. It
keeps the shared reasoning and authority in one place while each provider
continues operating in its already configured project.

When a provider stops, Room records the reason in the conversation and marks
its assignments awaiting reassignment. The lead or user can assign the next
available participant from the same room context. Claude reaching a
subscription limit therefore leaves the plan and decisions intact; Codex or
Antigravity continues by reading the room, not by receiving a lossy handoff
written in a separate channel.

Owner approval and merge operations are not exposed to ordinary worker tokens. Shell/native tools remain outside the MCP broker unless independently sandboxed; an MCP allowlist does not secure those side channels.

## 6. Platform and runtime choices

First managed runtime: Linux through WSL2, with Windows browser access. This is a design choice to concentrate process and isolation testing on one execution platform while preserving a familiar UI. It requires a real device compatibility test, especially for native Windows Antigravity and WSL networking.

Store the authoritative database on the Linux filesystem. Do not share a SQLite file across Windows/Linux or network mounts. Native connectors communicate over authenticated local transport. Bind only locally, validate origin/host, reject arbitrary cross-origin requests, and scope tokens per room/participant. Never expose the service to the LAN by default.

Managed workspaces are created as explicit clones/checkouts separate from the user's original repository. Handle Windows paths, executable bits, case collisions, line endings, symlinks, and credential stores in onboarding. Never copy an entire home directory or all `.env` files into workers.

Package first as a local service and browser app; a desktop launcher follows after the room workflow works. macOS/Linux packaging and native Windows managed execution follow conformance testing. No cloud account, external message platform, Docker requirement, Redis, Temporal cluster, or mandatory forge is required for the initial product.

## 7. State and authority model

### Primary records

| Record | Important fields |
|---|---|
| Project / room | Repository identity, integration ref, owner, policy revision |
| Participant / session | Tool, role, connector, capability manifest, native session ID |
| Message / event | Sequence, authenticated author, origin type, thread, task, content hash |
| Decision | Proposed/approved/superseded, revision, approving user, affected scope |
| Feature / task | Goal, acceptance criteria, dependencies, scope, spec revision |
| Grant | Issuer, permitted actions, task scope, delegation boundary, validity |
| Attempt / lease | Task, owner, epoch, expiry, isolated workspace, event cursor |
| Checkpoint | Base SHA, snapshot manifest, artifact hashes, attempt epoch |
| Evidence | Candidate SHA, command/verifier version, exit result, logs, provenance |
| Acceptance | User, candidate SHA, decision and verifier revisions, evidence IDs |
| Integration intent | Expected base, tested result SHA, idempotency key, observed outcome |

Use transactional tables plus an append-only domain-event journal and durable outbox in the same database transaction. Do not attempt to replay every provider's hidden session state. Large logs/artifacts live in a content-addressed local store. Room text search can use SQLite FTS; vector storage is unnecessary initially.

Task lifecycle: draft → ready → leased → working → submitted → verifying → ready for owner → accepted → integrated. Explicit blocked, paused, cancelled, and rework states exist. Dependency checks and transitions are server validated.

### Authority boundaries

- Owner can approve policy, grants, and final candidates.
- Planner can propose tasks and decisions; permitted subtasks may be created inside an approved grant.
- Worker can read relevant state, post, claim eligible work, checkpoint, and submit.
- Reviewer can attach findings; cannot approve on the owner's behalf.
- Verifier supplies controller-observed receipts; product code runs with no room-administration or merge credentials.
- Integrator alone updates the protected integration reference.

Run controller/verification authority outside worker write access. For managed execution, test OS/user isolation and remove inherited administrator and repository-host credentials. Separate per-attempt clones are preferred at the strict trust boundary because ordinary worktrees share Git administrative state. Worktrees inside one trusted runtime are an optimization, not a security claim.

For agents connected from unconstrained native applications, room/merge authority remains enforceable only if protected remotely or through a separate OS identity. Do not promise host-level containment for an IDE running with the user's full permissions. Existing personal Git credentials may bypass local controls; onboarding must show the actual protection level and configure protected integration before claiming enforcement.

## 8. Switching workers without losing the project

1. Classify the interruption. Provider quota, authentication, permission denial, crash, user pause, and product-test failure are different events.
2. Block further submissions for the old attempt and increment the ownership epoch transactionally.
3. Interrupt/stop the old runtime where supported. Never assign a second worker to its live writable directory.
4. Quiesce writes and snapshot tracked modifications, staged state, allowed untracked files, deletions, binary files, modes, and relevant artifacts. Exclude secrets and generated caches by policy. A patch or `git stash create` alone is insufficient.
5. If quiescence cannot be proven, preserve the last stable checkpoint and label newer work uncertain. Do not claim a complete capture.
6. Create a new isolated attempt from the snapshot, or a known-good base plus recoverable work.
7. Compile the approved task, current decisions, relevant conversation, diff, evidence, and remaining requirements into the replacement's context.
8. Replacement acknowledges the revisions and checks the workspace before continuing. No automatic replan.
9. Publish a truthful switch receipt to the room. Later messages/submissions from the old epoch remain attributable but cannot mutate authoritative task state or integrate code.

Automatic routing chooses only available, capable, authorized providers within the user's account policy. Never silently select an API-key path. If none qualifies, preserve work and display the blocker. Resets are displayed in Pakistan time where a reliable reset time exists; unknown times remain unknown.

## 9. Verification and integration

Passing tests and semantic acceptance are different claims. A feature is ready only when its configured mechanical checks pass and required review findings are resolved. Nawaz's final acceptance remains required under the selected mode.

The controller runs a pinned verification manifest in a separate environment against the candidate. Workers may add legitimate product tests; they may not weaken the controller-owned acceptance suite, runner configuration, or required checks. Never indiscriminately replace all tests with old main: new features require new tests and sometimes approved baseline changes.

Record the exact source SHA, integration base, verifier revision, environment and dependency lock hashes, executed checks, exit codes, and missing coverage. Timeout, permission denial, skipped tests, and unknown exit states cannot count as passing. Untrusted build scripts run without merge credentials, controller database access, or arbitrary secrets.

For UI work, provide a preview with isolated test data and ports. For libraries/services, provide a runnable example or API behavior report. Previewing a product is not proof of its full correctness.

Serial integration initially: create a candidate atop the current integration head, verify that exact tree/commit, bind user acceptance to the resulting content, then update the protected ref using expected-old-value semantics. If the base changes, rebuild and reverify; material candidate changes require renewed owner acceptance. No speculative batching in v1.

Persist intent before external operations. After a crash, inspect actual local/remote refs and reconcile outcomes before retrying. Exactly-once effects are not assumed. Do not blindly delete Git lock files or abort another process's merge. Rollback is an explicit revert proposal and a new verification cycle, not destructive history rewriting.

## 10. Reuse strategy and research reconciliation

All four attachments were read. They provide leads, not proof of a tested stack. ChatGPT and Claude explicitly report no execution; Gemini's “Code-verified” labels do not provide reproduced tests here. Final Handoff contains placeholder pins such as `vX.Y`, future-dated text, and agent capability claims contradicted by the other reports. It is not the controlling specification.

Disagreements resolved in this plan:

- Structured protocol availability is checked against actual tool/version tests, not copied CLI flags from a report.
- MCP middleware governs its own exposed tools, not every native shell/file action.
- File reservations, process termination, task leases, and fencing are distinct controls.
- A durable chat log does not reconstruct hidden model reasoning or guarantee cross-provider continuation.
- Recovery is reconciliation, not unconditional rollback/retry.
- No assumption that a reliable merge system takes only a few hundred lines.
- No automatic bulk secret copying or writable hard-linked build directories across attempts.
- Research consensus does not establish subscription eligibility or license compatibility.

### Candidate component map

The pins and license descriptions below are attachment-reported leads unless explicitly identified as newly checked. Verify full revision, LICENSE/NOTICE, dependencies, relevant tests, and extraction boundaries before copying code.

| Component | Candidate / source | Intended reuse | Commitment |
|---|---|---|---|
| Session supervisor and delivery outbox | OrchestratorInc/agent-orchestrator, report pin `fe0550a`, Apache-2.0 reported | Bounded Go modules if separable; otherwise use designs and test scenarios | Preferred extraction spike; no full-product fork |
| Authority, evidence, acceptance | agent-sh/tower-crane, reported 0.1.7 / MIT | Extract small validated mechanisms into our single state model | No second JSON authority store |
| Atomic claims and race tests | DmarshalTU/coord, report pin `44fe390` / MIT | Adapt transaction and conformance-test patterns | No separate scheduler database |
| Stale-owner fencing | tasksmd/tasks.md, MIT reported | Reference claim semantics and build epoch checks into our broker | No Markdown source of authority |
| Proof bundles / verification | ystepanoff/awo, report pin `4475248` / MIT | Inspect bounded receipt and read-only review code | Reuse after tests |
| Subscription-native adapter lessons | alamops/agetor, report pin `0a2e636` / MIT | Inspect drivers and fixtures; prefer supported structured interfaces | No tmux/transcript dependency for core authority |
| Provider/backend separation | awslabs/cli-agent-orchestrator, report pin `261c5e1` / Apache-2.0 | Selected interface/error classification reference | Do not inherit bypass-permission defaults |
| Workspace setup | git-worktree-runner; worktrunk | Evaluate small helpers for safe allocation, cleanup, ports | Exclude bulk secret copying and mutable shared caches |
| Messaging/inboxes | MCP Agent Mail, newly discovered lead | Reference identities, acknowledgements, inbox patterns | Current LICENSE names an OpenAI/Anthropic rider; no copying or dependency adoption pending license review |
| Protocol implementations | Official provider interfaces and MCP SDK | Depend on tested, version-pinned protocol libraries | Native tool stays separately installed and licensed |

A new group-chat-focused research lead was necessary because the supplied audits emphasize runners. MCP Agent Mail documents inboxes, acknowledgements, and advisory reservations, but its current license is not simply unmodified MIT. Its code is not approved for reuse by this plan.

Avoid wholesale adoption of multiple orchestrators, rebranding a donor UI, or bundling proprietary agent binaries. Prefer a reusable component only when its tested behavior and maintenance cost beat implementing a small well-specified boundary ourselves. Keep provenance and tests for every extraction; preserve required notices.

## 11. Provider findings that affect scope

New primary-source checks on 30 October 2026:

- Google documents custom MCP servers for Antigravity IDE and CLI. This supports investigating native participation in the room. It does not prove idle wake-up or guarantee permission for every possible controller design.
- Google's FAQ distinguishes direct scripts/CI from consumer-plan wrapping of `agy` in third-party applications, which it says is unsupported. Do not implement a wrapper, GUI automation, or MCP loop as an asserted loophole. Native outbound access to room tools is a separately documented integration surface; validate our exact use and behavior.
- Anthropic's current legal page describes end-user sign-in to the unmodified Claude Code binary in hosted products under stated conditions, while restricting third-party credential collection/intermediation. Keep authentication in the official tool and validate the intended deployment/account path. Do not use an OAuth proxy.
- Antigravity headless docs describe structured output and continuation, but also soft-denied tools with an exit code of zero. Exit status alone cannot be a success gate.

Antigravity remains a first-class planned participant. The first engineering milestone must prove native room read/post/assignment acknowledgement and practical message delivery. Fully automatic idle wake on each provider is an explicit feasibility gate, not a promised capability. Failure does not justify silently replacing Antigravity with Gemini CLI or a Gemini API model.

## 12. Cost, attention, and bounded autonomy

- Subscriptions first; no separate model API spending enabled by default.
- Default maximum two simultaneous implementation attempts for a project; one active writer per task. Adjust after measuring local resource use and quota impact.
- Maximum two automatic repair cycles per submission, then a specific blocker. Infrastructure retries have separate bounded backoff and cannot erase repair counts.
- One reviewer by default. Additional opinions are user-requested or tied to a significant risk/decision.
- Local event routing, presence, queueing, scheduling, and receipts do not require model calls.
- Context packets contain relevant deltas and decisions, not every chat message. Critical decision text remains verbatim or directly retrievable; summaries cannot silently replace it.
- Show usage only when observed; distinguish provider-reported quota from estimates. No invented “tokens remaining.”
- A deadline changes prioritization and suggests scope reduction; it never silently drops checks or rewrites acceptance criteria.
- Pause all stops dispatch, revokes active authorization as appropriate, requests interruption, and records which processes actually stopped. It never claims immediate cancellation of an unknown external side effect.

## 13. Delivery roadmap and exit criteria

Use milestones with evidence, not a calendar promise before the connector spikes. The room workflow is tested first; attractive UI work must not mask an unworkable integration.

### M0 — Prove the group chat

Build only a disposable connector harness and minimal room, not the production application. Connect each real tool through its intended native/supported interface. Exercise an owner instruction, agent reply, agent-to-agent question, delivery during work, idle delivery, disconnect, restart, and quota-like failure using fixtures where live limits are unavailable.

Deliver: provider/platform capability matrix, account-path findings, message receipts, fixture transcripts, donor-license ledger, and pass/fail record. Test WSL ↔ native Windows access on Nawaz's chosen machine before committing packaging.

Exit: all three can participate in a real shared room and receive/acknowledge assignments; each unsupported wake behavior is documented. The full “no repeated native prompts” promise is blocked until every advertised participant passes wake tests. If it fails, bring one concrete UX tradeoff to Nawaz with a reproduction, not another abstract architecture question.

### M1 — A usable shared room

Implement participant identities, authenticated messaging, threads, persistent history, @mentions, durable inbox/outbox, read/acknowledgement states, relevance routing, and reconnect. Include one-command/one-action native enrollment where the host supports it, otherwise minimal guided setup.

Exit: agents exchange genuine messages; reconnect loses no accepted messages; duplicates do not create duplicate assignments; an offline agent is never shown as acting. Nawaz can direct the feature from one room.

### M2 — Instructions with authority

Add decisions, scoped grants, task revisions, dependencies, claims, epochs, mandatory catch-up, and authorization checks. Add bounded coordinator/planner behavior without making a specific model permanent.

Exit: stale claims, forged owner messages, peer self-approval, out-of-scope delegation, and attempts to change approved criteria are rejected. Ordinary work within an approved feature proceeds without repeated owner prompts.

### M3 — Work and seamless replacement

Add isolated attempts, checkpoints, supervisor lifecycle, supported managed adapters, quota/error routing, provider replacement, resume, and per-attempt evidence.

Exit: stop Claude mid-feature, continue with Codex, involve Antigravity through its validated connection, then reconnect Claude. The task/decision identity remains unchanged; no stale attempt can submit or modify the replacement's workspace. Dirty and untracked work survives where a stable snapshot was possible.

### M4 — Verified feature acceptance

Add protected verification, reviewer findings, feature previews, owner acceptance, serial integration, and recovery reconciliation.

Exit: false success, test tampering, stale acceptance, concurrent base movement, interrupted integration, and unknown external outcomes cannot falsely produce Done. Owner accepts a specific verified result in the room.

### M5 — Public alpha

Polish onboarding, uninstall/config rollback, accessibility, fast reconnect, backups/export, redaction, migration recovery, and actionable diagnostics. Publish contribution guide, adapter SDK, threat model, tested compatibility matrix, license/NOTICE inventory, and reproducible conformance suite.

Exit: a new user connects the supported agents without source edits; completes a representative feature and replacement drill; can restore a backup and understand every limitation in the advertised support tier.

### Later scope

Desktop packaging, remote/mobile access, team permissions, cross-repository work, richer preview annotations, routing based on observed project outcomes, and optional automated integration. Cross-repository work initially uses coordinated tasks, never claims an atomic multi-repository merge. Production deployment remains a separate explicit capability.

## 14. Engineering work boundaries

Proposed repository modules: `apps/web`, `cmd/roomd`, `internal/room`, `internal/authority`, `internal/scheduler`, `internal/storage`, `internal/supervisor`, `internal/workspace`, `internal/verification`, `internal/integration`, `connectors`, `protocol`, `tests/conformance`, and `docs/decisions`.

Freeze protocol/schema contracts before parallel implementation. Start with one agent implementing each subsystem and another reviewing a meaningful completed slice; do not launch a fleet to design incompatible state machines. Database migrations and authority transitions have one integration owner. Generated client types derive from a shared schema.

Initial implementation backlog: M0 evidence harness → message/event schema → storage/outbox → connector identity → native room sync/post → delivery receipts → room UI → assignments/grants → revision barriers → isolation/snapshot → replacement → verification/acceptance → integration/recovery.

Each issue must include its invariant, relevant prior decision, touched boundary, acceptance test, and excluded scope. Definition of done: tests appropriate to risk pass, user-visible states are truthful, provenance/license obligations are handled, and docs reflect actual behavior.

## 15. Test and product evaluation plan

Use deterministic fake adapters for timing/race/failure tests and a separate opt-in live-provider suite. Never consume an entire real quota to simulate exhaustion. Label simulated results separately from live evidence.

Required failure tests: duplicate and reordered messages; same-task claim races; outdated decision acknowledgement; stale session events; user/peer identity forgery; active MCP wait timeout; provider soft denial; disconnect mid-turn; late writes after reassignment; binary/untracked checkpoint recovery; verifier tampering; controller crash before/after dispatch; crash before/after integration; host sleep/resume; database migration failure; unknown provider version; local browser cross-origin request; secret redaction; isolation from other projects.

Compare baseline manual switching with the same tasks in the product. Record time to a verified feature, user interventions, rework after replacement, missed decisions, quota-consuming discussion turns, and recovery failures. Evaluate several representative tasks and languages; do not announce universal reliability from a single demo.

Acceptance targets for controlled tests: zero unauthorized or stale integrations; zero lost acknowledged room messages after tested restarts; no separate API charges initiated without explicit configuration; exact candidate/evidence binding for every accepted result. UX targets: routine assignment and final acceptance occur in the room; no copy/paste relay; relevant updates reach active agents at the next supported boundary; unsupported idle wake is visibly distinguished. Performance targets are provisional until a baseline device is measured.

## 16. Export, privacy, and maintenance

Export the room, decisions, assignments, grants, and evidence manifests as documented Markdown/JSON plus optional artifacts. Back up SQLite using a consistent backup mechanism and include schema version/artifact references. Retention is configurable; do not treat an unbounded transcript archive as free storage.

Collect no telemetry by default. Diagnostics exclude credentials and redact likely secrets, with user preview before sharing. Provider logs and message content remain local except when sent to selected participants as part of their authorized context. Deleting an agent disconnects its token and stops future delivery; historical attribution remains.

Pin supported adapter versions. Run conformance tests before upgrading. Unknown versions receive a compatibility warning and cannot silently inherit the highest assurance tier. Maintain an SBOM/provenance ledger and license notices for all vendored code. Proposed license for our original code: Apache-2.0, subject to compatibility review before release; no commitment to copy restricted upstream code.

## 17. What is settled and what needs evidence

Settled: shared group chat; actual agent participation; one authoritative room; owner-controlled decisions and final acceptance; automatic work within grants; subscriptions first; relevant update delivery; independent verification; our own UX and domain model.

Provisional implementation choices: Go/React/SQLite; WSL2 first managed runtime; exact donor modules; native hooks/extensions; managed adapter details.

Evidence gates: automatic wake in each actual host, subscription/account eligibility for the exact mode, WSL/native compatibility, OS isolation, donor license/NOTICE, crash recovery, and real provider replacement. These need experiments before product promises. No further user decision is required to complete this planning phase.

## Source register

Attached research used as local planning inputs:

- A: `ChatGPT's research.md` — pins, authority/gating candidates, structured adapters, and limitations.
- B: `Claude's research.md` — native protocols, subscription concerns, sandbox/merge distinctions, and evidence limits.
- C: `Gemini's research.md` — workspace/supervision ideas and candidate map; stronger claims downgraded where not demonstrated.
- D: `Final Handoff.md` — supplemental leads; contradictions/placeholders prevent treating it as final authority.

New targeted primary/documentation checks (30 October 2026):

- https://antigravity.google/docs/mcp — native custom MCP participation surface.
- https://antigravity.google/docs/faq — direct scripts versus consumer-plan application wrapping.
- https://antigravity.google/docs/cli/headless/ — structured events, continuation, and soft-denial behavior.
- https://code.claude.com/docs/en/legal-and-compliance — official binary/authentication distinctions.
- https://github.com/Dicklesworthstone/mcp_agent_mail — messaging reference, not an adopted dependency.
- https://github.com/Dicklesworthstone/mcp_agent_mail/blob/main/LICENSE — rider noted; license review required.

The fresh checks are documentation-level. This planning phase did not clone donors or execute their tests. Proposed product behavior is clearly separate from established upstream capabilities.
