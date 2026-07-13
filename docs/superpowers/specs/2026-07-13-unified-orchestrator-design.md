# Unified Orchestrator Design

**Goal:** Integrate Hunter memory, passive reconnaissance, attack-surface
analysis, deferred attack-chain planning, pattern confirmation, evidence,
learning, and report handoff into a resumable workflow kernel.

## Architecture

`WorkflowKernel` remains the event-sourced persistence boundary. A new
`UnifiedOrchestrator` coordinates seven bounded stages:

1. `memory`
2. `recon`
3. `attack_surface`
4. `attack_execution`
5. `vulnerability_confirmation`
6. `evidence_learning`
7. `report`

Each stage is implemented through an injected adapter map. The default adapters
produce local results and deferred Hunter/browser/stealth handoffs; tests inject
fake adapters. This keeps orchestration deterministic and prevents kernel code
from directly issuing target requests or executing payloads.

## State and Recovery

The workflow state gains `orchestrator` metadata, `memo`, `target_profile`,
`attack_surface`, `attack_queue`, `stage_results`, `confirmation_required`,
`learning_updates`, and `report_path`. Every stage emits start/completion/block
events and creates a checkpoint after completion. Resume reads the last stage
result and continues from the first incomplete stage.

## Policies

`fast`, `standard`, and `deep` select bounded queue/depth limits. The workflow
policy remains authoritative: interactive mode pauses before high-impact
execution or post-exploitation; guided mode returns confirmation actions;
autopilot still emits external handoffs and never bypasses explicit approval.

## Compatibility

Existing `WorkflowKernel.run()` and workflow MCP tools remain compatible. A new
`UnifiedOrchestrator.orchestrate()` method and `hunter_auto_pentest` MCP wrapper
expose the full pipeline. Existing event hashes, phase transitions, evidence
registration, and finding promotion semantics are preserved.

## Verification

`tests/test_orchestrator.py` covers full fake-adapter execution, stage
progress, checkpoint creation, interruption and resume, memory query/update,
interactive confirmation blocking, and MCP smoke output. Full Hunter regression
tests must remain green.
