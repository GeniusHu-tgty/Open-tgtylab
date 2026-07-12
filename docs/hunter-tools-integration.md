# Hunter `hunter_tools` + OpenTgtyLab Integration

OpenTgtyLab keeps web-security automation in the independent `Hunter` repository and integrates it through one MCP server named **`hunter_tools`**. Do not register the legacy `hunter` name.

## Responsibilities

- `hunter_tools`: web/API recon, vulnerability analysis, payloads, Burp proof plans, sessions, reports, and OpenTgtyLab workspace coordination.
- `reverse_lab_tools`: project KB routing plus PE/APK/Frida/Ghidra and general reverse-engineering workflows.
- Shared contract: `cases/<slug>/state.json`, project KB, and evidence/note/report artifact paths.

## Required environment

Set `OPEN_TGTYLAB_ROOT` to the absolute checkout path. The Hunter adapter also accepts `OPEN_TGTYLAB_WORKSPACE` or `TGTYLAB_ROOT`, but the canonical variable is `OPEN_TGTYLAB_ROOT`.

The Hunter entrypoint is installed separately at:

```text
~/.agents/skills/hunter/mcp_server.py
```

Clone/update it from `https://github.com/GeniusHu-tgty/Hunter` before enabling the MCP registration.

## Recommended flow

1. `hunter_workspace_health`
2. `hunter_case_open` / `hunter_case_next_steps`
3. `hunter_project_kb_search` -> `hunter_project_kb_read`
4. Hunter/Burp proof tools
5. `hunter_evidence_save`
6. `hunter_note_write` / `hunter_report_publish`
7. `hunter_case_update`

HTTP execution remains `Burp send_http2_request` first and `http_probe` second. Hunter's Burp tools package explicit actions and evidence plans; they do not duplicate another MCP server.

## Verification

Run:

```powershell
python scripts/misc/verify_hunter_tools_integration.py
```

The check fails if `hunter` is registered, if `hunter_tools` is absent, if the entrypoint is missing, or if workspace health cannot be obtained.
