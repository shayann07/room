# Simple Room design

The previous baton, sidecar, and convergence-kernel designs were useful
reviews, but they are too much machinery for the first real product. The
problem can be solved with one shared local room and one tiny command surface.

## The product

Room is a durable project chat backed by one SQLite file. Each existing Claude,
Codex, and Antigravity project receives the same short Room instruction:

> Before acting, read the current Room messages. After acting, post what you
> did, what you need, and whether the assignment is complete. Treat accepted
> decisions and assignments in Room as binding.

The provider still runs its own normal session and tools. Room does not create
or supervise sessions.

## Three commands

The connector surface is intentionally only:

```text
room read <project> [--after CURSOR]
room say <project> --as PARTICIPANT --text TEXT
room claim <project> --as PARTICIPANT --task TASK
```

`room read` prints the latest compact room state and new messages. `room say`
posts an authenticated message. `room claim` atomically records ownership so
two agents cannot take the same assignment. Everything else is ordinary chat.

The UI calls these same operations. There is no second protocol for models,
no provider-specific authority system, and no requirement that an agent call a
tool exposed inside its prompt.

## Why this is better now

- A quota hit leaves the conversation intact; the next agent runs `room read`
  and continues.
- A returning Claude session sees the same messages as Codex and Antigravity.
- The user can inspect exactly what each agent saw and posted.
- A SQLite transaction handles claims and duplicate posts.
- Provider integration is reduced to project instructions plus a local command;
  MCP, plugins, SDKs, and session automation are optional enhancements.
- There is no invented scheduler that can claim it woke an idle model.

## Authority rule

Room messages are binding only when they are typed as an assignment or
accepted decision. Plain discussion is visible but cannot change task state.
The user owns acceptance and integration. A lead may assign only inside the
scope granted by the user. If the lead is unavailable, the user appoints a new
lead in Room; the next agent does not guess.

## Honest limit

No software can make an idle provider run without a supported provider hook.
This design does not pretend otherwise. It makes the common case cheap and
reliable: whenever an agent is active, it reads the same room before work and
posts back after work. If no agent is active, Room shows queued work and waits
for the next existing session.

## Migration

`room_kernel.py`, `room_link.py`, and the MCP fixture remain useful experiments,
but they are not required for the core user flow. The next implementation
should expose the three commands over the existing SQLite backend and test a
simulated quota switch from Claude to Codex.
