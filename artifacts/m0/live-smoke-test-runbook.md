# M0 live smoke test (pending authorization)

The local-only proof is complete enough to justify a very small live check, but
the check has not been run. It may consume subscription quota. It must be
authorized explicitly before starting.

The test uses a disposable directory and this exact prompt:

> Reply exactly `ROOM_M0_ACK`. Do not edit files, run shell commands, use MCP
> tools, or access the network.

Run one bounded turn through each provider's existing local interface. Do not
register an MCP server, change account settings, use account rotation, or use a
bypass-permission flag. Stop on any tool call, approval request, unexpected
credential path, or file change. Capture the provider's structured output,
terminal status, and any session identifier. A response proves only that one
turn completed; it does not prove idle wake or durable Room delivery.

The candidate interfaces and their local evidence are in
`dry-run-adapter-plans.json`, `capability-matrix.json`, and
`interface-probes/`. Codex's generated protocol schemas are under
`codex-schema/`.

After authorization, the result should be added as a separate live evidence
record. Existing simulated pass/fail results must not be overwritten or turned
into live claims.

The guarded runner is `live_smoke_runner.py`. It requires the literal
`--confirm LIVE_M0`; the intended invocation is:

```powershell
python live_smoke_runner.py --confirm LIVE_M0 --provider all
```

The runner stores one result directory per provider and records whether the
acknowledgement text appeared, whether structured JSON lines were observed, and
whether the disposable working directory changed.

After a run, `record_live_evidence.py` classifies the captured results and
creates `live-provider-results.json` plus a clearly labelled local bridge. The
bridge is an ingestion fixture; it must not be described as native MCP
connectivity.
