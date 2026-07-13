# Hunter and OpenTgtyLab Integration Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Hunter and OpenTgtyLab workflow persistence, approvals, recovery,
reruns, integration verification, configuration, and repository state reliable
under concurrent and interrupted operation.

**Architecture:** Add matching per-workflow cross-process lock helpers to both
projects and keep `workflow.json` as a derived event-log cache. Bind approvals
to deterministic confirmation descriptors, complete evidence stages only after
durable registration, and represent repeated target runs as explicit workflow
generations. Strengthen OpenTgtyLab verification so deployment and CI validate
the real 111-tool FastMCP contract and exact workspace.

**Tech Stack:** Python 3.11+, standard-library file locking (`msvcrt`/`fcntl`),
FastMCP registry introspection, JSON/TOML, pytest, GitHub Actions.

---

### Task 1: Hunter Concurrent Workflow Locking

**Files:**
- Create: `C:\Users\Administrator\.agents\skills\hunter\core\workflow\locking.py`
- Modify: `C:\Users\Administrator\.agents\skills\hunter\core\workflow\kernel.py:39-95`
- Test: `C:\Users\Administrator\.agents\skills\hunter\tests\test_workflow_kernel.py`

- [ ] **Step 1: Write failing concurrent-writer tests**

Add tests that create independent `WorkflowKernel` instances and append 32
hypotheses concurrently. Assert that all calls succeed, revisions are
`1..33`, hashes form one chain, and `materialize()` returns 32 hypotheses.

```python
def test_concurrent_kernel_instances_preserve_event_chain(tmp_path):
    WorkflowKernel(tmp_path).create("race", "proof", [])
    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = [
            pool.submit(WorkflowKernel(tmp_path).add_hypothesis, "race", f"h-{i}")
            for i in range(32)
        ]
        assert [future.result() for future in futures]
    events = read_events(tmp_path / "cases" / "race" / "workflow.events.jsonl")
    assert [event["revision"] for event in events] == list(range(1, 34))
    assert len(WorkflowKernel(tmp_path).materialize("race")["hypotheses"]) == 32
```

- [ ] **Step 2: Run the test and verify the current race**

Run:

```powershell
python -m pytest tests/test_workflow_kernel.py::test_concurrent_kernel_instances_preserve_event_chain -q
```

Expected: FAIL with duplicate revisions or `event chain mismatch`.

- [ ] **Step 3: Implement `WorkflowFileLock`**

Implement a context manager with:

```python
class WorkflowFileLock:
    def __init__(self, path: Path, timeout: float = 10.0): ...
    def __enter__(self) -> "WorkflowFileLock": ...
    def __exit__(self, exc_type, exc, tb) -> None: ...
```

Use a process-local `threading.RLock` per resolved lock path and a thread-local
depth/handle map. The outermost acquisition locks byte zero of
`.workflow.lock` with retry/backoff; nested acquisitions reuse the handle.
Raise `TimeoutError("workflow lock timeout: <path>")` after the deadline.

- [ ] **Step 4: Lock Hunter event transactions**

Add `WorkflowKernel._lock(slug)` and hold it across `_append`, `checkpoint`, and
checkpoint-tail repair. Generate materialized-state temp files with
`.<pid>.<thread-id>.tmp` suffixes before `os.replace`.

- [ ] **Step 5: Run focused and kernel regression tests**

```powershell
python -m pytest tests/test_workflow_kernel.py -q
```

Expected: all workflow-kernel tests pass.

- [ ] **Step 6: Commit**

```powershell
git add core/workflow/locking.py core/workflow/kernel.py tests/test_workflow_kernel.py
git commit -m "fix: serialize workflow event transactions"
```

### Task 2: Checkpoint Tail Recovery

**Files:**
- Modify: `C:\Users\Administrator\.agents\skills\hunter\core\workflow\kernel.py:248-332`
- Modify: `C:\Users\Administrator\.agents\skills\hunter\tests\test_orchestrator.py`
- Test: `C:\Users\Administrator\.agents\skills\hunter\tests\test_workflow_kernel.py`

- [ ] **Step 1: Write an invalid UTF-8 recovery test**

```python
def test_checkpoint_resume_discards_invalid_utf8_tail(tmp_path):
    kernel = WorkflowKernel(tmp_path)
    kernel.create("utf8-tail", "proof", [])
    checkpoint = kernel.checkpoint("utf8-tail")
    with kernel._events("utf8-tail").open("ab") as handle:
        handle.write(b'{"partial":"\xff')
    resumed = kernel.resume("utf8-tail", checkpoint["checkpoint_id"])
    assert resumed["state"]["workflow_id"]
    assert resumed["state"]["resume_metadata"]["discarded_events"] >= 1
```

- [ ] **Step 2: Verify RED**

```powershell
python -m pytest tests/test_workflow_kernel.py::test_checkpoint_resume_discards_invalid_utf8_tail -q
```

Expected: FAIL with `UnicodeDecodeError`.

- [ ] **Step 3: Repair from bytes**

Read the event file with `read_bytes().splitlines(keepends=False)`. Attempt
normal materialization inside a handler that includes `UnicodeDecodeError`.
When repair is required, decode and validate only the checkpoint prefix, write
that prefix to a unique temporary file, fsync, and atomically replace the event
file. Preserve documented valid-tail replay behavior.

- [ ] **Step 4: Verify recovery and existing replay semantics**

```powershell
python -m pytest tests/test_workflow_kernel.py::test_checkpoint_resume_discards_invalid_utf8_tail tests/test_workflow_kernel.py::test_resume_replays_events_after_checkpoint tests/test_orchestrator.py::test_checkpoint_resume_recovers_from_corrupt_event_tail -q
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```powershell
git add core/workflow/kernel.py tests/test_workflow_kernel.py tests/test_orchestrator.py
git commit -m "fix: recover checkpoints from binary event tails"
```

### Task 3: Action-Bound Approval Model

**Files:**
- Modify: `C:\Users\Administrator\.agents\skills\hunter\core\workflow\kernel.py:123-170`
- Modify: `C:\Users\Administrator\.agents\skills\hunter\core\workflow\kernel.py:392-610`
- Modify: `C:\Users\Administrator\.agents\skills\hunter\tests\test_orchestrator.py`

- [ ] **Step 1: Write failing approval tests**

Add separate tests for:

- Approval without a pending confirmation is rejected.
- Approval for confirmation A does not authorize changed confirmation B.
- Scope mismatch is rejected.
- A consumed approval cannot authorize another action.
- The existing interactive confirmation flow succeeds when the exact returned
  `confirmation_id` and `confirmation_digest` are supplied.

Use the first response's descriptor:

```python
pending = first["confirmation_required"][0]
approval = {
    "stage": "vulnerability_confirmation",
    "approved": True,
    "decision_id": "analyst-001",
    "confirmation_id": pending["confirmation_id"],
    "confirmation_digest": pending["confirmation_digest"],
    "scope": pending["scope"],
}
```

- [ ] **Step 2: Verify RED**

```powershell
python -m pytest tests/test_orchestrator.py -k "approval or confirmation" -q
```

Expected: changed-action and pre-approval tests fail.

- [ ] **Step 3: Normalize confirmation descriptors**

Add helpers:

```python
def _confirmation_digest(stage: str, action: Mapping[str, Any]) -> str: ...
def _normalize_confirmations(stage: str, actions: Sequence[Any]) -> list[dict[str, Any]]: ...
def _validate_approval(self, state: Mapping[str, Any], approval: Mapping[str, Any]) -> dict[str, Any]: ...
def _is_confirmation_approved(state, stage, confirmation) -> bool: ...
```

Canonicalize JSON with sorted keys and compact separators. Include stage, tool,
target, arguments, and scope in the digest. Store `requested_at`, stable
`confirmation_id`, and `confirmation_digest`.

- [ ] **Step 4: Persist and consume exact approvals**

Materialize `orchestrator.approval.recorded` and
`orchestrator.approval.consumed`. Reject legacy stage-only approvals. On
resume, rerun the planning adapter, normalize its current confirmations, and
continue only when every descriptor has an unconsumed exact approval. A changed
descriptor returns `awaiting_confirmation` again.

- [ ] **Step 5: Verify all orchestrator tests**

```powershell
python -m pytest tests/test_orchestrator.py -q
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```powershell
git add core/workflow/kernel.py tests/test_orchestrator.py
git commit -m "fix: bind approvals to exact confirmation actions"
```

### Task 4: Evidence Completion Transaction

**Files:**
- Modify: `C:\Users\Administrator\.agents\skills\hunter\core\workflow\kernel.py:237-247`
- Modify: `C:\Users\Administrator\.agents\skills\hunter\core\workflow\kernel.py:632-665`
- Modify: `C:\Users\Administrator\.agents\skills\hunter\core\workflow\kernel.py:757-797`
- Modify: `C:\Users\Administrator\.agents\skills\hunter\tests\test_orchestrator.py`

- [ ] **Step 1: Write failure-and-resume tests**

Inject a kernel whose first evidence registration raises `OSError`. Assert:

- The first run is blocked/interrupted.
- `evidence_learning` is not completed.
- Resume registers evidence/findings.
- Exactly one evidence and one finding exist after retry.

- [ ] **Step 2: Verify RED**

```powershell
python -m pytest tests/test_orchestrator.py -k "evidence_registration_failure" -q
```

Expected: FAIL because the stage is already completed.

- [ ] **Step 3: Add idempotency keys**

Extend `register_evidence` and `promote_finding` with optional
`dedupe_key=""`. Return the existing matching item when the key already exists.
The orchestrator computes keys from workflow ID, stage, finding identity, and
evidence summary.

- [ ] **Step 4: Reorder durable operations**

For `evidence_learning`, call:

```python
self._register_evidence_and_findings(slug, safe_result)
self.kernel._append(slug, "orchestrator.stage.completed", ...)
self.kernel.checkpoint(...)
```

Keep registration inside the stage exception boundary so failure produces a
resumable blocked/interrupted state.

- [ ] **Step 5: Verify**

```powershell
python -m pytest tests/test_orchestrator.py tests/test_workflow_kernel.py -q
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```powershell
git add core/workflow/kernel.py tests/test_orchestrator.py tests/test_workflow_kernel.py
git commit -m "fix: complete evidence stages transactionally"
```

### Task 5: Workflow Generations and Policy Updates

**Files:**
- Modify: `C:\Users\Administrator\.agents\skills\hunter\core\workflow\kernel.py:444-514`
- Modify: `C:\Users\Administrator\.agents\skills\hunter\mcp_server.py:3089-3191`
- Modify: `C:\Users\Administrator\.agents\skills\hunter\tests\test_orchestrator.py`
- Modify: `C:\Users\Administrator\.agents\skills\hunter\tests\test_workflow_mcp.py`

- [ ] **Step 1: Write failing MCP behavior tests**

Test:

- Existing interactive workflow changes to autopilot when requested.
- Existing autopilot workflow changes to interactive when requested.
- Same completed target with changed profile/modules creates a new generation.
- `fresh_run=true` always creates a new generation.
- `resume=true` keeps the existing slug and first incomplete stage.

- [ ] **Step 2: Verify RED**

```powershell
python -m pytest tests/test_orchestrator.py tests/test_workflow_mcp.py -k "mode or generation or fresh_run" -q
```

- [ ] **Step 3: Add generation metadata**

Persist:

```python
"generation": {
    "id": "gen-<uuid>",
    "base_slug": base_slug,
    "number": generation_number,
    "created_at": now(),
}
```

Include it in orchestrator output. Add a helper that compares requested mode,
profile, modules, objective, success conditions, and proof types to the
persisted configuration.

- [ ] **Step 4: Resolve the workflow slug**

Keep the deterministic base slug for generation one. For fresh or changed
completed runs, create `<base-slug>-g<N>-<short-id>`. Apply requested mode via
`kernel.set_policy()` before orchestration whenever an existing workflow's mode
differs.

- [ ] **Step 5: Validate and run regression**

```powershell
python -m pytest tests/test_orchestrator.py tests/test_workflow_mcp.py -q
```

- [ ] **Step 6: Commit**

```powershell
git add core/workflow/kernel.py mcp_server.py tests/test_orchestrator.py tests/test_workflow_mcp.py
git commit -m "fix: version repeated pentest workflows"
```

### Task 6: OpenTgtyLab Workflow Durability

**Files:**
- Create: `D:\Open-tgtylab-repo\scripts\misc\workflow_lock.py`
- Modify: `D:\Open-tgtylab-repo\scripts\misc\workflow_state.py`
- Modify: `D:\Open-tgtylab-repo\tests\test_workflow_state.py`

- [ ] **Step 1: Write concurrent and stale-cache tests**

Create tests equivalent to Hunter's concurrent-writer test. Add a stale cache
test that appends a valid event without updating `workflow.json`, then asserts
`load()` returns state reconstructed from events and repairs the cache.

- [ ] **Step 2: Verify RED**

```powershell
python -m pytest tests/test_workflow_state.py -q
```

Expected: concurrent test fails with revision/state temp conflicts; stale-cache
test returns old state.

- [ ] **Step 3: Implement the shared lock convention**

Implement `WorkflowFileLock` with the same `.workflow.lock` filename, byte-zero
locking, timeout behavior, and reentrancy contract as Hunter.

- [ ] **Step 4: Materialize from validated events**

Add:

```python
def validate_events(events_path: Path) -> list[dict[str, Any]]: ...
def materialize_events(events: list[dict[str, Any]]) -> dict[str, Any]: ...
```

Handle all current Hunter event types, including orchestrator events, approval
consumption, evidence, findings, policies, checkpoints, and phase transitions.
Treat unknown additive event types as history-only rather than corrupting
state. Write the derived state cache atomically under the workflow lock.

- [ ] **Step 5: Verify**

```powershell
python -m pytest tests/test_workflow_state.py -q
```

- [ ] **Step 6: Commit**

```powershell
git add scripts/misc/workflow_lock.py scripts/misc/workflow_state.py tests/test_workflow_state.py
git commit -m "fix: make workflow storage event authoritative"
```

### Task 7: Full Hunter Integration Verification

**Files:**
- Modify: `D:\Open-tgtylab-repo\scripts\misc\verify_hunter_tools_integration.py`
- Modify: `D:\Open-tgtylab-repo\scripts\misc\hunter_tools_manager.py`
- Modify: `D:\Open-tgtylab-repo\tests\test_hunter_tools_manager.py`
- Create: `D:\Open-tgtylab-repo\tests\test_hunter_tools_integration_verify.py`
- Modify: `D:\Open-tgtylab-repo\.github\workflows\hunter-tools-integration.yml`

- [ ] **Step 1: Write verifier and exit-code tests**

Test:

- Missing required contract tool fails verification.
- FastMCP registry missing a required tool fails verification.
- Configured entrypoint mismatch fails.
- Configured workspace mismatch fails.
- `doctor` and `install/update` return nonzero when nested verification fails.
- CI workflow contains a full verifier invocation without `--config-only`.

- [ ] **Step 2: Verify RED**

```powershell
python -m pytest tests/test_hunter_tools_manager.py tests/test_hunter_tools_integration_verify.py -q
```

- [ ] **Step 3: Validate exact configuration**

Parse both project configs, expand `${HOME}` and `${workspaceFolder}`, and
compare their resolved Hunter entrypoint and `OPEN_TGTYLAB_ROOT` against the
entrypoint/root being verified. Replace `setdefault` with an explicit
verification environment.

- [ ] **Step 4: Validate contract and FastMCP registry**

Read `integration-contract.json`; require the server name, minimum count, all
required tools, and version fields. Inspect the FastMCP registry used by
`mcp_server.py`, not only module callables. Include actual workspace and tool
count in verifier output.

- [ ] **Step 5: Propagate nested failures**

Add:

```python
def result_failed(result: Mapping[str, Any]) -> bool:
    return (
        result.get("status") == "error"
        or result.get("verify", {}).get("status") == "error"
        or result.get("status", {}).get("entrypoint_exists") is False
    )
```

Return exit code 1 whenever install/update/doctor verification fails.

- [ ] **Step 6: Update CI and verify**

Run full verification after unit tests:

```yaml
- name: Full Hunter integration verification
  run: python scripts/misc/verify_hunter_tools_integration.py
```

Then run:

```powershell
python -m pytest tests/test_hunter_tools_manager.py tests/test_hunter_tools_integration_verify.py -q
python scripts/misc/verify_hunter_tools_integration.py
python scripts/misc/hunter_tools_manager.py doctor
```

- [ ] **Step 7: Commit**

```powershell
git add scripts/misc/verify_hunter_tools_integration.py scripts/misc/hunter_tools_manager.py tests/test_hunter_tools_manager.py tests/test_hunter_tools_integration_verify.py .github/workflows/hunter-tools-integration.yml
git commit -m "fix: verify the complete hunter integration"
```

### Task 8: Configuration and Repository Hygiene

**Files:**
- Modify: `C:\Users\Administrator\.codex\config.toml`
- Restore: `C:\Users\Administrator\.agents\skills\hunter\payloads\file-upload\file-upload-bypass.md`
- Modify: `C:\Users\Administrator\.agents\skills\hunter\.gitignore`
- Modify: `C:\Users\Administrator\.agents\skills\hunter\SKILL.md`
- Modify: `D:\Open-tgtylab-repo\.codex\config.toml`
- Modify: `D:\Open-tgtylab-repo\README.md`
- Modify: `D:\Open-tgtylab-repo\docs\hunter-tools-integration.md`

- [ ] **Step 1: Add configuration/documentation regression tests**

Extend tests to assert:

- Global and project configs have no `hunter` server.
- Both project clients resolve the same workspace.
- Current README says 111 tools.
- `SKILL.md` contains no `????` corruption markers.
- File-upload payload reference exists.
- No tracked `__pycache__` or `.pyc` paths remain.

- [ ] **Step 2: Verify RED**

Run the new tests and record the expected failures.

- [ ] **Step 3: Apply configuration cleanup**

Use the corrected manager to back up and rewrite the global Codex config,
leaving one `hunter_tools` block. Make the committed project Codex config use
the repository root consistently and document when the runtime workspace
`D:\Open-tgtylab` is intentionally selected.

- [ ] **Step 4: Restore and clean Hunter**

Restore the deleted payload file from `HEAD`. Remove all tracked bytecode paths
from the Git index while keeping `__pycache__/` and `*.pyc` ignored. Rewrite
`SKILL.md` as valid UTF-8 with the current 111-tool inventory and safety rules.

- [ ] **Step 5: Update current documentation**

Change only current capability statements to 111. Leave dated historical
counts unchanged when they describe a specific past commit.

- [ ] **Step 6: Verify**

```powershell
python -m pytest tests/test_hunter_tools_complete.py -q
python -m pytest tests/test_hunter_tools_manager.py tests/test_hunter_tools_integration_verify.py -q
git ls-files | rg "__pycache__|\.pyc$"
git diff --check
```

Expected: tests pass, tracked-bytecode search has no output, and diff check is
clean.

- [ ] **Step 7: Commit both repositories**

Create one focused Hunter hygiene/documentation commit and one focused
OpenTgtyLab configuration/documentation commit. Do not include unrelated
untracked design files.

### Task 9: Full Verification, Final Review, and Push

**Files:**
- Verify all files changed in Tasks 1-8.

- [ ] **Step 1: Run Hunter verification**

```powershell
python -m pytest -q
python -m compileall -q core mcp_server.py
python -c "import asyncio, mcp_server; print(asyncio.run(mcp_server.hunter_contract_check()))"
python -c "import asyncio, mcp_server; print(asyncio.run(mcp_server.hunter_doctor()))"
git diff --check
```

Required: zero test failures, 111 registered tools, no missing contract tools,
no legacy registration error.

- [ ] **Step 2: Run OpenTgtyLab verification**

```powershell
python -m pytest -q
python scripts/misc/verify_hunter_tools_integration.py
python scripts/misc/hunter_tools_manager.py doctor
git diff --check
```

Required: zero failures and zero exit-code/config/path errors.

- [ ] **Step 3: Review repository state**

Confirm only intended files are committed. Preserve the two pre-existing
untracked unified-orchestrator documents unless separately incorporated.

- [ ] **Step 4: Push and verify remote refs**

Push Hunter `main`, then OpenTgtyLab `main`. Fetch and compare:

```powershell
git rev-parse HEAD
git rev-parse origin/main
```

Required: local HEAD and `origin/main` match in both repositories.

- [ ] **Step 5: Update case state and publish evidence**

Update `D:\Open-tgtylab\cases\hunter-skill\state.json` with verified commits,
test counts, fixed findings, remaining external-tool gaps, and next steps.
Write a concise note under `D:\Open-tgtylab\exports\notes`.
