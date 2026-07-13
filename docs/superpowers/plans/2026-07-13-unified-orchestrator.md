# Unified Orchestrator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a resumable seven-stage orchestration pipeline while preserving the existing event-sourced workflow API.

**Architecture:** Extend `core/workflow/kernel.py` with injected stage adapters and event-backed stage state. Add one MCP wrapper that creates/opens a workflow, runs bounded stages, and returns findings, handoffs, checkpoints, and confirmation requirements.

**Tech Stack:** Python standard library, existing WorkflowKernel event log, existing Hunter memory/session/browser abstractions, pytest.

---

### Task 1: RED tests

**Files:**
- Create: `C:\Users\Administrator\.agents\skills\hunter\tests\test_orchestrator.py`

- [ ] Test seven-stage fake-adapter execution and output fields.
- [ ] Test stage progress/checkpoint events.
- [ ] Test interruption and resume from the first incomplete stage.
- [ ] Test memory context loading and learning updates.
- [ ] Test interactive high-impact confirmation blocking.
- [ ] Run the test file and confirm the missing orchestrator API failure.

### Task 2: Kernel orchestration

**Files:**
- Modify: `C:\Users\Administrator\.agents\skills\hunter\core\workflow\kernel.py`
- Modify: `C:\Users\Administrator\.agents\skills\hunter\core\workflow\__init__.py`

- [ ] Add bounded policy profiles and serializable stage metadata.
- [ ] Add adapter normalization and default passive/deferred adapters.
- [ ] Add stage event materialization and checkpoint-aware resume.
- [ ] Implement `UnifiedOrchestrator.orchestrate()` and preserve `run()`.

### Task 3: MCP integration

**Files:**
- Modify: `C:\Users\Administrator\.agents\skills\hunter\mcp_server.py`
- Modify: `C:\Users\Administrator\.agents\skills\hunter\integration-contract.json`
- Modify: `C:\Users\Administrator\.agents\skills\hunter\core\hunter_tools_facade.py`

- [ ] Add `hunter_auto_pentest(target_url, options)` with fast/standard/deep and modules validation.
- [ ] Make `hunter_workflow_run` expose orchestrator state when requested while preserving legacy behavior.
- [ ] Add tool metadata and contract entry.

### Task 4: Documentation and verification

**Files:**
- Modify: `C:\Users\Administrator\.agents\skills\hunter\README.md`
- Modify: `C:\Users\Administrator\.agents\skills\hunter\TOOLS.md`
- Modify: `C:\Users\Administrator\.agents\skills\hunter\SKILL.md`
- Modify: `D:\Open-tgtylab\cases\hunter-skill\state.json`
- Create: `D:\Open-tgtylab\exports\notes\hunter-unified-orchestrator-20260713.md`

- [ ] Document stage semantics and approval boundaries.
- [ ] Run focused tests, full Hunter tests, contract checks, compile and diff checks.
- [ ] Record evidence and residual risk.
