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

## Integration v2 lifecycle

Use the cross-platform manager instead of editing MCP paths manually:

```bash
# Clone Hunter when missing, update it when present, configure this checkout,
# configure the user's Codex MCP registry, then verify the bridge.
python scripts/misc/hunter_tools_manager.py install --global-codex

# Fast-forward an existing Hunter checkout and re-apply idempotent config.
python scripts/misc/hunter_tools_manager.py update --global-codex

# Diagnose repository, contract, entrypoint and integration state.
python scripts/misc/hunter_tools_manager.py doctor
```

Optional overrides make the workflow portable:

```bash
python scripts/misc/hunter_tools_manager.py install \
  --root /path/to/Open-tgtylab \
  --hunter-dir /path/to/hunter \
  --python /path/to/python \
  --global-codex
```

The manager removes the legacy `hunter` registration, writes only `hunter_tools`, injects the resolved `OPEN_TGTYLAB_ROOT`, and is idempotent. A changed global Codex configuration reports `restart_required=true`.

## Codex security-research checkpoints

Long security tasks can be resumed without replaying the entire Codex JSONL session:

```bash
python scripts/misc/codex_security_checkpoint.py --latest \
  --output exports/checkpoints/current.checkpoint.json
```

The adapter reads Codex session metadata, token counters, tool calls, bounded outputs, findings, and next steps. It writes a compact checkpoint with source SHA-256 and a resume hint. It never edits the original session. Use `--dry-run` to preview metrics and `--no-backup` to disable output backup rotation.

This follows the useful adapter/backup/diff principles observed in `ryfineZ/codex-session-patcher`, while keeping OpenTgtyLab focused on evidence-grounded research continuity rather than rewriting model responses.

## Evidence manifest

Register case artifacts in a deduplicated, hash-addressed manifest:

```bash
python scripts/misc/evidence_manifest.py \
  --manifest exports/evidence/<case>/manifest.json \
  --case <case> \
  --artifact exports/evidence/<case>/request.txt \
  --tool hunter_auto_idor \
  --type http-request \
  --finding-id idor-1
```

Artifacts must remain inside the case evidence directory. Entries include stable evidence id, relative path, SHA-256, byte size, producing tool, finding linkage and UTC timestamp. Re-registering the same path/hash is idempotent.

## Unified CTF / reverse / pentest workflow

See `docs/hunter-unified-workflow.md` for Workflow State v2, event sourcing, lane/phase contracts, multi-client checkpoints, backend responsibilities and migration commands.
