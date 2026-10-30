# Live smoke evidence

These results came from the explicitly authorized bounded test on 30 October
2026. Each provider received one prompt in an empty disposable directory. The
prompt prohibited file edits, shell commands, MCP tools, and network access.

- Claude emitted structured initialization and rate-limit events, then rejected
  the turn with a seven-day usage limit. No acknowledgement was produced.
- Codex emitted four JSON events, returned `ROOM_M0_ACK`, exited successfully,
  and left its workspace unchanged.
- Antigravity emitted six stream-json events, returned `ROOM_M0_ACK`, exited
  successfully, and left its workspace unchanged.

The captured provider outputs are evidence of bounded CLI turns only. The
`live-bridge-receipts.json` file is a controller ingestion fixture; no native
Room MCP server was registered, and idle wake was not tested.

The handoff analysis keeps Claude's limit distinct from Codex's successful
probe. It does not claim that Codex continued Claude's work: the smoke prompt
carried no coding task or transferred task context.
