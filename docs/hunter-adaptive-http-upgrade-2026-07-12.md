# Hunter Adaptive HTTP Upgrade ? 2026-07-12

## Result

- Hunter repository: `C:\Users\Administrator\.agents\skills\hunter`
- Branch: `main`
- Commit: `34822d16f6515886b3250be47d4039df72594e05`
- GitHub: https://github.com/GeniusHu-tgty/Hunter/commit/34822d16f6515886b3250be47d4039df72594e05
- MCP server name: `hunter_tools`
- Registered tools: 90
- Full test suite: 188 passed
- Hunter doctor: ok; missing tools: none
- MCP smoke: session persistence ok, fingerprint consistency true, proxy pool 2 entries, contract ok, health ok

## Delivered

- `core/stealth/fingerprint_manager.py`
- `core/stealth/waf_detector.py`
- `core/stealth/rate_limiter.py`
- `core/stealth/captcha_handler.py`
- `core/stealth/proxy_pool.py`
- `core/stealth/stealth_http_client.py`
- MCP tools: `hunter_stealth_request`, `hunter_stealth_scan`, `hunter_session_create`, `hunter_session_state`, `hunter_set_proxy_pool`
- JavaScript analysis pipeline preserved and integrated into the same 90-tool contract.

## Final review fixes

- Applied WAF strategy failures are recorded before retry.
- 503 handling is unified and requires rate-limit evidence.
- Rate probes evaluate each response's own headers/body.
- Proxy failures and audit timeline remain attributed to the actual request proxy.
- Rate-limit failures are counted once and backoff begins at 1 second.
- HTML captcha pages resolve and fetch the real image in the same session/proxy context, retry OCR up to three times, then resubmit the business request.
- Payload WAF blocks no longer automatically mark a proxy IP as target-banned.
- Session writes use atomic replacement; timeline, steps, and OAuth windows are bounded.

## Verification evidence

```text
188 passed in 3.35s
hunter_doctor: status=ok, registered_tool_count=90, missing_tools=[]
MCP smoke: session=ok, consistent=true, proxies=2, contract=ok, count=90, missing=[], health=ok
```
