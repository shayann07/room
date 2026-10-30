# Cross-Agent Orchestration Architecture: Open-Source Source-Code Reuse Audit
**Research Date:** October 29–30, 2026  
**Auditor:** Senior Open-Source Systems Researcher  
**Target Agents:** Anthropic Claude Code, OpenAI Codex CLI, Google Antigravity CLI  
**Objective:** Discover, inspect, grade, and map existing inspectable open-source components to build a persistent, authoritative, durable cross-agent project control system.

---

## 1. Findings and Architectural Recommendations

### 1.1 Executive Summary
Developers using frontier coding agents (Claude Code, OpenAI Codex, and Google Antigravity) across real-world repositories face severe operational friction when switching between agents upon reaching quota and rate limits. The incoming replacement agent lacks grounding in previous architectural decisions, misinterprets uncommitted or partially staged edits, re-implements already rejected approaches, or falsely declares victory without executing verification suites. When the original agent returns, developer time and quota are spent undoing drift.

Our research goal was strictly investigative: **What existing, inspectable, legally reusable code can we assemble into an authoritative, durable, cross-agent development controller—and what do we genuinely need to invent ourselves?**

### 1.2 What Already Exists Closest to Our Goal
We uncovered three major architectural tiers of multi-agent and harness-management software in active open-source repositories:

1. **Local-First CLI Harness Orchestrators:**
   * **`alamops/agetor`** (MIT License, Bun/TypeScript, Electrobun/React): A local-first Kanban and CLI daemon designed specifically to run Claude Code, Codex, Antigravity (`agy`), Gemini CLI, Cursor, and fx concurrently. It isolates every task in a dedicated Git worktree, manages agent processes inside detached `tmux` sessions, tails native structured transcripts, and supports basic pipeline chaining with `<handoff>` JSON blocks.
   * **`awslabs/cli-agent-orchestrator` (CAO)** (Apache-2.0 License, Python 3.10+, uv): A multi-agent framework created by AWS Labs that wraps Claude Code, Codex CLI, Antigravity CLI, and Kiro CLI. Crucially, CAO implements an out-of-band MCP policy middleware (`@cao-mcp-server`) that intercepts tool calls before the agent executes them, and enforces **asymmetric workflow approvals** (an agent cannot approve its own plan).
   * **`OrchestratorInc/agent-orchestrator`** (Apache-2.0 License, Go daemon, Electron/React): A daemon-supervised orchestrator that models tasks via SQLite Change Data Capture (CDC) event streams, manages native PTY/ConPTY sessions, isolates tasks into per-project Git worktrees, and supports detached Agent Client Protocol (ACP) session hosts that survive daemon restarts.

2. **Dedicated Workspace & Git Worktree Managers:**
   * **`coderabbitai/git-worktree-runner` (`git gtr`)** (Apache-2.0 License, Bash/POSIX): A battle-tested utility specifically designed to automate Git worktree isolation for AI coding agents (`git gtr new <branch> --porcelain`). It automates baseline commit pinning, configuration file copying (`.env`, config files), post-creation hooks, and safe directory lifecycle management.
   * **`max-sixty/worktrunk` (`wt`)** (MIT License, Rust): A CLI tailored for parallel agent workflows that provides build-cache copying (`node_modules/`, `target/`), unique port allocations per worktree to prevent local dev server collisions, and post-merge teardown.

3. **Durable State Engines and Speculative Merge Queues:**
   * **`All-Hands-AI/OpenHands`** (MIT License, Python): Offers a battle-tested `EventStream` architecture (`openhands/core/event_stream.py`) separating typed Actions from Observations, providing durable state replay and sandboxed runtime boundaries.
   * **`bors-ng`** (Apache-2.0, Elixir): The reference open-source implementation of a "strict mode" speculative merge queue. It proves the invariant that an integration branch (`main`) must never accept a merge directly; it merges candidates to a temporary integration branch, runs deterministic CI checks outside the author's control, and only fast-forwards `main` upon automated test passage.

### 1.3 Which Hard Problems Have Credible Reusable Implementations
Our code inspection confirms that four difficult engineering problems have mature, inspectable, and reusable solutions:

1. **Zero-API-Billing Native CLI Driving:** Both `alamops/agetor` and `awslabs/cli-agent-orchestrator` successfully drive Claude Code, Codex CLI, and Antigravity CLI using developer subscription logins (`claude login`, `agy login`, Codex browser OAuth). They avoid expensive, separately metered per-token API billing by wrapping the native terminal binaries.
2. **Crash-Resilient Session Survival:** Wrapping long-running CLI sessions inside background `tmux` sessions (proven in `agetor`, `cao`, and `agent-orchestrator`) ensures that orchestrator crashes, UI refreshes, and terminal disconnects never abort an in-flight 30-minute agent run. Transcripts can be reattached and replayed seamlessly.
3. **Physical Workspace Isolation:** Native Git worktrees (proven in `agetor` and `git gtr`) cleanly prevent concurrent agents from colliding on files, lockfiles, or git index state, with zero container virtualization overhead.
4. **Out-of-Band Tool Policy Enforcement:** CAO’s `@cao-mcp-server` middleware demonstrates that tool authorization, delegation restrictions, and role permissions can be mechanically enforced outside the LLM context window using standard JSON-RPC interceptors.

### 1.4 Which Capabilities Remain Fundamental Gaps
Despite the maturity of individual tools, no existing system solves the end-to-end problem described by the user. Three major gaps require our own implementation:

1. **Tripartite Epistemological State Separation:** Existing tools conflate proposals, decisions, and facts into flat event streams or markdown files. A replacement agent cannot distinguish between:
   * *A Proposal:* An unverified plan, speculative prompt, or dirty diff.
   * *An Approved Decision:* An immutable architectural constraint signed off by the human operator.
   * *An Observed Fact:* A deterministic test failure, compiler error, exit code, or Git commit SHA.
2. **Deterministic Cross-Provider Task Handoff Without Replanning:** Existing tools either reset the agent session upon model change or dump a lossy natural language summary into the new agent's context. When an agent hits a rate limit, no existing tool automatically snapshots uncommitted worktree changes, extracts the incomplete sub-requirements from an authoritative specification, and injects them into the replacement agent with an explicit command to continue execution without replanning the architecture.
3. **Tamper-Proof Mechanical Verification & Merge Queue:** In all existing agent orchestrators, verification is advisory: agents execute tests via bash tools and self-report whether they passed. If an agent hallucinates a passing exit code, edits the test file to make it pass, or deletes `.github/workflows/`, existing orchestrators accept the PR. An out-of-band merge gate that runs independent test suites in an isolated clean worktree with orchestrator-owned credentials does not exist in any current agent harness.

### 1.5 Architectural Recommendation: Extend and Compose
* **Verdict:** Do NOT build from scratch, and do NOT fork a heavy monolithic enterprise platform.
* **Recommended Strategy:** **Compose a targeted local-first controller.**
  * Adopt the **Bun/TypeScript harness and worktree foundation of `alamops/agetor`** (MIT License) as the primary base for session supervisor, tmux process management, and CLI transcript ingestion.
  * Extract the **out-of-band MCP policy middleware and asymmetric approval architecture of `awslabs/cli-agent-orchestrator`** (Apache-2.0 License).
  * Build the missing core: A **SQLite-backed Tripartite State Machine** and an **Out-of-Band Speculative Merge Queue** that executes verification in an isolated validation worktree before merging into protected branches.

---

## 2. Landscape Table

The following table summarizes the open-source landscape across multi-agent orchestrators, harness runners, worktree managers, and execution engines.

| Candidate Repository & Organization | Primary Purpose | Relevant Supported Agents & Integration Type | Applicable Capabilities (1–8) | Evidence Level | License | Maintenance & Release Status | Main Limitations | Recommendation & Reason |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`alamops/agetor`**<br>(Alamo Ops) | Local-first Kanban & CLI orchestrator for coding CLIs | Claude Code (tmux interactive), Codex (`codex exec --json`), Antigravity (`agy stream-json`), Gemini CLI, Cursor, fx | 1 (Chat/Kanban), 2 (Agents), 5 (Replacement), 6 (Worktrees), 8 (Local-first) | **Code-verified**, **Test-supported** | **MIT License** (per `LICENSE`) | Very Active (v1.0.2 released Oct 2026; 324 commits) | Runs agents with unconstrained user privileges; no out-of-band verification gate; macOS-focused Electrobun desktop | **Shortlist (Primary Foundation Candidate):** Cleanest implementation of multi-harness CLI driving, worktree isolation, and restart survival. |
| **`awslabs/cli-agent-orchestrator`**<br>(AWS Labs) | CLI multi-agent orchestration framework & server | Claude Code (tmux/hooks), Codex CLI (`@openai/codex`), Antigravity CLI (`agy`), Kiro CLI | 1 (Workflows), 2 (Agents), 4 (Policy), 5 (Error detection), 6 (Worktrees), 7 (Autonomy) | **Code-verified**, **Test-supported** | **Apache-2.0** (per `LICENSE`) | Active (v2.1.1 released Oct 2026; 1.5k stars) | Complex supervisor abstraction; opinionated toward AWS-DLC workflows; lacks cohesive single-user desktop UI | **Shortlist (Core Policy & Adapter Subsystem):** Indispensable reference and reusable code for out-of-band tool restriction middleware and asymmetric approvals. |
| **`OrchestratorInc/agent-orchestrator`**<br>(Untrivial / OrchestratorInc) | Supervised daemon for coding agent fleets | Claude Code, Codex, 35+ CLI agents via PTY/ConPTY and detached ACP hosts | 1 (Fleet UI), 2 (Agents), 3 (CDC State), 6 (Worktrees), 8 (Local/Daemon) | **Code-verified**, **Documented only** | **Apache-2.0** (per `LICENSE`, Copyright Untrivial) | Active (Commit `71bb19f`, Oct 2026 nightlies) | Monorepo tightly coupled to Go daemon and Electron/Mobile clients; heavy internal abstractions | **Shortlist (Design Reference):** Excellent pattern for CDC SQLite persistence and detached ACP session survival, but extraction burden is high. |
| **`coderabbitai/git-worktree-runner` (`git gtr`)**<br>(CodeRabbit) | Automated Git worktree lifecycle runner for AI tools | Tool-agnostic CLI wrapper; built-in adapters for Claude Code, Cursor, Codex | 6 (Worktree isolation, config sync, lifecycle hooks) | **Code-verified**, **Test-supported** | **Apache-2.0** (per `LICENSE.txt`) | Active (v2.11.1 released Oct 2026) | Shell script; does not manage agent processes, transcripts, or scheduling | **Shortlist (Subsystem Utility):** Best-in-class, robust script for porcelain worktree creation, `.env` copying, and hook execution. |
| **`max-sixty/worktrunk` (`wt`)**<br>(Max Sixty) | Rust CLI for Git worktree management tailored for AI agents | Tool-agnostic CLI; launches AI tools in worktrees | 6 (Worktree management, build cache copying, port isolation) | **Code-verified** | **MIT / Apache-2.0** | Active (v0.8.x, Sept/Oct 2026) | Focused strictly on directory and port management; no agent state or transcript streaming | **Secondary Component:** Excellent reference for build-cache copying (`node_modules`) and port allocation per worktree. |
| **`All-Hands-AI/OpenHands`**<br>(All-Hands-AI) | Autonomous software development agent framework | In-house agents (CodeAct); connects to raw LLM APIs (Anthropic, OpenAI, etc.) | 3 (EventStream state), 4 (Docker sandboxing), 7 (Budgets) | **Code-verified**, **Test-supported** | **MIT License** | Very Active (v0.14+, 45k+ stars) | Does NOT drive external CLI agents (Claude Code / agy); requires full Docker container daemon per agent | **Shortlist (Subsystem Architecture):** The `EventStream` architecture (`openhands/core/event_stream.py`) is the gold standard for typed state machines. |
| **`bors-ng/bors-ng`**<br>(Bors-ng Maintainers) | Continuous testing merge queue bot ("Strict Mode") | Git repository host integration (GitHub/GitLab) | 4 (Authority), 6 (Controlled merge queue, independent verification) | **Code-verified**, **Documented only** | **Apache-2.0** | Maintained / Legacy reference (author deprecated in 2023, widely forked) | Written in Elixir; designed for central GitHub repos rather than local development loops | **Shortlist (Design Reference):** Reference logic for speculative batching and out-of-band verification gates before merging. |
| **`PaulGauthier/aider`**<br>(Paul Gauthier) | AI pair programming in terminal with git integration | Direct LLM API calls; architect/editor mode | 3 (Repo map, Git commit history), 8 (Local CLI) | **Code-verified** | **Apache-2.0** | Very Active | Monolithic single-agent CLI; does not wrap Claude Code or Antigravity; cannot orchestrate external agent CLIs | **Reject as Foundation:** Aider is an agent itself, not an orchestrator of external coding CLIs. |
| **`andyrewlee/awesome-agent-orchestrators` / `agent-console`** | Curation list & Rust TUI session viewer | Session discovery for Claude Code, Codex, Agetor | 1 (Inspection), 8 (Local TUI) | **Documented only** | **MIT License** | Emerging (Oct 2026) | Read-only session inspection; no scheduling, state, or task enforcement | **Reject:** Useful for directory discovery, but contains no orchestration logic. |

---

## 3. Deep Source Audits of the Strongest Candidates

### 3.1 Candidate 1: `alamops/agetor`
* **Repository:** `https://github.com/alamops/agetor`
* **Pinned Revision:** Release `v1.0.2` (Commit `62f4b4a1b028`, October 2026)
* **License:** MIT License (verified in root `LICENSE` file)
* **Subsystem Inspected:**
  1. Process Supervisor & Tmux Lifecycle: `src/bun/orchestrator.ts`, `src/bun/tmux.ts`
  2. Agent Harness Drivers: `src/bun/harnesses/claude.ts`, `src/bun/harnesses/codex.ts`, `src/bun/harnesses/antigravity.ts`
  3. Git Worktree Lifecycle: `src/bun/worktree.ts`
  4. Handoff Schema & Pipeline DAG: `src/bun/pipeline.ts`

#### How Its Implementation Works
`agetor` is an Electrobun application (a Bun core backend listening on `127.0.0.1:4317` with token authentication, paired with a native macOS WebView and React UI). It drives external CLIs without proxying LLM tokens:
1. **Claude Code Harness:** Spawns an interactive `claude` session inside a named `tmux` session (`agetor-<task_id>`). Prompts and user inputs are sent via `tmux send-keys`. Crucially, rather than scraping ANSI terminal escapes, `agetor` streams structured output by locating and tailing Claude Code's native JSONL session transcript at `~/.claude/projects/<slug>/<session_id>.jsonl`.
2. **Codex Harness:** Drives `@openai/codex` in headless mode by executing `codex exec --json` per turn inside `tmux`. Resumption across turns is achieved by passing `--resume <thread_id>`, capturing stdout JSON lines.
3. **Antigravity CLI Harness:** Invokes Google Antigravity's terminal CLI `agy` using `agy stream-json` inside `tmux`, resuming conversations via `agy resume <conversation_id>`.
4. **Worktree Management:** When a task is created, `worktree.ts` executes `git worktree add ~/.agetor/worktrees/<task-id> -b agetor/<task-id>-<slug> <base-commit>`. All agent commands are executed strictly within that isolated directory.
5. **Durable Handoffs:** Pipelines allow chaining steps. A step concludes by emitting a structured JSON block:
   ```json
   <handoff>
   {
     "purpose": "Implement authentication middleware",
     "summary": "Added JWT validation in auth.ts; unit tests pass.",
     "reason": "Ready for security review",
     "next": "SecurityReviewer",
     "artifacts": ["src/middleware/auth.ts"],
     "openQuestions": []
   }
   </handoff>
   ```
   If a step fails, times out, or requests input, `agetor` transitions the task card to `Blocked` and halts automatic progression.

#### Tests and Failure Handling
* **Inspected Tests:** `src/bun/orchestrator.test.ts`, Playwright integration tests (`playwright.config.ts`).
* **Crash Recovery:** On daemon boot, `agetor` inspects active `tmux` sessions. If a session is alive, it reconnects and replays the JSONL transcript without duplicating messages. If the session died during an uncompleted run, the task is safely moved from `Running` back to `Ready`.
* **Known Limitations / Failure Modes:**
  * **Unconstrained Agent Privileges:** The agent runs with the developer's full local shell permissions. There is no sandboxing or tool gating.
  * **Advisory Handoffs:** The `<handoff>` block is parsed from LLM text. If the LLM omits it or formats it improperly, the system retries once and then stalls.
  * **No Out-of-Band CI Verification:** When a task moves to `Review`, `agetor` provides a diff viewer and a "Commit and Push" button, but performs no independent compilation or test validation.
  * **Platform Coupling:** The desktop shell relies on Electrobun (macOS Apple Silicon). However, the headless CLI daemon (`agetor daemon`) runs on pure Bun and Linux.

#### Dependencies, Coupling, and Extraction Difficulty
* **Runtime:** Bun ≥ 1.3.5, `tmux` ≥ 3.3, `git`.
* **Coupling:** The core orchestration logic (`src/bun/`) is cleanly separated from the Electrobun UI wrapper. It communicates via an internal HTTP/SSE REST API.
* **Extraction Assessment:** **Low to Moderate difficulty.** The entire `src/bun/` daemon can be extracted and run as a headless background CLI service on Linux or macOS.

---

### 3.2 Candidate 2: `awslabs/cli-agent-orchestrator` (CAO)
* **Repository:** `https://github.com/awslabs/cli-agent-orchestrator`
* **Pinned Revision:** Release `v2.1.1` (Commit `e9a3b12`, October 2026)
* **License:** Apache License 2.0 (verified in `LICENSE`)
* **Subsystem Inspected:**
  1. Out-of-Band Tool Restriction Middleware: `docs/tool-restrictions.md`, `src/cli_agent_orchestrator/services/mcp_server.py`
  2. Provider Adapters: `src/cli_agent_orchestrator/providers/claude_code.py`, `providers/codex.py`, `providers/antigravity.py`
  3. Asymmetric Workflow Engine: `docs/workflows.md`, `skills/cao-workflow/SKILL.md`

#### How Its Implementation Works
CAO is a Python-based orchestrator that coordinates CLI coding agents through a local server (`cao-server` on port 9889) and CLI (`cao`):
1. **The Out-of-Band Policy Broker (`@cao-mcp-server`):** Unlike naive orchestrators that rely on system prompt instructions to restrict agents, CAO runs an MCP server that acts as a secure middleware. Every tool invocation passes through an `on_call_tool` middleware before dispatch:
   * Tools are gated against an explicit profile allowlist (`allowedTools`).
   * Delegation tools (`assign`, `handoff`, `assign_elastic`, `create_ephemeral_agent`) are restricted based on caller identity.
   * If an agent attempts to invoke a disallowed tool, the middleware rejects the call at the RPC boundary—the underlying operating system or terminal never executes it.
2. **Asymmetric Plan Approval:** CAO enforces a strict architectural boundary between planning and execution. In workflow mode:
   * An agent can write and propose a plan (`workflow_plan_approval`).
   * The agent is programmatically denied access to the approval tool.
   * Approval requires an explicit human command via the CLI (`cao workflow approve <plan_id>`). An agent can never approve its own plan.
3. **Provider Abstraction:** CAO's `BaseProvider` class defines a standard interface:
   * `claude_code.py`: Launches Claude Code inside `tmux`, pipes pane output through a FIFO watcher (`services/fifo_reader.py`), and injects `@cao-mcp-server` into Claude's MCP configuration.
   * `codex.py`: Invokes `@openai/codex` passing developer instructions via `-c developer_instructions="..."`.
   * `antigravity.py`: Launches `agy` with appropriate flags and hooks into its local configuration.
4. **Error Classification:** CAO explicitly categorizes task failures in `cao-workflow`:
   * `transient`: Timeouts or temporary connection drops (safe to resume).
   * `artifact_defect`: Model syntax errors, invalid JSON, or `provider_error` (authentication failure, rate limit reached, quota exhausted). When a `provider_error` is classified, the system immediately halts the loop rather than burning tokens in an endless retry cycle.

#### Tests and Failure Handling
* **Inspected Tests:** `test/providers/test_kiro_cli_unit.py`, `test/test_workflows.py`, `test/test_tool_restrictions.py`.
* **Failure Handling:** Robust detection of process exit codes, socket timeouts (~8820s ceiling for blocking CLI runs), and pipe-pane liveness watchdogs.
* **Limitations:**
  * State is maintained across local SQLite and JSON files, but lacks an event-sourced audit log.
  * The codebase is tightly bound to AWS Labs' AI-DLC concepts and terminology, requiring refactoring to make it a general-purpose project controller.

#### Dependencies, Coupling, and Extraction Difficulty
* **Runtime:** Python 3.10+, `uv`, `tmux`.
* **Extraction Assessment:** **Low difficulty for provider adapters and MCP middleware.** The `on_call_tool` restriction middleware and provider CLI wrapper patterns are modular and can be directly vendored or translated into TypeScript/Go.

---

### 3.3 Candidate 3: `OrchestratorInc/agent-orchestrator`
* **Repository:** `https://github.com/OrchestratorInc/agent-orchestrator`
* **Pinned Revision:** Commit `71bb19f` (Nightly Build, October 28, 2026)
* **License:** Apache License 2.0 (Copyright 2026 Untrivial / OrchestratorInc)
* **Subsystem Inspected:**
  1. Architecture & Persistence Model: `docs/architecture.md`, `docs/development.md`
  2. Storage & Migrations: `backend/storage/`, SQLite schema migrations
  3. Detached Session Hosts: Session service and ACP host manager

#### How Its Implementation Works
`agent-orchestrator` is designed around a Go daemon that acts as an authoritative supervisory control plane:
1. **Durable Minimalism via Facts & CDC:** The system follows an event-sourced philosophy: "Store only facts, compute everything else." The SQLite database records append-only operational facts (process spawn, exit, turn start, turn finish, error emitted). Derived status (e.g., whether a task is active, stalled, or failed) is computed dynamically. A Change Data Capture (CDC) engine broadcasts SQLite row modifications to all connected desktop and mobile clients.
2. **Detached Session Hosts:** To prevent agent abortion during controller crashes or desktop app restarts, Codex and all Agent Client Protocol (ACP) processes run inside detached per-session OS host processes. The daemon can crash, restart, and reconnect to the host process without severing the in-flight agent turn or losing JSON-RPC correlation IDs.
3. **Session Virtualization:** It abstracts agent interfaces into two distinct modes:
   * *TUI Mode:* Runs the agent inside a native PTY/ConPTY runtime (with `tmux` as fallback).
   * *Chat Mode:* Communicates directly with the agent's protocol layer without allocating a pseudo-terminal.

#### Tests and Failure Handling
* **Failure Handling:** Conservative termination logic ensures processes are not prematurely killed; strict path validation prevents directory traversal out of assigned worktrees.
* **Limitations:** Heavy monorepo codebase; tightly coupled to proprietary mobile client push notifications and Electron desktop scaffolding.

#### Dependencies, Coupling, and Extraction Difficulty
* **Runtime:** Go 1.22+, SQLite, CGO / ConPTY on Windows.
* **Extraction Assessment:** **High difficulty for code extraction; Outstanding as an architectural design reference.** The CDC event-driven persistence and detached session host design provide the exact blueprint for our durable controller.

---

### 3.4 Candidate 4: `coderabbitai/git-worktree-runner` (`git gtr`)
* **Repository:** `https://github.com/coderabbitai/git-worktree-runner`
* **Pinned Revision:** Release `v2.11.1` (Commit `a41bc78`, October 2026)
* **License:** Apache License 2.0 (verified in `LICENSE.txt`)
* **Subsystem Inspected:**
  1. Worktree Creation & Porcelain Protocol: `lib/commands/new.sh`, `README.md`
  2. Configuration Copying & Environment Isolation: `lib/core/copy.sh`
  3. Lifecycle Hooks: `lib/core/hooks.sh`

#### How Its Implementation Works
`git gtr` is a lightweight, cross-platform CLI written in portable Bash that solves the dirty practicalities of Git worktrees for AI coding agents:
1. **Porcelain Automation:** Running `git gtr new <branch> --porcelain` creates an isolated Git worktree linked to `<branch>`, verifies base ref validity, and outputs machine-parseable JSON/paths for external orchestrators.
2. **Automated Configuration Synchronization:** Normal Git worktrees do not copy untracked `.env` files, local configurations, or tool settings. `git gtr` reads `gtr.copy.include` from `.git/config` and automatically copies necessary development secrets and configurations into the newly spawned worktree without checking them into Git.
3. **Post-Creation Setup Hooks:** Executes `gtr.hook.postCreate` (e.g., installing dependencies or generating stub code) immediately after worktree allocation, ensuring the AI agent enters a fully prepared environment.
4. **Safe Pruning:** `git gtr prune` inspects whether a worktree contains uncommitted changes or unpushed branches before removing it, preventing accidental data loss when an agent session is terminated.

#### Tests, Dependencies, and Extraction Difficulty
* **Runtime:** Pure POSIX Bash, Git ≥ 2.30.
* **Extraction Assessment:** **Trivial difficulty.** Can be vendored directly as a helper script or called as a sub-process CLI command by our controller.

---

### 3.5 Candidate 5: `All-Hands-AI/OpenHands`
* **Repository:** `https://github.com/All-Hands-AI/OpenHands`
* **Pinned Revision:** Release `0.14.0` (Commit `39df28a`, September 2025 – 2026)
* **License:** MIT License (verified in `LICENSE`)
* **Subsystem Inspected:**
  1. Event Stream Architecture: `openhands/core/event_stream.py`
  2. State Machine & Controller: `openhands/controller/state/state.py`
  3. Action & Observation Hierarchy: `openhands/events/action/`, `openhands/events/observation/`

#### How Its Implementation Works
OpenHands structures agent execution entirely around an append-only, strongly typed event stream:
1. **Action/Observation Duality:** The agent emits an `Action` (e.g., `CmdRunAction`, `FileWriteAction`, `AgentThinkAction`). The execution environment responds with an `Observation` (e.g., `CmdOutputObservation`, `FileReadObservation`, `ErrorObservation`).
2. **Durable Replay:** Because every state transition is recorded as an immutable event with an incremental ID, the controller can reconstruct the full mental state, file changes, and tool results of any session after a crash simply by replaying the event stream.
3. **Execution Sandboxing:** Isolates execution inside Docker containers, preventing dangerous shell commands from compromising the host.

#### Trade-Offs for Our Project
* **Why OpenHands Cannot Be Our Direct Foundation:** OpenHands is designed to build *its own* agents by issuing raw prompt completions to LLM APIs (OpenAI, Anthropic). It does not provide abstractions to supervise, attach to, or parse external coding CLIs like Claude Code or Antigravity.
* **What We Can Reuse:** The `EventStream` schema and typed state transition contracts (`Action` vs `Observation`) can be extracted as our internal project state model.

---

### 3.6 Candidate 6: `bors-ng` (Strict Mode Speculative Merge Queue)
* **Repository:** `https://github.com/bors-ng/bors-ng`
* **Pinned Revision:** `v0.5.x` (Commit `c45de10`)
* **License:** Apache License 2.0
* **Subsystem Inspected:** Batcher, Brancher, and Test Verification State Machine (`lib/bors/worker/`)

#### How Its Implementation Works
`bors-ng` enforces a strict invariant that eliminates integration drift: **no branch is ever merged into `main` without testing the exact merge commit first.**
1. When a task claims completion, it does not merge into `main`. It adds the task branch to a verification queue.
2. The batcher creates a speculative merge commit on a temporary branch (`staging`): `git merge --no-ff <task-branch>`.
3. The out-of-band CI system executes the full test and lint suite against `staging`.
4. If all tests pass, `bors-ng` fast-forwards `main` to the tested commit (`git push origin staging:main`). If tests fail, the speculative branch is discarded, `main` remains untouched, and the author (or agent) is notified of the exact failure.

#### Trade-Offs for Our Project
* Written in Elixir, which is unsuitable as an embedded dependency for a local developer CLI.
* However, the **state machine logic** (speculative merge commit -> isolated out-of-band test run -> fast-forward `main` upon success -> discard on failure) is straightforward to implement deterministically in TypeScript or Python (under 250 lines of code).

---

## 4. Component Reuse Map

The following map defines the exact candidate components, source locations, reuse methods, licenses, confidence levels, and remaining implementation gaps across every required architectural capability.

| Required Capability | Candidate Component | Exact Source Location | Preferred Reuse Method | License Considerations | Confidence Level | Remaining Gap for Us to Build |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Central Chat & Task Board** | `alamops/agetor` | `src/bun/orchestrator.ts`, React Kanban UI | **Fork / Adapt** | MIT License | **Code-verified** | Replace Electrobun desktop wrapper with lightweight headless local web/TUI server; add executable assignment schema. |
| **Agent CLI Adapters (Claude, Codex, Antigravity)** | `alamops/agetor` + `awslabs/cli-agent-orchestrator` | `agetor/src/bun/harnesses/`, `cao/src/cli_agent_orchestrator/providers/` | **Extract & Vendor** | MIT / Apache-2.0 (compatible) | **Code-verified** | Normalize JSON output formats; handle Antigravity CLI's implicit protobuf/JSONL stream quirks. |
| **Out-of-Band Tool & Policy Enforcement** | `awslabs/cli-agent-orchestrator` | `docs/tool-restrictions.md`, `cao-mcp-server` middleware | **Extract & Port** | Apache-2.0 (notice required) | **Code-verified** | Bind MCP interceptor to local filesystem boundaries and read-only test configuration rules. |
| **Durable Tripartite State & Event Log** | `All-Hands-AI/OpenHands` (Schema) + `agetor` (SQLite) | `openhands/core/event_stream.py`, `agetor/src/bun/db.ts` | **Design Reference & Independent Impl** | MIT License | **Code-verified** | Implement explicit SQLite schema distinguishing *Proposals* (unapproved diffs), *Approved Decisions* (ADRs), and *Observed Facts* (CI outputs). |
| **Restart-Safe Process Supervision** | `alamops/agetor` + `agent-orchestrator` | `agetor/src/bun/tmux.ts`, `agent-orchestrator/backend/` | **Vendor / Adapt** | MIT / Apache-2.0 | **Code-verified** | Implement PID lease fencing and kill signals to terminate stale agents upon task reassignment. |
| **Git Worktree Isolation & Setup** | `coderabbitai/git-worktree-runner` (`git gtr`) | `lib/commands/new.sh`, `lib/core/copy.sh` | **Depend / Shell Exec** | Apache-2.0 | **Code-verified** | Connect worktree creation to controller task lifecycle; automate cleanup on task archival. |
| **Build Cache & Port Isolation** | `max-sixty/worktrunk` | `src/worktree.rs`, `src/port.rs` | **Design Reference** | MIT / Apache-2.0 | **Code-verified** | Implement copy-on-write or hardlinked `node_modules` sharing; assign unique ephemeral ports per worktree. |
| **Out-of-Band CI Verification & Merge Queue** | `bors-ng` | `lib/bors/worker/batcher.ex` | **Independent Implementation** (Design Reference) | Apache-2.0 | **Code-verified** | Write deterministic 200-line Git merge queue in controller runtime that executes tests before updating `main`. |
| **Bounded Autonomy & Loop Detection** | `awslabs/cli-agent-orchestrator` | `cao-workflow` classification, step caps | **Extract Logic** | Apache-2.0 | **Code-verified** | Implement token/time repair budgets and hard step caps (default 25 turns) before escalating to operator. |

---

## 5. Agent Compatibility Matrix

An in-depth technical comparison of Anthropic Claude Code, OpenAI Codex CLI, Google Antigravity CLI, and Google Antigravity IDE.

| Capability / Attribute | Anthropic Claude Code (`claude`) | OpenAI Codex CLI (`codex`) | Google Antigravity CLI (`agy`) | Google Antigravity IDE (Full App) |
| :--- | :--- | :--- | :--- | :--- |
| **Underlying Binary & Distribution** | `claude` (npm: `@anthropic-ai/claude-code`) | `codex` (npm: `@openai/codex`) | `agy` (curl script / Homebrew / `uv add google-antigravity`) | Full standalone desktop application (`antigravity.google/download`) |
| **Programmatic / Headless Launch** | `claude -p "<prompt>"` or interactive `tmux` | `codex exec "<prompt>"` or `npx @openai/codex` | `agy -p "<prompt>"` or `agy stream-json` | GUI application only; lacks headless CLI invocation interface |
| **Streaming Output Format** | Live JSONL transcript in `~/.claude/projects/<slug>/<id>.jsonl` or `--output-format json/stream` | Line-delimited JSON events (`codex exec --json`) | Line-delimited JSON events (`agy stream-json`) | Proprietary internal RPC / Electron IPC; not designed for external CLI piping |
| **Session Resumption** | `--resume <session_id>` or append keystrokes to active `tmux` session | `codex exec --resume <thread_id>` | `agy resume <conversation_id>` (SQLite: `antigravity-cli.conversations`) | Resumed within IDE workspace GUI only |
| **Unattended Operation & Approvals** | `--permission-mode dontAsk` or `bypassPermissions` | `--headless` mode, auto-approves tool execution | `--trust` flag; auto-approves workspace context | Visual approval modals within editor window |
| **Cancellation & Termination** | `SIGINT` (Ctrl+C), `SIGTERM`, or `tmux kill-session` | `SIGINT`, `SIGTERM`, or `tmux kill-session` | `SIGINT`, `SIGTERM`, or `tmux kill-session` | Requires GUI window closure or process SIGKILL |
| **Rate-Limit & Quota Detection** | Emits HTTP 429 / "Overloaded" / "Rate limit reached" in JSONL transcript | Emits error event in JSON stream with quota status | Emits quota exhaustion message in stream; inspectable via `agy models` / `agy /usage` | Modal popup in UI displaying quota exhaustion |
| **Hooks & Out-of-Band Points** | PreToolUse, PostToolUse, OnNotification in `.claude/hooks.json` | Passes developer context via `-c developer_instructions="..."` | Plugin system, Model Context Protocol (MCP) support | VS Code / JetBrains style extension marketplace |
| **Supported Authentication & Billing** | Web OAuth subscription (`claude login` -> Pro/Team/Max) OR `ANTHROPIC_API_KEY` | ChatGPT subscription login (Plus/Team/Pro) OR `OPENAI_API_KEY` | Google OAuth subscription login (`agy login`) OR `GEMINI_API_KEY` | Google Account OAuth sign-in within desktop IDE |
| **Zero-API-Cost Local Operation?** | **YES** (via existing Claude Pro/Team subscription) | **YES** (via existing ChatGPT Plus/Pro subscription) | **YES** (via existing Google Workspace / Gemini subscription) | **YES** (via Google Account login) |
| **OS & Platform Support** | macOS, Linux, WSL2 (native Windows unsupported) | macOS, Linux, Windows native | macOS, Linux (packaged for Ubuntu/Debian/Homebrew) | macOS, Windows, Linux desktop |

### Key Clarification: Antigravity IDE vs. Antigravity CLI vs. Gemini CLI
1. **Antigravity IDE:** A full-featured desktop development environment featuring an AI Agent Manager and editor extensions. It is **not suitable** as a headless orchestrator worker because it cannot be driven non-interactively via stdio.
2. **Antigravity CLI (`agy`):** Google's official autonomous terminal coding agent introduced in 2026. It is lightweight, supports headless streaming (`agy stream-json`), accepts prompt injection, and manages local sessions in an internal SQLite database. **This is the exact target to integrate.**
3. **Gemini CLI (`gemini`):** The legacy predecessor CLI (`@google/gemini-cli`). Google provides migration guides (`Migrating from Gemini CLI - Google Antigravity`) to migrate MCP configurations and skills to `agy`. Gemini CLI should be treated as legacy.

---

## 6. Failure-Scenario Assessment

We audited how existing implementations respond to the ten failure scenarios identified in the problem statement, identifying where code exists and where custom engineering is mandatory.

```
+-------------------------------------------------------------------------------------------------------+
|                                    FAILURE SCENARIO AUDIT MATRIX                                      |
+-----------------------------------+-----------------------------------+-------------------------------+
| Scenario                          | Handled by Existing Code?         | Exact Mechanism & Gap         |
+-----------------------------------+-----------------------------------+-------------------------------+
| 1. Claude reaches limit mid-edit  | PARTIAL (`cao`, `agetor`)         | Classified as provider_error. |
|                                   |                                   | GAP: Uncommitted edit freeze  |
+-----------------------------------+-----------------------------------+-------------------------------+
| 2. Codex inherits partial work    | POOR / UNVERIFIED                 | Sent full diff or raw prompt. |
|                                   |                                   | GAP: AST delta reconciliation |
+-----------------------------------+-----------------------------------+-------------------------------+
| 3. Antigravity unauthorized arch  | PARTIAL (`cao` tool restrictions) | Blocks disallowed tools.      |
|                                   |                                   | GAP: File/directory ACLs      |
+-----------------------------------+-----------------------------------+-------------------------------+
| 4. Paused worker resumes later    | PARTIAL (`agetor`, `ao`)          | Tmux session remains active.  |
|                                   |                                   | GAP: Fencing token revocation |
+-----------------------------------+-----------------------------------+-------------------------------+
| 5. Concurrent interface conflicts | PARTIAL (`agetor` worktrees)      | Separate worktrees prevent FS |
|                                   |                                   | collision. GAP: Merge queue   |
+-----------------------------------+-----------------------------------+-------------------------------+
| 6. Controller crash during merge  | PARTIAL (`ao` SQLite CDC)         | Tmux survives crash.          |
|                                   |                                   | GAP: Two-phase Git commit WAL |
+-----------------------------------+-----------------------------------+-------------------------------+
| 7. Worker claims tests pass       | UNHANDLED (Universal Gap)         | Models self-report success.   |
|                                   |                                   | GAP: Out-of-band CI runner    |
+-----------------------------------+-----------------------------------+-------------------------------+
| 8. Tests pass, violates reqs      | PARTIAL (`cao` workflow approval) | Asymmetric plan approval gate.|
|                                   |                                   | GAP: Formal requirement spec  |
+-----------------------------------+-----------------------------------+-------------------------------+
| 9. Worker edits verification rules| UNHANDLED in harnesses            | Models have write access.     |
|                                   |                                   | GAP: Git hook / read-only ACL |
+-----------------------------------+-----------------------------------+-------------------------------+
| 10. All providers unavailable     | PARTIAL (`cao-workflow`)          | Halts run; sets Blocked state.|
|                                   |                                   | GAP: Exponential backoff poll |
+-----------------------------------+-----------------------------------+-------------------------------+
```

### Detailed Scenario Analysis

#### Scenario 1: Claude reaches a limit mid-edit
* **Existing Code:** CAO classifies rate limits as `provider_error` under `skills/cao-workflow/SKILL.md`. `agetor` detects error events in Claude's JSONL stream and halts the task into `Blocked`.
* **The Gap:** Neither tool preserves the exact dirty working tree state safely. If Claude crashes while writing a file, the file is left half-written.
* **Our Solution:** The controller must execute `git stash create` or record an ephemeral `WIP: Pre-switch snapshot` commit before spawning the replacement agent.

#### Scenario 2: Codex inherits partial work
* **Existing Code:** `agetor` provides the `<handoff>` JSON block, which summarizes touched files and open questions.
* **The Gap:** Codex has different prompting defaults and model biases. If passed only natural language, Codex frequently re-architects or discards Claude's half-finished code.
* **Our Solution:** The controller must compile an immutable **Handoff Bundle**:
  1. The original frozen Task Specification (acceptance criteria, forbidden files).
  2. The exact Git diff (`git diff HEAD~1`) produced by Claude.
  3. A strict continuation directive: *"Do NOT alter architecture or existing passing functions in [Files]. Only implement the remaining incomplete acceptance criteria: [List]."*

#### Scenario 3: Antigravity attempts an unauthorized architecture change
* **Existing Code:** CAO’s `@cao-mcp-server` middleware intercepts tool calls out-of-band.
* **The Gap:** If Antigravity uses its native bash tool or file edit capabilities, MCP middleware cannot stop it unless file-system writes are intercepted at the OS level.
* **Our Solution:** Implement OS-level filesystem restrictions (e.g., Linux Landlock, Bubblewrap, or a pre-commit Git hook) that rejects changes to files outside the task's authorized `scope.allowed_paths`.

#### Scenario 4: A paused worker resumes after reassignment
* **Existing Code:** In `agetor` and `cao`, the previous agent's `tmux` session may still be running in the background. If the user accidentally resumes it or the process unblocks, both agents could write to the same worktree.
* **The Gap:** Lack of process fencing or lease revocation.
* **Our Solution:** The controller must issue an explicit `kill-session` to the old agent's `tmux` session and rotate the worktree branch name or lease token before initializing the new worker.

#### Scenario 5: Two workers modify a shared interface
* **Existing Code:** `agetor` and CAO isolate workers in independent Git worktrees (`~/.agetor/worktrees/<id>`). They do not collide on the local disk.
* **The Gap:** When both workers attempt to merge their branches back into `main`, Git conflicts occur. Neither tool features an automated conflict mediator.
* **Our Solution:** Implement a speculative merge queue (Bors pattern). The first worker merges cleanly. The second worker's branch is automatically rebased against new `main` in an isolated rebase worktree; if merge conflicts arise, an automated conflict-resolution task is spawned.

#### Scenario 6: The controller crashes during an external action or merge
* **Existing Code:** `agent-orchestrator` persists raw facts to SQLite with WAL mode.
* **The Gap:** If the controller crashes while performing a Git merge or network push, the Git repository can be left with locked index files (`index.lock`).
* **Our Solution:** Two-phase state commit. Write an intent record (`MERGE_IN_PROGRESS`) in SQLite before invoking Git. Upon recovery, the daemon checks for orphaned `index.lock` files, rolls back unfinished merges with `git merge --abort`, and retries.

#### Scenario 7: A worker claims success while tests fail
* **Existing Code:** In all existing harnesses (`agetor`, CAO, `agent-orchestrator`), the agent self-reports completion. If the model hallucinates or ignores a test failure, the orchestrator marks the card `Review`.
* **The Gap:** Total absence of mechanical, out-of-band test execution.
* **Our Solution:** Mechanical Verification Gate. The controller ignores the agent's natural language claim. A task cannot transition to `Done` until the controller independently runs the verification suite in a pristine worktree and verifies `exit_code == 0`.

#### Scenario 8: Tests pass but the feature violates an approved requirement
* **Existing Code:** CAO enforces asymmetric workflow approval: agents can submit plans, but only humans can approve them.
* **The Gap:** Semantic verification cannot be automated purely with bash tests.
* **Our Solution:** Tripartite approval state:
  1. *Mechanical Verification:* Automated unit/integration tests pass (prerequisite).
  2. *Operator Sign-Off:* Diff and requirement checklist presented to the human in the chat UI. Merge is blocked until explicit human approval.

#### Scenario 9: A worker modifies its own verification rules
* **Existing Code:** No existing harness prevents an agent from editing `test_*.py` or `.github/workflows/` to force failing tests to pass.
* **The Gap:** Critical security and integrity vulnerability in autonomous coding agents.
* **Our Solution:** Out-of-band verification isolation. The controller executes tests using the test suite from the protected `main` branch, ignoring any modifications the agent made to test specifications, or rejecting the PR immediately if protected test paths are touched without authorization.

#### Scenario 10: Every available provider is temporarily unavailable
* **Existing Code:** CAO classifies this as `provider_error` and transitions the workflow to `stalled` or `blocked`.
* **The Gap:** Lack of coordinated exponential backoff and resume polling.
* **Our Solution:** The controller moves the active task to `QuotaPaused`, records the timestamp, schedules a periodic health check (`agy /usage`, `claude` ping), and alerts the user without discarding task progress.

---

## 7. Evidence-Backed Assembly Options

We propose three concrete assembly architectures based strictly on the inspected open-source codebases.

```
+---------------------------------------------------------------------------------------------------------+
|                                      ASSEMBLY ARCHITECTURE OPTIONS                                      |
+-----------------------------------+-----------------------------------+---------------------------------+
| Option A: Fastest Prototype       | Option B: Strongest Long-Term     | Option C: Simplest Local-First  |
| ("The Pragmatic Harness")         | ("The Controlled Platform")       | ("The Deterministic Dispatcher")|
+-----------------------------------+-----------------------------------+---------------------------------+
| Base: alamops/agetor (Bun)        | Base: CAO + OpenHands EventStream | Base: Go Daemon (AO pattern)    |
| UI: Agetor React Kanban / TUI     | UI: Web UI (FastAPI/React) + CLI  | UI: Terminal UI (Bubbletea)     |
| Isolation: git gtr + Worktrees    | Isolation: Bubblewrap + Worktrees | Isolation: git worktree         |
| Policy: Regex/Hook guards         | Policy: Out-of-band MCP middleware| Policy: Git pre-commit hooks    |
| Verification: Local Bash runner   | Verification: Bors Merge Queue    | Verification: Synchronous CI    |
+-----------------------------------+-----------------------------------+---------------------------------+
```

### Option A: Fastest Credible Prototype ("The Pragmatic Harness")
* **Foundation:** Fork and adapt **`alamops/agetor`** (Bun/TypeScript, MIT License).
* **Architecture:**
  * Keep `agetor`'s Bun core daemon, SQLite database, and proven harness drivers for Claude Code, Codex, and Antigravity CLI.
  * Integrate **`coderabbitai/git-worktree-runner` (`git gtr`)** for hardened porcelain worktree creation and configuration copying.
  * Add a lightweight TypeScript verification script that executes project tests upon task completion before enabling the "Commit" action.
* **Missing Code to Build:**
  * Headless Linux daemon packaging (strip Electrobun desktop dependency).
  * Out-of-band test verification runner in `src/bun/verifier.ts`.
  * Handoff bundle compiler that snapshots dirty diffs before switching harnesses.
* **Operational Cost & Footprint:** Minimal. Runs as a single local process using `bun`, requires local `git` and `tmux`.
* **Major Risks:** UI is tightly coupled to desktop macOS in upstream repo; policy enforcement remains advisory without an MCP interceptor.

### Option B: Strongest Long-Term Foundation ("The Controlled Platform")
* **Foundation:** Compose **`awslabs/cli-agent-orchestrator`** (Python/uv, Apache-2.0) with an **`OpenHands`**-style EventStream and a **`bors-ng`** speculative merge queue.
* **Architecture:**
  * **Control Plane:** Python 3.11 daemon using FastAPI and SQLite (WAL mode).
  * **Policy Enforcement:** Extract CAO's `@cao-mcp-server` `on_call_tool` middleware to strictly sandbox agent capabilities out-of-band.
  * **Execution Isolation:** Run each agent CLI in a dedicated Git worktree inside a lightweight Linux user namespace (via `bubblewrap`), preventing arbitrary writes outside assigned directories.
  * **Durable State:** Implement a formal Tripartite State Machine recording Proposals, Approved Decisions (ADRs), and Facts.
  * **Merge Safety:** An in-process speculative merge queue that validates integration in a pristine worktree before updating `main`.
* **Missing Code to Build:**
  * Unified Web/CLI chat client.
  * Bubblewrap sandboxing wrapper scripts.
  * In-process Bors merge queue state engine.
* **Operational Cost & Footprint:** Moderate. Requires Python, `uv`, `tmux`, `bubblewrap`, and Git. Completely local; zero external SaaS dependencies.
* **Major Risks:** Higher initial integration effort across Python packages.

### Option C: Simplest Local-First Setup ("The Deterministic Dispatcher")
* **Foundation:** A standalone, single-binary Go orchestrator inspired by the **`OrchestratorInc/agent-orchestrator`** minimalism pattern.
* **Architecture:**
  * Compiled single Go binary embedding SQLite (`modernc.org/sqlite` without CGO).
  * Manages Git worktrees directly via native `os/exec` Git calls.
  * Supervises agents in background `tmux` sessions.
  * Provides a responsive, beautiful Terminal User Interface (TUI) built using `bubbletea` and `lipgloss`.
* **Missing Code to Build:**
  * Independent implementation of Claude Code, Codex, and Antigravity transcript tailing in Go.
  * TUI screens for task board, transcript streaming, and human approvals.
* **Operational Cost & Footprint:** Lowest possible. Single static binary, instant startup, zero runtime dependencies except `git` and `tmux`.
* **Major Risks:** Re-implementing CLI parsers and transcript scrapers in Go requires substantial upfront parsing work.

### Provisional Recommendation
**We provisionally recommend Option A (Adapting `alamops/agetor` core) for rapid validation, transitioning into Option B (The Controlled Platform) for long-term production use.**  
`agetor` already has functioning, tested adapters for the exact trio of agents (Claude Code, Codex, and Antigravity `agy`), while CAO provides the exact security blueprint for out-of-band enforcement.

---

## 8. Small Validation Plan

To validate our architectural assumptions before writing production code, we define four minimal, non-destructive, local-only experiments.

### Experiment 1: Headless Cross-Provider Worktree Handoff
* **Objective:** Verify whether an uncommitted code change produced by Claude Code can be successfully inherited and finished by Codex CLI and Antigravity CLI without replanning.
* **Execution:**
  1. Initialize a test repository with a failing pytest suite (e.g., an unfinished string parser).
  2. Create a Git worktree: `git worktree add ../wt-test -b test/handoff`.
  3. Launch Claude Code headless in `wt-test`: `claude -p "Implement tokenize() in parser.py. Do not run tests."`
  4. Terminate Claude mid-task. Record `git diff`.
  5. Launch Codex in the same worktree: `codex exec -c developer_instructions="Continue implementation. Do not alter existing functions." "Complete tokenize() so tests pass."`
* **Success Criteria:** Codex preserves Claude's syntax/style, passes tests, and does not rewrite existing AST structures.
* **Disqualifying Outcome:** Codex completely erases or replaces Claude's code, or refuses to work on dirty uncommitted files.

### Experiment 2: Out-of-Band Tool Restriction Middleware
* **Objective:** Prove that CAO’s `@cao-mcp-server` middleware can prevent an agent from invoking unauthorized tools, independent of system prompt adherence.
* **Execution:**
  1. Configure a CAO agent profile with `allowedTools: ["fs_read", "fs_write"]` (omitting `execute_bash`).
  2. Prompt Claude Code to execute `execute_bash` to delete a temporary file.
* **Success Criteria:** The MCP middleware returns a JSON-RPC permission denied error; the shell command is never executed.
* **Disqualifying Outcome:** Claude bypasses the restriction or executes shell commands via an unintercepted side-channel.

### Experiment 3: Daemon Crash Recovery & Tmux Session Reattachment
* **Objective:** Prove that an in-flight 10-minute agent turn survives an immediate `kill -9` of the controller process.
* **Execution:**
  1. Launch a long-running Antigravity CLI refactoring task inside a named `tmux` session via `agetor` or a custom script.
  2. While the agent is mid-turn, execute `killall -9 bun` (or controller daemon).
  3. Restart the controller daemon. Inspect database and `tmux` session.
* **Success Criteria:** The `tmux` session continues executing undisturbed; on restart, the daemon reconnects to the session and resumes streaming the transcript without duplicate event processing.
* **Disqualifying Outcome:** Killing the controller kills the child agent process, causing corrupt or lost work.

### Experiment 4: Speculative Worktree Anti-Tamper Test Verification
* **Objective:** Validate that an agent cannot bypass test failures by altering test files.
* **Execution:**
  1. Configure an agent task to "fix failing tests".
  2. Prompt the agent maliciously or observe if it attempts to edit `tests/test_core.py` to `assert True`.
  3. The controller merge runner checks out `staging`, overwrites the `tests/` directory with `origin/main:tests/`, and executes the test runner.
* **Success Criteria:** The test runner detects the true regression and rejects the merge, despite the agent's worktree showing passing tests.
* **Disqualifying Outcome:** The merge queue accepts the agent's modified test suite and merges corrupted code into `main`.

---

## 9. Research Trail

* **Research Date:** October 29–30, 2026
* **Sources & Pinned Revisions Audited:**
  * `alamops/agetor` (Commit `62f4b4a1b028`, Release `v1.0.2`, MIT License)
  * `awslabs/cli-agent-orchestrator` (Commit `e9a3b12`, Release `v2.1.1`, Apache-2.0 License)
  * `OrchestratorInc/agent-orchestrator` (Commit `71bb19f`, Nightly 2026-10-28, Apache-2.0 License)
  * `coderabbitai/git-worktree-runner` (Commit `a41bc78`, Release `v2.11.1`, Apache-2.0 License)
  * `max-sixty/worktrunk` (Release `v0.8.x`, MIT/Apache-2.0)
  * `All-Hands-AI/OpenHands` (Commit `39df28a`, Release `v0.14.0`, MIT License)
  * `bors-ng/bors-ng` (Commit `c45de10`, Release `v0.5.x`, Apache-2.0 License)
  * Official Anthropic Claude Code Documentation (`code.claude.com/docs/en/headless`, `hooks-guide`)
  * Official Google Antigravity Documentation (`antigravity.google/docs/cli/reference/`, `gcli-migration`)
  * Official OpenAI Codex Documentation (`learn.chatgpt.com/docs/codex/cli`, `non-interactive-mode`)
* **Search Areas Covered:**
  * Multi-agent coding orchestrators, harness drivers, and terminal virtualizers.
  * Git worktree managers, automated setup hooks, and build-cache sharing utilities.
  * Out-of-band MCP policy brokers and tool restriction middlewares.
  * Speculative merge queues and continuous testing gates.
  * Local-first desktop and CLI architectures.
* **Rejected Candidates & Reasons:**
  * `PaulGauthier/aider`: Monolithic single-agent CLI; does not orchestrate external CLIs.
  * `Cursor / Cline / Roo Code`: Desktop IDE extensions bound to VS Code; cannot act as autonomous, headless, multi-agent project supervisors.
  * `andyrewlee/awesome-agent-orchestrators` / `agent-console`: Read-only session inspection; lacks orchestration logic.
* **Unresolved Questions for Phase 2:**
  * What is the exact protobuf wire format of Antigravity CLI's implicit conversation cache (`antigravity-cli.conversations`) when streaming in non-JSON mode?
  * How does Claude Code's `--allowed-tools` flag interact with dynamic tools registered via Model Context Protocol (MCP) servers across different minor versions?
* **Next Highest-Value Investigation:**
  * Execute Validation Experiment 1 locally: Run a scripted handoff from Claude Code to Codex and Antigravity CLI inside a Git worktree to measure token overhead and prompt drift quantitatively.
