# Hunter JavaScript and Attack Session Upgrade — 2026-07-13

## Result

- Hunter repository: [GeniusHu-tgty/Hunter](https://github.com/GeniusHu-tgty/Hunter)
- Branch: `main`
- Final commit: [`bddc462`](https://github.com/GeniusHu-tgty/Hunter/commit/bddc462)
- Supporting commits: `d26c2c6`, `0ce6df4`
- MCP server: `hunter_tools`
- Registered tools: 94
- Full test suite: 269 passed
- Integration contract: ok
- Hunter doctor: ok

## JavaScript deep analysis

- Detects Webpack, Webpack 5, Vite, Rollup, Parcel, esbuild, and Turbopack.
- Extracts Webpack module tables and logical Vite/Rollup module boundaries.
- Writes module files and dependency/export trees.
- Performs conservative string decoding, dead-branch removal, control-flow recovery, IIFE expansion, and contextual identifier recovery.
- Extracts HTTP APIs, WebSocket formats, framework routes, and authentication signals.
- Scores signature candidates, reconstructs supported canonicalization, traces key sources, and accepts JSHook observations.
- Generates signing-only scaffolds unless a complete observed request context is available.
- Generates transport replay only from observed method, URL, headers, and parameter placement.
- Blocks private-network URL analysis by default; private access requires explicit operator configuration.
- Pins remote JavaScript retrieval to the validated DNS result, validates every redirect, and enforces script-count and cumulative-size limits.

## Persistent attack sessions

- Encrypts persisted Cookie, CSRF, auth-token, authorization, extracted-data, and cursor state using authenticated local encryption.
- Separates internal snapshots from redacted MCP-facing snapshots.
- Enforces authorized origins and HTTP methods.
- Requires session-scoped approval and matching evidence before post-exploitation planning.
- Supports YAML/JSON attack chains, retries, branching, extraction, blockers, and checkpoints.
- Persists an in-flight marker before requests.
- Refuses to replay unresolved mutating requests after recovery.
- Allows safe GET/HEAD recovery without repeating completed steps.
- Returns hashed response summaries instead of raw bodies, sensitive headers, query tokens, or error text.

## Security review closure

- Approval-required and blocked domain states propagate through MCP responses.
- Captcha image retrieval is origin-scoped, does not follow redirects, and strips non-safe headers across origins.
- Generated replay scripts disable automatic redirects.
- Attack-session HTTP clients do not persist Cookie or CSRF data in plaintext.
- Private JavaScript analysis requires both an explicit tool parameter and operator environment authorization.

## Verification

```text
269 passed
registered tools: 94
missing required tools: []
integration verification: ok
hunter doctor: ok
```
