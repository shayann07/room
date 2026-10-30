# Room

Room is an open-source local-first group room for a person, Claude Code, Codex,
and Google Antigravity. The approved visual prototype remains in
[`docs/room.html`](docs/room.html).

The product direction is documented in [`docs/ROOM_BATON_DESIGN.md`](docs/ROOM_BATON_DESIGN.md):
one shared project conversation with a durable baton for authority, assignments,
decisions, and continuation when a provider becomes unavailable.
The deeper coordination model is [`docs/ROOM_CONVERGENCE_KERNEL.md`](docs/ROOM_CONVERGENCE_KERNEL.md):
Room compiles authoritative state into verifiable turn packets so a provider's
hidden session is never the source of truth.
The connector boundary is [`docs/ROOM_LINK_PROTOCOL.md`](docs/ROOM_LINK_PROTOCOL.md):
Room Link uses a small local HTTP/event protocol; MCP is optional compatibility,
not a product requirement.

Repository: [github.com/shayann07/room](https://github.com/shayann07/room)

## M0 disposable proof

Run the local-only simulated proof with:

```powershell
python m0_harness.py
python -m unittest -v
python m0_harness.py --dry-run
python -m unittest -v
```

The harness writes JSON evidence to `artifacts/m0/`: a capability matrix,
durable room events, delivery receipts, a fixture transcript, a donor/license
ledger, and a pass/fail record. It does not
start a model turn or app-server session, inspect credentials, make network
requests, or claim that an idle provider can be woken. Its optional executable
probe only invokes `--version` and `--help`. A local executable being present is
only a machine observation; it is not a supported connection result.

The room proof also persists idempotency keys: retrying the same assignment
returns the original event instead of creating duplicate work.

Simulated agent posts also pass through a fixed participant-identity guard;
unknown authors are rejected. This is a fixture invariant, not a substitute
for authenticated provider credentials.

`room_http.py` provides the disposable localhost facade used by the integration
tests. It is deliberately bound to loopback and has no production
authentication; its purpose is to prove that separate local clients share the
same durable event store.

The dry-run adapter plans show the candidate launch/resume surfaces inferred
from local help output. They are plans only (`executed: false`) until a
user-authorized disposable provider test is run.

The current M0 evidence also includes a locally generated Codex app-server
schema bundle under `artifacts/m0/codex-schema/`. It verifies protocol types for
thread and turn lifecycle operations without starting a model turn.

The host check also found that WSL is not installed, so the planned
Windows-to-WSL managed runtime still needs a separate machine setup test.

The earlier M0 experiment registered an MCP-shaped fixture and captured its
approval limits. That experiment is retained as evidence only; MCP is not a
Room requirement. Room Link is the canonical connector boundary.

The guarded live runner is `live_smoke_runner.py`; it requires the explicit
`--confirm LIVE_M0` token and uses disposable working directories.

`record_live_evidence.py` converts captured provider output into a separate live
evidence record and a labelled local bridge without launching any provider.

`room_link.py` provides the canonical local connector primitives used by the
new protocol design. `room_mcp.py` remains a compatibility fixture and does not
claim to wake idle sessions.

The old provider-specific registration commands remain under `artifacts/m0/`
as historical evidence and are not part of onboarding.

Run `python mcp_preflight.py` only when reproducing the historical MCP fixture;
it is not a Room Link health check.

Run `python build_m0_report.py` to regenerate the combined M0 capability matrix.
