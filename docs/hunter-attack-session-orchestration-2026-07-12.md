# Hunter AttackSession Orchestration Upgrade

## Repositories

- Hunter feature commit: `d26c2c6`
- Hunter follow-up fix: `0ce6df4`
- Branch: `main`
- MCP server: `hunter_tools`
- Registered tools: `94`

## Delivered

Hunter now provides a persistent multi-step assessment layer:

- encrypted `AttackSession` state and checkpoints;
- CookieJar domain/path/expiration semantics;
- CSRF, JWT, API-key, form, redirect, and message extraction;
- verified authentication evidence;
- YAML/JSON `AttackChain` graph validation and resumable cursors;
- request, extract, condition, exploit-plan, and wait actions;
- bounded retries, payload variants, and strategy metadata;
- critical-step blocker checkpoints;
- six preset chain templates;
- five attack-session MCP APIs.

`hunter_session_state` remains backward compatible: `target` addresses the
existing Stealth session, while `session_id` addresses the new AttackSession.

## Boundaries

- Every AttackSession owns an isolated HTTP client and state directory.
- Requests are checked against allowed origins and methods before transport.
- Chain redirects are explicit rather than automatically followed.
- Sensitive state is Fernet-encrypted on disk and redacted in MCP responses.
- Arbitrary cookies do not count as authentication.
- Planning statuses pause the state machine rather than entering success paths.
- Caller-supplied approval data cannot create a trusted `ready` state. A host
  must provide an independent approval verifier backed by its operator and
  evidence registry.
- High-impact actions remain deferred; the planner does not directly write
  shells, establish reverse connections, persist through Redis, or access
  metadata endpoints.

## Verification

```text
Hunter full suite: 261 passed in 4.89s
JS analysis focused suite: 41 passed in 1.14s
FastMCP registry: 94
Contract: ok
Missing tools: []
Final focused review: Go
```

Runtime evidence:

```text
D:\Open-tgtylab\cases\hunter-skill\state.json
D:\Open-tgtylab\exports\notes\hunter-skill\attack-session-orchestration-2026-07-12.md
D:\Open-tgtylab\exports\reports\hunter-skill\attack-session-orchestration-2026-07-12.md
```
