# Hunter and OpenTgtyLab Integration Hardening Design

**Date:** 2026-07-13

**Goal:** Correct the workflow-integrity, approval, recovery, deployment,
configuration, and documentation defects found during the joint Hunter and
OpenTgtyLab review without weakening existing authorization boundaries or
breaking the current MCP contract.

## Scope

This change covers:

- Hunter workflow event persistence and checkpoint recovery.
- Unified orchestrator approval, evidence, rerun, and policy behavior.
- OpenTgtyLab workflow-store compatibility and durability.
- Hunter integration verification, lifecycle-manager exit codes, and CI.
- Project and global MCP configuration consistency.
- Repository hygiene, deleted payload restoration, and current documentation.

It does not add new exploitation capabilities, execute target requests, or
change the existing requirement that external and high-impact actions remain
explicitly authorized.

## Architecture

### Shared workflow locking

Hunter and OpenTgtyLab will use the same per-workflow lock-file convention.
Every read-modify-append-materialize operation will execute under an exclusive
cross-process lock.

The lock must:

- Work on Windows and Unix with standard-library facilities or a small local
  compatibility helper.
- Cover revision calculation, previous-hash selection, event append, fsync,
  state materialization, and atomic state replacement.
- Use unique temporary state filenames so unrelated writers cannot collide.
- Have a bounded acquisition timeout and produce an explicit lock-timeout
  error instead of silently corrupting state.
- Be re-entrant inside one process so orchestration code can call materialize
  while already holding the workflow lock.

OpenTgtyLab's `WorkflowStore.load()` will materialize state from the validated
event stream rather than trusting a potentially stale `workflow.json`.
`workflow.json` remains a derived cache.

### Approval binding

An approval will authorize one exact confirmation request, not an entire
stage. Hunter will create a deterministic digest from the normalized stage,
tool, target, arguments, and requested scope.

The confirmation response must include the digest or decision identifier
returned by the pending confirmation. Approval is valid only when:

- The stage matches.
- The confirmation digest matches.
- The requested action is within the approved scope.
- The approval was recorded after the confirmation request was created.
- The approval has not already been consumed.

Potentially side-effecting adapters will not run before approval. Adapters
must first return a deferred confirmation descriptor; execution remains an
external handoff after approval.

### Evidence transaction ordering

A stage is complete only after all durable outputs have succeeded.

For `evidence_learning`, Hunter will:

1. Start the stage.
2. Build and validate the stage result.
3. Register evidence and findings idempotently.
4. Persist the stage-completed event.
5. Save the checkpoint.

Evidence and findings receive deterministic orchestration keys so retrying
after interruption cannot create duplicates. Any failure before completion is
recorded as interrupted or blocked and remains resumable.

### Resume and fresh-run semantics

Checkpoint resume continues to validate the selected checkpoint and replay a
valid event tail. A corrupt tail is truncated to the checkpoint boundary,
including tails that contain invalid UTF-8.

`hunter_auto_pentest` and orchestration-mode `hunter_workflow_run` gain explicit
run semantics:

- `resume=true`: continue the first incomplete stage.
- `fresh_run=true`: create a new generation for the same target.
- Neither option: return a completed prior generation when configuration is
  unchanged; start a new generation when mode, profile, modules, or objective
  changed.

Existing workflows will apply requested mode changes through
`WorkflowKernel.set_policy`. A generation identifier is included in persisted
orchestrator metadata and output.

### Integration verification

OpenTgtyLab's verifier will inspect:

- `.mcp.json` and `.codex/config.toml` registration names, entrypoints, and
  workspace roots.
- The Hunter integration contract and every required tool.
- The actual FastMCP registry, not only Python callables.
- Minimum tool count and version fields.
- Hunter workspace health against the exact OpenTgtyLab checkout being
  verified.

The lifecycle manager will propagate nested verification failures to its
process exit code for `install`, `update`, and `doctor`. CI will run full
integration verification in addition to unit tests and static configuration
checks.

### Configuration and repository cleanup

The global Codex configuration will retain only `hunter_tools`; the legacy
`hunter` registration will be removed. Project configurations will resolve the
same workspace root and avoid committed machine-specific paths where the
client supports variables.

The deleted file-upload payload reference will be restored from Git history.
Tracked bytecode files will be removed from the index while remaining ignored.
Corrupted `SKILL.md` content and current tool-count documentation will be
rewritten in valid UTF-8. Historical dated reports retain their historical
counts when clearly labeled as snapshots.

## Compatibility

- Existing workflow event schema version `1.0` and state schema version `2.0`
  remain readable.
- New event payload fields are additive.
- Legacy stage-level approvals are treated as untrusted and require a new
  confirmation.
- Existing completed workflows remain inspectable.
- The MCP tool count remains 111 unless implementation introduces an
  explicitly approved new tool.

## Testing

Hunter tests will cover:

- Concurrent writers across independent kernel instances.
- Approval digest and scope matching, pre-approval rejection, consumption,
  and changed-action rejection.
- Evidence-registration failure followed by successful resume.
- Invalid UTF-8 event-tail recovery.
- Mode/profile/module updates and fresh generations for the same target.
- Existing checkpoint-tail replay compatibility.

OpenTgtyLab tests will cover:

- Concurrent `WorkflowStore` writers.
- Event-based recovery from a stale materialized state.
- Full 111-tool contract and FastMCP registry verification.
- Entrypoint and workspace-path mismatch failures.
- Nonzero manager exit codes on nested verification failure.
- CI invoking the full verifier.

Final verification requires:

- Full Hunter test suite.
- Full OpenTgtyLab test suite.
- Hunter contract check with 111 registered and no missing tools.
- Hunter doctor with no legacy registration error.
- Integration verifier and lifecycle-manager doctor returning exit code zero.
- Git diff checks confirming no payload deletion or tracked bytecode changes.
- Remote push verification for both repositories.

## Migration and Failure Handling

No destructive migration runs automatically. Locks and new approval metadata
are introduced lazily on the next workflow operation. Before changing global
configuration, the manager preserves its existing backup behavior.

If a workflow lock times out, if an event tail cannot be repaired from the
requested checkpoint, or if the configured workspace differs from the
verified checkout, the operation fails explicitly and does not report success.
