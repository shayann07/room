# Room intelligent UI

Room is a local web/desktop application. It is not a skill. Optional provider
instructions, hooks, or connectors help Claude Code, Codex, and Antigravity
participate, but the product is the Room app and its durable project state.

## Agent-authored UI without arbitrary model-generated pages

Agents can attach a typed `surface` event to a room message. The app renders a
known component from a validated schema:

```json
{
  "surface": "handoff",
  "title": "Claude reached its limit",
  "severity": "warning",
  "actions": ["open_wip", "assign_steward"],
  "data": {"from": "claude", "to": "codex", "task": "T-03"}
}
```

Initial surfaces:

- `assignment`: owner, scope, acceptance check, status;
- `handoff`: provider stop, WIP, steward, next action;
- `decision`: locked rule, proposal, impact, owner action;
- `question`: target, blocking scope, answer action;
- `evidence`: tests, candidate, diff, unresolved concerns;
- `acceptance`: owner review, stale reason, accept/request-changes;
- `provider_status`: verified receipt, last check-in, capability limits.

The agent may choose a surface and fill its data, but cannot submit HTML,
JavaScript, arbitrary buttons, or an action outside its authority. Room validates
the surface schema and permission of each action. The same event remains useful
as plain chat if a client does not support the surface.

## Visual direction

The prototype should keep its organic restraint while gaining enough contrast
for engineering work:

- warm paper for conversation;
- deep graphite navigation and code/status surfaces;
- moss for aligned/approved state;
- amber for handoff, waiting, and attention;
- blue for provider activity and evidence;
- red only for blocked or failed work.

Responsive behavior must preserve the core truth on small screens: the current
assignment, authority, and provider status remain visible before the transcript.
The right panel becomes a bottom sheet or stacked section instead of silently
disappearing.
