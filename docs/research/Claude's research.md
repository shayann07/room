# Cross-agent controller: source-reuse audit

Research date: 2026-10-30. Scope: research only; nothing was installed, run, or changed.

## 0. Limits of this audit (read first)

- I had web search and page fetch only. I could not clone repositories or run code or tests (the sandbox has no network). **Nothing below is 'Executed'.**
- Labels: **Code-seen** = I read a source snippet (mostly docs.rs at a pinned crate version). **Documented** = READMEs, official docs, vendor staff forum replies. **Inferred** = my judgment.
- I could not obtain commit-pinned GitHub permalinks with line numbers. The pins I do have are in section 9. Reliability claims for the big orchestrators (Bernstein, Agent Orchestrator) are **Documented only**.
- Not fetched: Google's primary Antigravity FAQ page and the current Anthropic Agent SDK billing page after its June 2026 pause. Both matter (section 5).

## 1. Findings and recommendation

**Closest existing things (verified at doc level):**

- **Bernstein** (Apache-2.0, Python): deterministic scheduler, git worktrees, a 'janitor' verifier, heartbeat/crash reaping, WAL recovery, HMAC audit log, 40+ CLI adapters. Closest to an execution-plus-verification core.
- **Composio Agent Orchestrator** (MIT, TypeScript): plugin slots for agent/runtime/tracker/SCM, CI-failure and review-comment 'reactions'. Strong on PR lifecycle, weak on authority and durable decisions.
- **thirdshift** (Rust): issue-to-PR factory with a harness adapter trait covering Claude Code, Codex and the Antigravity CLI; preserves work as a draft when it cannot stand behind it.
- **Agetor** (MIT): the lead you mentioned exists (alamops/agetor). It is a human-driven kanban, not a controller.

**Hard problems with credible reusable pieces:** provider adapters and protocols (ACP, Codex app-server, Claude stream-json), worktree isolation (commodity), merge gating on a self-hosted forge (shunt, gitea-mq, Forgejo branch protection), OS sandboxing (Anthropic sandbox-runtime), durable execution (DBOS, Temporal), rate-limit wake-ups (TaskWake design).

**Gaps nobody I inspected fills:** (1) a ledger separating proposal / approved decision / observed fact, (2) worker-immutable policy and verifier rules, (3) leases with fencing tokens enforced at the git/merge boundary, (4) a takeover protocol across providers (not transcript replay), (5) semantic-constraint review, (6) quota awareness for Antigravity (no machine-readable usage in headless mode).

**Biggest non-technical risk:** subscription terms. Google staff said on 2026-10-16 that wrapping `agy` inside third-party coding agents or applications is not supported on consumer plans (details in section 5). Anthropic's published position is that developers building products should use API keys. Whether a personal open-source controller counts is unresolved. Design the worker adapter so API-key mode is a first-class path.

**Judgment (Inferred):** compose, don't fork. Build a small controller core of your own (event log, authority, leases, takeover), and reuse adapters, protocol libraries, merge queue, sandbox and durable-execution library. Use Bernstein as a benchmark and spike target, not as the foundation, until section 8 experiments pass.

## 2. Landscape table

| Repo | Purpose / agents / integration | Evidence | License | Status | Main limits | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| alamops/agetor | Local kanban. Claude Code in tmux, JSONL transcript tailed; Codex via one-shot `codex exec`; later builds add Antigravity/Copilot/Cursor/Gemini (experimental, PR #256) | Documented (README read in full) | MIT | 255 commits, 65 stars; macOS primary, arm64-only CLI installer | Human decides Done. No sandbox. Boot reconcile kills tmux sessions and marks running rows orphaned (discards, not resumes). Approvals found by pane scraping (Claude) and stdout heuristics (Codex) | Design reference. Reject as foundation |
| chernistry/bernstein (PyPI: bernstein) | Deterministic Python orchestrator; .sdd/ file state; 40+ CLI adapters; janitor, gates, cross-model review, circuit breaker | Documented (readthedocs, PyPI) | Apache-2.0 | Solo-maintained. Same project appears under chernistry, sipyourdrink-ltd and a mirror; PyPI pages show inconsistent versions (1.4.16, 3.12.0, 3.14.159) | Provenance unclear. Docs say policy limits fail open by default and multi-worker WAL safety is experimental. Janitor signals are declared per task by the planner | Shortlist: spike |
| ComposioHQ/agent-orchestrator (AgentWrapper copy exists) | TS pnpm monorepo (\~30 packages); plugins: agent-claude-code, aider, codex, opencode; trackers GitHub/Linear/GitLab; tmux or process runtime | Documented (README, repo CLAUDE.md excerpt, third-party review) | MIT | \~7.3k stars; CLI v0.3.0 | No Antigravity plugin listed. Authority = GitHub PR/CI. CI retry reportedly twice then escalate (third-party review only) | Shortlist: reference for lifecycle/reactions |
| johannesjo/parallel-code | Desktop app; Claude Code, Codex, OpenCode, Copilot, Antigravity CLI in worktrees | Documented | MIT | \~1.1k stars | Human-driven; no durable decisions | Reference for agy handling only |
| BloopAI/vibe-kanban and forks | Rust (axum, SQLite); `crates/executors` per-agent protocol adapters | Documented | Apache-2.0 | Company shut down April 2026; last upstream commit 2026-04-24; forks unvetted | Pinned CLI versions are stale | Reference / possible bounded extraction of executors |
| Enderfga/claw-orchestrator | npm runtime: persistent sessions over Claude, Codex, agy, Cursor, OpenCode; MCP + ACP; maxBudgetUsd | Documented | Not checked | Tracks agy 1.1.13 to 1.1.15 | Session wrapper, no authority model | Evaluate adapter layer |
| thirdshift (crate) | Adapter trait for claude/codex/agy/grok/muse/opencode; issue-to-PR | Code-seen (adapter.rs 0.13.5; agy.rs 0.14.1) | Not checked | v0.14.1; Linux x86\_64 and macOS arm64 | GitHub-issue driven; single-shot | Design reference; license check pending |
| agentclientprotocol (spec, SDKs, registry, claude-agent-acp, codex-acp) | Editor-to-agent protocol; adapters for Claude, Codex, Gemini; registry lists Google's own Antigravity ACP server | Documented | Registry and claude-agent-acp: Apache-2.0. Google's agy ACP server: proprietary binary | Repos updated 2026-10-27/28 | Designed for editors; permission and session model not built for unattended handoff | Integrate via protocol |
| DBOS Transact | Durable execution library; Postgres; SQLite in .NET and Rust ports | Documented | MIT | Active | SQLite for Python/TS not verified; workflow code must be deterministic | Shortlist: depend, pending check |
| Temporal server | Durable execution; `temporal server start-dev` | Documented | MIT | Mature | Heavy for one user | Alternative |
| steveyegge/beads | Dependency-graph task tracker over Dolt; hash IDs; `bd update --claim` | Documented | MIT | v0.57.0 (Mar 2026) on pkg.go.dev | Agents write freely: no authority separation | Design reference / possible task store |
| rbtr/shunt, Mic92/gitea-mq | Merge queues for Forgejo/Gitea: required status, batching, bbolt checkpoints | Documented | Not checked | Active | Needs a forge | Shortlist: merge gate |
| anthropic-experimental/sandbox-runtime | OS sandbox: macOS Seatbelt, Linux bubblewrap, proxy network filter | Documented | Apache-2.0 | Research preview | Filesystem/network scope only | Depend |
| Mira190/TaskWake | Hook-driven wake on usage reset: Claude StopFailure hook, `codex exec resume` | Documented | Not checked | Small | Same-provider resume only | Design reference |
| txcript | Converts session transcripts between harnesses (Claude Code, Codex, others) | Documented | Not checked | v0.12.0 | Transcript is not a decision record; Antigravity not in the snippet I saw | Evaluate for evidence capture |

**Rejected:** codex-switch (rotates accounts to dodge limits); OpenCode-to-Claude-Max proxies and opencode-antigravity-auth plugins (credential reuse, against both vendors' stated terms); Antigravity-Manager style OAuth proxies; agy-usage (reads the Antigravity OAuth token and calls Google backends directly); awesome-list entries I did not open.

**Coverage boundary:** I did not systematically cover Emdash, Paseo, Superset, Orca, Crystal, Gas Town-style systems, Restate, Hatchet, Inngest, OpenHands, Zuul internals or policy engines (OPA/Cedar).

## 3. Source audits (doc-level; no cloned code)

### A. Codex app-server (strongest integration seam)

- **What:** JSON-RPC 2.0 server over stdio, WebSocket or Unix socket. Methods: `thread/start`, `thread/resume`, `thread/fork`, `turn/start`, `turn/steer`, `turn/interrupt`. Open source under openai/codex `codex-rs/app-server`. Schema generation: `codex app-server generate-json-schema`. (Documented + Code-seen constants in unified-agent-api-codex 0.3.5 `mcp/protocol.rs`.)
- **Failure handling:** `turn/completed` carries status completed, interrupted or failed with `codexErrorInfo` including `UsageLimitExceeded`; `account/rateLimits/updated` and `account/rateLimits/read` exist (docs commit cbee5eb8a4a9771edd4667ee696c7ada4bf3a7ca; t3code PR tests; codex-codes 0.128.1 type list).
- **Contrast:** `codex exec --json` error events carry only a message string, not `codexErrorInfo` (openai/codex issue 22570). Classify limits via app-server, not exec.
- **Evidence against:** issue 42559 (Sept 2026) shows ChatGPT-login runs failing with 404 on the responses route while account endpoints worked, so auth/path regressions happen. A PR (21250) makes thread permission profiles server-owned and immutable; I did not confirm it merged.
- **Left for us:** durable thread-id bookkeeping, approval policy, takeover prompts.

### B. Bernstein

- **What:** tick-loop orchestrator; heartbeat/crash/stall reaping (`core/agents/agent_lifecycle.py`); janitor (`core/quality/janitor.py`, docs cite `verify_task` at lines 80-97); gate plugins; approval gates between verify and merge (`core/security/approval.py`); file locks; task lifecycle kernel that rejects illegal transitions (`core/tasks/lifecycle.py`). Documented.
- **Pin:** PyPI attests bernstein 3.12.0 built from sipyourdrink-ltd/bernstein@021e0023fdc2512c635d5b0762866e3e871f244c.
- **Tests:** docs cite 44 tests for verification-nudge tracking; I did not inspect tests.
- **Against:** solo maintainer; identity/version confusion; 'fail-open defaults'; experimental multi-worker safety; janitor signals come from the planner's task definition, so a worker that can edit those files or tests can weaken them unless the verifier runs from a protected location (Inferred).
- **Left for us:** decision ledger, lease/fencing at the git boundary, cross-provider takeover, semantic review.

### C. Composio Agent Orchestrator

- **What:** worktree + tmux (or process) per agent; reactions route CI logs and review comments back to the owning agent; plugin registry in `packages/core`. Documented.
- **Against:** no Antigravity plugin seen; human decisions and approvals live in GitHub PR flow; I could not inspect crash recovery.
- **Use:** copy the plugin-slot idea and reactions model; do not adopt wholesale.

### D. Agetor

- **What:** Bun + SQLite; per-task worktree with base ref pinned to a SHA at creation; localhost API with per-launch bearer token; PreToolUse hook posts approvals to its API for Claude.
- **Design choice worth noting:** it drives interactive `claude` in tmux so usage stays on the subscription, at the cost of keystroke injection and transcript scraping (brittle; Inferred).
- **Left for us:** everything about authority, durability across restart, takeover.

### E. ACP stack

- **What:** protocol plus registry (index at cdn.agentclientprotocol.com/registry/v1/latest/registry.json). Registry has entries for Claude, Codex, Gemini and antigravity-acp. The Antigravity entry is Google's proprietary server binary, version 1.0.0, from an 20260818 release candidate. Documented.
- **Community alternatives:** agy-agent-acp (jameslunardi; notes its stream-json dependency is undocumented in `agy --help` at 1.1.7), agy-acp (shindgew; reads agy conversation DBs). Not endorsed.
- **Use:** one uniform seam, but it is editor-shaped: it does not give leases, handoff or authority.

### F. Antigravity integration cluster

- thirdshift `agy.rs` (0.14.1) uses `--output-format stream-json`, `--print-timeout`, `--conversation <id>`, and its tests assert the conversation id stays stable on resume (Code-seen, partial).
- safe-chains `targets/agy.rs` (0.221.0) documents `hooks.json` PreToolUse decisions allow/deny/ask/force\_ask; deny blocks, force\_ask forces a prompt, **allow does not grant** on agy 1.1.2, and agy fails closed on malformed decisions. The author says verified live on 2026-07-13 (Documented; second-hand).
- ShadowCode 0.31.0 release notes say agy print mode silently denied tool actions, so it moved to a local server instead (Documented).
- Early agy `-p` versions (1.0.0, 1.0.6) hung or dropped stdout without a TTY (GitHub issues 76 and 318); later wrappers track 1.1.x, fix status unverified.

### G. Merge gate

- Forgejo/Gitea branch protection (required status context, restricted pushes) plus shunt or gitea-mq: the queue sets its own required status and lets the forge's auto-merge land the PR. shunt configures protection so only the bot pushes staging branches and persists checkpoints in bbolt or Postgres. Documented. Needs repo-admin API access for the bot.

## 4. Component reuse map

| Capability | Candidate | Location | Reuse method | License notes | Confidence | Remaining gap |
| --- | --- | --- | --- | --- | --- | --- |
| Chat UI | Agetor/Parallel Code UIs; ACP clients | their repos | Design reference | MIT | Low | Chat to persistent task spec; not found |
| Planner (model) | Ours; Bernstein manager as reference | n/a | Independent | n/a | Low | Must emit specs, never schedule |
| Scheduler | DBOS or Temporal; Bernstein tick loop | libs | Depend (DBOS) | MIT | Medium | Leases, fencing, quotas |
| Claude adapter | Claude Agent SDK / `claude -p` stream-json; claude-agent-acp | docs; crates | Integrate via CLI/protocol | Claude Code is proprietary; claude-agent-acp Apache-2.0 | Medium | Billing path |
| Codex adapter | `codex app-server` | openai/codex | Integrate via protocol | Check LICENSE (not verified here) | High | Auth path for unattended runs |
| Antigravity adapter | `agy -p` stream-json; Google ACP binary | vendor | Integrate; no vendoring | Proprietary | Low | Terms, quota, reliability |
| Durable state | SQLite event log (ours) + DBOS checkpoints | n/a | Build + depend | MIT | Medium | Proposal/decision/fact schema |
| Task graph | Beads schema | steveyegge/beads | Design reference | MIT | Medium | Authority separation |
| Task ownership | Nothing found with fencing | n/a | Build | n/a | Low | Lease + fencing token checked by git hook |
| Workspace isolation | git worktrees (Agetor `worktree.ts`, AO) | repos | Reimplement | MIT | High | Dependency dirs, secrets |
| Policy enforcement | Claude/agy hooks; Codex sandbox; srt | docs; srt repo | Depend on srt; use hooks as defense in depth | Apache-2.0 | Medium | Controller-owned hook install |
| Verification | Bernstein janitor/gates as reference | `core/quality/` | Reference; run verifier from protected ref | Apache-2.0 | Medium | Semantic checks |
| Merging | Forgejo + shunt/gitea-mq | repos | Depend | Check each | Medium | Local-first install weight |
| Observability | Bernstein trace/audit; OpenTelemetry hooks for agy | docs | Reference | n/a | Low | Unified timeline |

**Interface mismatches (Inferred):** Codex exposes server-owned threads; Claude exposes file-backed sessions; agy exposes conversation ids plus on-disk transcripts. None share a resume format, so cross-provider takeover must restart from the task spec plus the git state, not transcripts. Bernstein's file-based `.sdd` state and an event-log database are different durability models; do not combine them.

## 5. Agent compatibility matrix

|  | Claude Code | Codex | Antigravity CLI (`agy`) |
| --- | --- | --- | --- |
| Programmatic launch | `claude -p`; Agent SDK wraps the binary | `codex exec`; `codex app-server`; `codex mcp-server` | `agy -p/--print`; Google ACP server |
| Structured stream | `--output-format stream-json --verbose`: system/init, assistant, user, `rate_limit_event`, result (Code-seen in claude-code 0.1.2 `stream.rs`); `system/api_retry` with error such as rate\_limit (Documented) | exec JSONL; app-server notifications | \`--output-format json |
| Resume | `--resume <id>`, `--continue`, `--fork-session` | `thread/resume`, `thread/fork`, `codex exec resume` | `--conversation <id>`, `--continue` |
| Unattended + approvals | Permission modes incl. dontAsk, auto, bypassPermissions; PreToolUse hook allow/deny/ask/defer; exit 2 blocks; defer pauses a headless run for later resume (changelog 2.1.91, via a mirror repo) | sandbox read-only/workspace-write/full-access; approval requests are server-to-client JSON-RPC | Default `request-review` prompts; hooks.json PreToolUse; `--dangerously-skip-permissions` mentioned by forum staff reply; print mode has had silent-deny reports |
| Cancel | Interrupt via SDK/signal (not verified here) | `turn/interrupt` | `--print-timeout`; kill process (other methods unknown) |
| Rate-limit detection | `rate_limit_event`, `api_retry`, StopFailure hook (TaskWake docs) | `UsageLimitExceeded`, `account/rateLimits/updated` | Exit code 3 plus AGY\_ERROR on stderr for model/API errors (one secondary source); no machine-readable usage in headless |
| Hooks | Rich (PreToolUse etc.) | `/hooks` lifecycle hooks exist; details unverified | `hooks.json`; fails closed |
| Auth / billing | OAuth for ordinary Claude Code use. Anthropic's legal page: product developers should use API keys and may not offer claude.ai login or route requests through Free/Pro/Max credentials for users. A June 15, 2026 plan to move `claude -p` and Agent SDK to a separate monthly credit is marked paused on the support page; current state unverified | ChatGPT sign-in or API key; `CODEX_API_KEY` for exec; third-party advice says API keys for unattended runs | Consumer login. Staff reply 2026-10-16: direct local scripts and CI using `agy -p` are fine; wrapping `agy` inside third-party coding agents or applications is not supported on consumer plans and can trigger suspension; recommends Gemini Enterprise or AI Studio key. Earlier replies (Sept to Oct) said spawning the official binary is fine; the later reply says it supersedes. Primary FAQ not fetched |
| Platform | macOS/Linux; Windows unverified here | Cross-platform; app-server ws/unix | Linux/macOS/Windows binaries listed in ACP registry |

**Antigravity naming:** Antigravity IDE (editor), Antigravity CLI `agy` (successor to Gemini CLI), an SDK, and Gemini CLI (legacy; sources disagree on whether it is retired or deprecated) are different products with different flags and policies. Treat them separately.

## 6. Failure scenarios

| Scenario | Existing code that helps | Gap |
| --- | --- | --- |
| Claude hits limit mid-edit | `rate_limit_event`/StopFailure for detection; TaskWake for same-provider wake; thirdshift 'preserve work, leave draft' | Controller must snapshot dirty tree to a WIP ref, record the evidence, and release the lease |
| Codex inherits partial work | Worktree + WIP ref; Codex `thread/start` with the task spec | Takeover prompt built from spec, decisions and diff, not transcript; no code found |
| Antigravity attempts unauthorized architecture change | Hooks (deny works), srt filesystem scope, protected branch | Semantic check needs a reviewer against approved decisions; mechanical import/dependency rules we write |
| Paused worker resumes after reassignment | Nothing found with fencing | Lease epoch checked by a server-side git hook; stale pushes rejected |
| Two workers change a shared interface | Worktrees; merge queues test against latest base | Declared file/interface ownership and dependency-aware scheduling |
| Controller crashes during merge | shunt persists queue checkpoints; DBOS checkpoints; Bernstein WAL (experimental) | Idempotent merge step keyed by task and commit; reconcile on restart |
| Worker claims success, tests fail | Bernstein janitor; verify-gated completion concept (an arXiv case study, not production evidence) | Workers submit; controller runs verifier |
| Tests pass but requirement violated | LLM review in Bernstein; cross-model review | Requirement-to-check traceability; human gate for approved-decision changes |
| Worker edits verification rules | Nothing structural found | Verifier config and CI definitions live in a protected ref the worker cannot push to; run as separate OS user |
| All providers unavailable | TaskWake-style waiters; Quesma's wrapper falls back by exit code | Queue persistently, continue unblocked work, notify; bounded retries |

**What each control actually prevents (Inferred):** model instructions (AGENTS.md, prompts) guide but can be ignored. In-harness hooks block tool calls only while installed and not bypassed, and a same-user worker can edit them. OS sandboxes bound filesystem and network reach but not bad code inside allowed paths. Git server-side hooks and branch protection with merge credentials the worker never holds are the first controls outside the model's reach. CI from a protected ref checks only what is encoded as a check.

## 7. Assembly options

**1. Fastest credible prototype: Bernstein spike.** Pin a release, run with our own decision ledger beside it, verifier run from a protected path, merge via local bare repo plus hook. Missing: ledger, fencing, takeover, agy trust. Costs: low. Risks: provenance, fail-open defaults, solo maintainer, adapter quality unverified.

**2. Strongest long-term: thin controller + adapters.** SQLite event log (ours) with DBOS (or Temporal) for step durability; adapters over Codex app-server, Claude `-p` stream-json/Agent SDK, `agy -p` or Google ACP; Forgejo + shunt/gitea-mq; srt sandbox; Beads-like schema. Missing: ledger, authority, leases, takeover, review. Costs: highest build, lowest lock-in. Risks: policy changes on subscription use; Forgejo install weight.

**3. Simplest local-first: git-native.** Bare integration repo with server-side update hook as authority; SQLite task table; shell supervisors with TaskWake-style wake; srt for workers. Missing: nearly all coordination, but it makes the enforcement boundary real from day one. Costs: lowest. Risks: grows ad hoc.

**Provisional recommendation:** start with option 3's enforcement boundary, grow into option 2, and run option 1 only as a time-boxed benchmark.

## 8. Small validation plan (you run; no production repos or accounts)

1. **Adapter probe** on a throwaway repo: for each CLI, force a failure and a rate-limit-like stop (fake binary for limits). Success: limit vs crash vs refusal classified from structured output only. Disqualify: agy requires terminal scraping. Resolves: adapter viability.
2. **Terms check:** ask Google and Anthropic in writing whether a single-user local open-source controller launching the official CLI counts as third-party use. Success: written yes. Disqualify: no, then API-key mode only for that vendor.
3. **Takeover drill:** kill a worker mid-edit, snapshot to a WIP ref, hand the task spec to a different provider. Success: completes without touching a frozen interface (mechanically checked). Disqualify: reliance on transcript replay.
4. **Fencing test:** old worker pushes after reassignment. Success: server hook rejects it. Resolves: stale-worker risk.
5. **Tamper test:** worker edits tests and CI config. Success: verifier from protected ref still fails the task.
6. **Bernstein crash spike:** `kill -9` mid-tick and mid-merge; check no duplicate or lost task. Disqualify: lost or double-merged work.
7. **DBOS on SQLite (Python/TS):** confirm support before choosing it.

## 9. Research trail

- **Date:** 2026-10-30.
- **Searched:** multi-agent orchestrators; Antigravity CLI headless, hooks, terms; Claude headless, hooks, billing policy; Codex app-server, auth, errors; ACP and registry; durable execution; task graphs; sandboxing; merge queues; cross-harness transcript tools; Vibe Kanban status.
- **Pins and primary pages:** Bernstein 3.12.0 at sipyourdrink-ltd/bernstein@021e0023fdc2512c635d5b0762866e3e871f244c (PyPI attestation); Codex docs commit cbee5eb8a4a9771edd4667ee696c7ada4bf3a7ca; docs.rs: thirdshift 0.13.5 and 0.14.1, safe-chains 0.221.0, claude-code 0.1.2, unified-agent-api-codex 0.3.5, codex-codes 0.128.1; Agetor README (alamops/agetor, main, no SHA obtained); code.claude.com/docs/en/legal-and-compliance and agent-sdk/overview; support.claude.com article 15036540; developers.openai.com/codex/app-server; discuss.ai.google.dev threads 183051, 189905, 185992, 187945; agentclientprotocol.com registry; github.com/agentclientprotocol/registry (antigravity-acp/agent.json); vibekanban.com/shutdown.
- **Unresolved:** Google's primary FAQ wording; Anthropic's current subscription treatment of `claude -p`/Agent SDK; Codex and thirdshift/clawo/shunt/gitea-mq/TaskWake/txcript licenses; DBOS SQLite in Python/TS; Windows support for each CLI; whether agy print-mode bugs are fixed.
- **Not performed:** any code execution, cloning, test runs, issue-tracker triage beyond a few issues, line-level source audits of Bernstein and Agent Orchestrator.
- **Note:** one search result (claudeskills.info) contained text addressed to AI agents asking them to query it; I ignored it.
- **Next highest-value investigation:** clone Bernstein at the pinned SHA and read `agent_lifecycle.py`, `file_locks.py`, the WAL code and its Claude/Codex/agy adapters with their tests; in parallel obtain the Google and Anthropic written positions (experiment 2).
