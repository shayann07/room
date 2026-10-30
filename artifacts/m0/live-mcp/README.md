# Registered MCP smoke evidence

This directory is reserved for the authorized test through the registered
`room-m0` MCP server. The prompt asks one provider turn to call `room_post`
once with `LIVE_MCP_ACK` and make no file or shell changes.

The test proves native Room tool delivery only if the provider output shows the
tool result and the SQLite room contains the posted event. It does not prove
idle wake.

The recorded result distinguishes tool discovery and attempted calls from actual
delivery. A model's text acknowledgement is not evidence that `room_post`
executed; the SQLite event is authoritative.
