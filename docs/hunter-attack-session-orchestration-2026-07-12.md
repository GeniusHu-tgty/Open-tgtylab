# Hunter AttackSession Orchestration Upgrade

## Repositories

- Hunter feature commit: `d26c2c6`
- Hunter follow-up fix: `0ce6df4`
- Hunter final hardening: `bddc462`
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
- Mutating requests persist an in-flight marker and require manual recovery
  instead of being replayed after an uncertain crash.
- MCP results contain hashed response summaries rather than raw response bodies,
  query tokens, redirect tokens, or error text.
- Captcha image requests are origin-scoped, do not follow redirects, and retain
  only non-credential browser headers across approved origins.
- Caller-supplied approval data cannot create a trusted `ready` state. A host
  must provide an independent approval verifier backed by its operator and
  evidence registry.
- High-impact actions remain deferred; the planner does not directly write
  shells, establish reverse connections, persist through Redis, or access
  metadata endpoints.

## Verification

```text
Hunter full suite: 269 passed
Security-focused suite: 95 passed
FastMCP registry: 94
Contract: ok
Missing tools: []
Final focused review: passed
```
