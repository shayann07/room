# Room

Room is an open-source local-first group room for a person, Claude Code, Codex,
and Google Antigravity. The approved visual prototype remains in
[`docs/room.html`](docs/room.html).

The product direction is documented in [`docs/ROOM_BATON_DESIGN.md`](docs/ROOM_BATON_DESIGN.md):
one shared project conversation with a durable baton for authority, assignments,
decisions, and continuation when a provider becomes unavailable.
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

MCP enrollment help was also captured for all three tools. The commands exist,
but no Room MCP server was registered; enrollment, active-turn delivery, and
idle wake remain live-test questions.

The guarded live runner is `live_smoke_runner.py`; it requires the explicit
`--confirm LIVE_M0` token and uses disposable working directories.

`record_live_evidence.py` converts captured provider output into a separate live
evidence record and a labelled local bridge without launching any provider.

`room_mcp.py` provides the disposable stdio MCP-shaped connector used by the
local tests. It is not registered with provider tools yet and does not claim to
wake idle sessions.

The provider-specific registration commands are documented in
`artifacts/m0/mcp-enrollment-plan.json`; they have not been executed.

The registration plan uses the SQLite/WAL backend through
`room_mcp.py --store sqlite`; the JSON store remains only for fixture
compatibility.

Run `python mcp_preflight.py` to verify the unregistered connector and the dry-run
templates locally.

Run `python build_m0_report.py` to regenerate the combined M0 capability matrix.
