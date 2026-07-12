# Hunter Unified CTF / Reverse / Pentest Workflow

OpenTgtyLab is the persistent workspace for the `hunter_tools` Workflow Kernel. Hunter is the orchestrator; specialized MCP servers remain execution backends.

## Ownership

| Component | Responsibility |
|---|---|
| `hunter_tools` | intake, lane routing, phase gates, DAG/budget, hypotheses, findings, evidence registration, checkpoint/resume |
| OpenTgtyLab | case state, event log, JSON Schema, KB, artifacts, evidence manifests, reports and CI |
| `reverse_lab_tools` | PE/APK/firmware/protocol execution |
| `ghidra` | interactive native-code analysis |
| `jshook` | JavaScript/browser runtime analysis |
| Burp bridge | HTTP proof execution and capture |

Only `hunter_tools` is a Hunter MCP registration. Do not register legacy `hunter`.

## Workflow state

Each upgraded case can contain:

```text
cases/<slug>/workflow.json
cases/<slug>/workflow.events.jsonl
```

`workflow.json` follows `schemas/workflow-state-v2.schema.json`. The JSONL file is append-only and records workflow creation, transitions, decisions, hypotheses, evidence, findings and dead ends.

Canonical phases:

```text
intake -> triage -> map -> hypothesis -> deep-analysis -> validation -> evidence -> report -> final
```

Validation may return to hypothesis. Other phase skips are rejected by the state store.

Canonical lanes:

```text
web api source javascript pe apk firmware script document protocol capture pwn crypto mixed
```

## Migration and validation

```powershell
python scripts/misc/workflow_state.py migrate cases/<slug>/state.json `
  --output cases/<slug>/workflow.json

python scripts/misc/workflow_state.py validate cases/<slug>/workflow.json
```

Legacy state is preserved; migration creates a v2 derivative rather than rewriting the source.

## Multi-client checkpoints

`session_checkpoint.py` provides read-only adapters for Codex, Claude Code and OpenCode. It detects the format, extracts bounded tool calls/findings/next steps, attaches a small case delta, hashes the source and never edits the original session.

```python
from scripts.misc.session_checkpoint import build_unified_checkpoint
build_unified_checkpoint(session, output, case_state=current_workflow)
```

## Output contract

Backends should return compact envelopes containing:

- summary
- signals
- evidence/artifact references
- suggested next actions
- metrics

Large raw data remains on disk and is retrieved only on demand. Confirmed findings must link to evidence and the producing tool run.

## Policy modes

- `interactive`: user approves phase changes.
- `guided`: automatically perform bounded low-cost actions; ask only for expensive or ambiguous branches.
- `autopilot`: follow gates, budget, dead-end memory and proof-aware early stop without routine pauses.

CTF automation should define explicit success conditions such as a flag, derived input, reproducible request, patch or runtime proof.
