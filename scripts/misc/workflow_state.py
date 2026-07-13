#!/usr/bin/env python3
"""Schema-validated event-sourced workflow state for OpenTgtyLab cases."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from threading import get_ident
from typing import Any

try:
    from .workflow_lock import WorkflowFileLock
except ImportError:
    from workflow_lock import WorkflowFileLock


PHASES = (
    "intake",
    "triage",
    "map",
    "hypothesis",
    "deep-analysis",
    "validation",
    "evidence",
    "report",
    "final",
)
TRANSITIONS = {
    phase: {PHASES[index + 1]}
    for index, phase in enumerate(PHASES[:-1])
}
TRANSITIONS["validation"].add("hypothesis")
TRANSITIONS["final"] = set()
LANES = {
    "web",
    "api",
    "source",
    "javascript",
    "pe",
    "apk",
    "firmware",
    "script",
    "document",
    "protocol",
    "capture",
    "pwn",
    "crypto",
    "mixed",
}
ORCHESTRATOR_STAGES = (
    "memory",
    "recon",
    "attack_surface",
    "attack_execution",
    "vulnerability_confirmation",
    "evidence_learning",
    "report",
)


def now():
    return datetime.now(timezone.utc).isoformat()


def validate_document(
    doc: dict[str, Any],
    schema: dict[str, Any],
) -> list[str]:
    errors = []

    def walk(value, spec, path):
        typ = spec.get("type")
        checks = {
            "object": dict,
            "array": list,
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
        }
        if typ in checks and not isinstance(value, checks[typ]):
            errors.append(f'{path or "document"} must be {typ}')
            return
        if "const" in spec and value != spec["const"]:
            errors.append(
                f'{path or "document"} must equal {spec["const"]}'
            )
        if "enum" in spec and value not in spec["enum"]:
            errors.append(f'{path or "document"} invalid value')
        if isinstance(value, dict):
            for required in spec.get("required", []):
                if required not in value:
                    prefix = f"{path}." if path else ""
                    errors.append(f"{prefix}{required} is required")
            for key, child in spec.get("properties", {}).items():
                if key in value:
                    prefix = f"{path}." if path else ""
                    walk(value[key], child, f"{prefix}{key}")
        if isinstance(value, list) and spec.get("items"):
            for index, item in enumerate(value):
                walk(item, spec["items"], f"{path}[{index}]")

    walk(doc, schema, "")
    return errors


def migrate_v1_state(old):
    slug = old.get("slug") or old.get("case", {}).get("slug") or "case"
    findings = []
    for index, item in enumerate(old.get("findings", []), 1):
        finding = (
            dict(item)
            if isinstance(item, dict)
            else {"title": str(item)}
        )
        finding.setdefault("id", f"finding-{index:04d}")
        finding.setdefault("status", "lead")
        findings.append(finding)
    return {
        "schema_version": "2.0",
        "workflow_id": old.get("workflow_id") or f"wf-{slug}",
        "slug": slug,
        "case": {"slug": slug},
        "objective": {
            "text": old.get("objective", ""),
            "success_conditions": [],
            "proof_types": [],
        },
        "scope": {
            "targets": [old["target"]] if old.get("target") else [],
            "allowed_actions": [],
            "constraints": [],
        },
        "policy": {"mode": "guided", "max_escalation": 2},
        "phase": (
            old.get("phase", "intake")
            if old.get("phase") in PHASES
            else "intake"
        ),
        "lane": (
            old.get("lane", "mixed")
            if old.get("lane") in LANES
            else "mixed"
        ),
        "lane_history": [],
        "assets": [],
        "artifacts": [],
        "signals": [],
        "hypotheses": [],
        "decisions": [],
        "tool_runs": [],
        "evidence": [],
        "findings": findings,
        "dead_ends": [],
        "blockers": old.get("blockers", []),
        "budgets": {},
        "checkpoints": [],
        "metrics": {},
        "next_steps": old.get("next_steps", []),
    }


def validate_events(events_path: Path) -> list[dict[str, Any]]:
    path = Path(events_path)
    if not path.exists():
        raise FileNotFoundError(f"workflow events not found: {path}")

    events = []
    previous_hash = ""
    expected_revision = 1
    workflow_id = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        supplied_hash = event.get("event_hash", "")
        unsigned = {
            key: value
            for key, value in event.items()
            if key != "event_hash"
        }
        canonical = json.dumps(
            unsigned,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        calculated_hash = hashlib.sha256(canonical.encode()).hexdigest()
        if supplied_hash != calculated_hash:
            raise ValueError("event hash mismatch")
        if (
            event.get("revision") != expected_revision
            or event.get("previous_event_hash", "") != previous_hash
        ):
            raise ValueError("event chain mismatch")
        if workflow_id is None:
            workflow_id = event.get("workflow_id")
        elif event.get("workflow_id") != workflow_id:
            raise ValueError("event workflow mismatch")
        previous_hash = supplied_hash
        expected_revision += 1
        events.append(event)
    return events


def _ensure_orchestrator_defaults(state):
    state.setdefault("orchestrator", {})
    orchestrator = state["orchestrator"]
    orchestrator.setdefault("version", "1.0")
    orchestrator.setdefault("status", "idle")
    orchestrator.setdefault("current_stage", "memory")
    orchestrator.setdefault("profile", "standard")
    orchestrator.setdefault("modules", ["all"])
    orchestrator.setdefault("stage_status", {})
    for stage in ORCHESTRATOR_STAGES:
        orchestrator["stage_status"].setdefault(stage, "pending")
    orchestrator.setdefault("stage_results", {})
    orchestrator.setdefault("confirmation_required", [])
    orchestrator.setdefault("approvals", [])
    orchestrator.setdefault("approval_consumptions", [])
    orchestrator.setdefault("observations", {})
    orchestrator.setdefault("resumed_from", "")
    state.setdefault("memo", {})
    state.setdefault("target_profile", {})
    state.setdefault("attack_surface", {})
    state.setdefault("attack_queue", [])
    state.setdefault("learning_updates", [])
    state.setdefault("report_path", "")
    return state


def _ensure_state_defaults(state):
    for key in (
        "lane_history",
        "assets",
        "artifacts",
        "signals",
        "hypotheses",
        "decisions",
        "tool_runs",
        "evidence",
        "findings",
        "dead_ends",
        "blockers",
        "checkpoints",
        "next_steps",
    ):
        state.setdefault(key, [])
    state.setdefault("metrics", {})
    state["metrics"].setdefault("tool_calls", 0)
    state["metrics"].setdefault("checkpoints", 0)
    state.setdefault("status", "active")
    state.setdefault("case", {"slug": state.get("slug", "case")})
    _ensure_orchestrator_defaults(state)
    return state


def _apply_orchestrator_result(state, stage, result):
    if stage == "memory":
        state["memo"] = deepcopy(result.get("memo", result))
    elif stage == "recon":
        state["target_profile"] = deepcopy(
            result.get("target_profile", result)
        )
    elif stage == "attack_surface":
        state["attack_surface"] = deepcopy(
            result.get("attack_surface", result)
        )
        state["attack_queue"] = deepcopy(result.get("attack_queue", []))
    elif stage == "evidence_learning":
        state["learning_updates"] = deepcopy(
            result.get("learning_updates", [])
        )
    elif stage == "report":
        state["report_path"] = str(result.get("report_path", ""))


def _consume_approval(state, payload):
    _ensure_orchestrator_defaults(state)
    source = (
        payload.get("consumption")
        or payload.get("approval")
        or payload
    )
    consumption = deepcopy(source)
    state["orchestrator"]["approval_consumptions"].append(consumption)
    confirmation_id = source.get("confirmation_id")
    decision_id = source.get("decision_id")
    for approval in reversed(state["orchestrator"]["approvals"]):
        if confirmation_id and approval.get("confirmation_id") != confirmation_id:
            continue
        if decision_id and approval.get("decision_id") != decision_id:
            continue
        approval["consumed"] = True
        approval["consumed_at"] = (
            source.get("consumed_at")
            or payload.get("consumed_at")
        )
        break
    if confirmation_id:
        state["orchestrator"]["confirmation_required"] = [
            item
            for item in state["orchestrator"]["confirmation_required"]
            if item.get("confirmation_id") != confirmation_id
        ]


def materialize_events(events: list[dict[str, Any]]) -> dict[str, Any]:
    state = None
    history = []
    for event in events:
        event_type = event["type"]
        payload = event["payload"]
        handled = True
        if event_type == "workflow.created":
            state = _ensure_state_defaults(deepcopy(payload["state"]))
        elif state is None:
            raise ValueError("workflow.created must be the first event")
        elif event_type == "phase.transitioned":
            state["phase"] = payload.get("phase", payload.get("to"))
            if "gate" in payload:
                state["last_gate"] = deepcopy(payload["gate"])
        elif event_type == "hypothesis.added":
            state["hypotheses"].append(deepcopy(payload["hypothesis"]))
        elif event_type == "policy.changed":
            state["policy"] = deepcopy(payload["policy"])
        elif event_type == "decision.recorded":
            state["decisions"].append(deepcopy(payload["decision"]))
        elif event_type == "tool_run.recorded":
            state["tool_runs"].append(deepcopy(payload["tool_run"]))
            state["metrics"]["tool_calls"] += 1
        elif event_type == "dead_end.recorded":
            state["dead_ends"].append(deepcopy(payload["dead_end"]))
        elif event_type == "evidence.registered":
            state["evidence"].append(deepcopy(payload["evidence"]))
        elif event_type == "finding.promoted":
            finding = deepcopy(payload["finding"])
            state["findings"].append(finding)
            objective = state.get("objective", {})
            conditions = (
                set(objective.get("success_conditions", []))
                if isinstance(objective, dict)
                else set()
            )
            satisfies = set(finding.get("satisfies", []))
            if (
                finding.get("status") == "confirmed"
                and conditions
                and conditions <= satisfies
                and state["policy"].get("stop_on_proof", True)
            ):
                state["status"] = "complete"
        elif event_type == "checkpoint.created":
            state["checkpoints"].append(deepcopy(payload["checkpoint"]))
            state["metrics"]["checkpoints"] += 1
        elif event_type == "orchestrator.initialized":
            _ensure_orchestrator_defaults(state)
            state["orchestrator"].update(
                deepcopy(payload.get("orchestrator", {}))
            )
            _ensure_orchestrator_defaults(state)
        elif event_type == "orchestrator.observations.updated":
            _ensure_orchestrator_defaults(state)
            state["orchestrator"]["observations"].update(
                deepcopy(payload.get("observations", {}))
            )
        elif event_type == "orchestrator.approval.recorded":
            _ensure_orchestrator_defaults(state)
            approval = deepcopy(payload["approval"])
            approval.setdefault("consumed", False)
            state["orchestrator"]["approvals"].append(approval)
            if (
                approval.get("approved")
                and not approval.get("confirmation_id")
                and approval.get("stage")
                == state["orchestrator"].get("current_stage")
            ):
                state["orchestrator"]["confirmation_required"] = []
        elif event_type == "orchestrator.approval.consumed":
            _consume_approval(state, payload)
        elif event_type == "orchestrator.stage.started":
            _ensure_orchestrator_defaults(state)
            stage = payload["stage"]
            state["orchestrator"]["current_stage"] = stage
            state["orchestrator"]["status"] = "running"
            state["orchestrator"]["stage_status"][stage] = "running"
        elif event_type == "orchestrator.stage.completed":
            _ensure_orchestrator_defaults(state)
            stage = payload["stage"]
            result = deepcopy(payload.get("result", {}))
            state["orchestrator"]["current_stage"] = stage
            state["orchestrator"]["stage_status"][stage] = "completed"
            state["orchestrator"]["stage_results"][stage] = result
            _apply_orchestrator_result(state, stage, result)
        elif event_type == "orchestrator.stage.blocked":
            _ensure_orchestrator_defaults(state)
            stage = payload["stage"]
            status = payload.get("status", "blocked")
            state["orchestrator"]["current_stage"] = stage
            state["orchestrator"]["status"] = status
            state["orchestrator"]["stage_status"][stage] = status
            if "result" in payload:
                state["orchestrator"]["stage_results"][stage] = deepcopy(
                    payload["result"]
                )
            state["orchestrator"]["confirmation_required"] = deepcopy(
                payload.get("confirmation_required", [])
            )
        elif event_type == "orchestrator.interrupted":
            _ensure_orchestrator_defaults(state)
            stage = payload["stage"]
            state["orchestrator"]["status"] = "interrupted"
            state["orchestrator"]["current_stage"] = stage
            state["orchestrator"]["stage_status"][stage] = "interrupted"
        elif event_type == "orchestrator.completed":
            _ensure_orchestrator_defaults(state)
            state["orchestrator"]["status"] = "completed"
            state["orchestrator"]["current_stage"] = "complete"
            if payload.get("complete"):
                state["status"] = "complete"
        else:
            handled = False

        if state is not None and handled:
            state["updated_at"] = event["timestamp"]
            state["case"]["updated_at"] = event["timestamp"]
        history.append(
            {
                "event_id": event["event_id"],
                "type": event_type,
                "timestamp": event["timestamp"],
            }
        )

    if state is None:
        raise ValueError("workflow event stream is empty")
    _ensure_state_defaults(state)
    state["history"] = history
    return state


class WorkflowStore:
    def __init__(self, case_dir):
        self.case_dir = Path(case_dir).resolve()
        self.state_path = self.case_dir / "workflow.json"
        self.events_path = self.case_dir / "workflow.events.jsonl"
        self.lock_path = self.case_dir / ".workflow.lock"

    def _lock(self):
        return WorkflowFileLock(self.lock_path)

    def _state_tmp(self):
        return self.state_path.with_name(
            f".{self.state_path.name}.{os.getpid()}.{get_ident()}.tmp"
        )

    def _write_locked(self, state):
        self.case_dir.mkdir(parents=True, exist_ok=True)
        temporary = self._state_tmp()
        try:
            with temporary.open("w", encoding="utf-8", newline="\n") as handle:
                handle.write(
                    json.dumps(state, ensure_ascii=False, indent=2) + "\n"
                )
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.state_path)
        finally:
            if temporary.exists():
                temporary.unlink()

    def _write(self, state):
        with self._lock():
            self._write_locked(state)

    def _event_locked(
        self,
        state,
        event_type,
        payload,
        actor="system",
        expected_revision=None,
    ):
        existing = (
            validate_events(self.events_path)
            if self.events_path.exists()
            else []
        )
        if (
            expected_revision is not None
            and expected_revision != len(existing)
        ):
            raise ValueError(
                "revision conflict: "
                f"expected {expected_revision}, current {len(existing)}"
            )
        revision = len(existing) + 1
        previous_hash = (
            existing[-1].get("event_hash", "")
            if existing
            else ""
        )
        event = {
            "event_id": f"evt-{uuid.uuid4().hex}",
            "schema_version": "1.0",
            "workflow_id": state["workflow_id"],
            "type": event_type,
            "timestamp": now(),
            "actor": actor,
            "revision": revision,
            "previous_event_hash": previous_hash,
            "payload": payload,
        }
        canonical = json.dumps(
            event,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        event["event_hash"] = hashlib.sha256(canonical.encode()).hexdigest()
        self.case_dir.mkdir(parents=True, exist_ok=True)
        with self.events_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        return event

    def _event(
        self,
        state,
        event_type,
        payload,
        actor="system",
        expected_revision=None,
    ):
        with self._lock():
            return self._event_locked(
                state,
                event_type,
                payload,
                actor,
                expected_revision,
            )

    def _materialize_locked(self):
        state = materialize_events(validate_events(self.events_path))
        self._write_locked(state)
        return state

    def _load_locked(self):
        state = materialize_events(validate_events(self.events_path))
        cached = None
        if self.state_path.exists():
            try:
                cached = json.loads(
                    self.state_path.read_text(encoding="utf-8-sig")
                )
            except (OSError, UnicodeError, json.JSONDecodeError):
                cached = None
        if cached != state:
            self._write_locked(state)
        return state

    def create(
        self,
        slug,
        objective,
        targets,
        lane="mixed",
        mode="guided",
    ):
        with self._lock():
            if self.events_path.exists():
                raise ValueError("workflow already exists")
            state = migrate_v1_state(
                {
                    "slug": slug,
                    "objective": objective,
                    "target": targets[0] if targets else None,
                    "lane": lane,
                }
            )
            state["scope"]["targets"] = list(targets)
            state["policy"]["mode"] = mode
            self._event_locked(
                state,
                "workflow.created",
                {"state": deepcopy(state)},
            )
            return self._materialize_locked()

    def load(self):
        with self._lock():
            return self._load_locked()

    def transition(self, to_phase, actor="system", deliverables=None):
        with self._lock():
            state = self._load_locked()
            current = state["phase"]
            if to_phase not in TRANSITIONS.get(current, set()):
                raise ValueError(
                    f"invalid transition: {current} -> {to_phase}"
                )
            self._event_locked(
                state,
                "phase.transitioned",
                {
                    "from": current,
                    "to": to_phase,
                    "phase": to_phase,
                    "gate": {"satisfied": True},
                    "deliverables": deliverables or {},
                },
                actor,
            )
            return self._materialize_locked()

    def append(
        self,
        event_type,
        payload,
        actor="system",
        expected_revision=None,
    ):
        with self._lock():
            state = self._load_locked()
            wrappers = {
                "hypothesis.added": "hypothesis",
                "evidence.registered": "evidence",
                "finding.promoted": "finding",
                "decision.recorded": "decision",
                "dead_end.recorded": "dead_end",
            }
            event_payload = (
                {wrappers[event_type]: payload}
                if event_type in wrappers
                else payload
            )
            event = self._event_locked(
                state,
                event_type,
                event_payload,
                actor,
                expected_revision,
            )
            return event, self._materialize_locked()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["migrate", "validate"])
    parser.add_argument("input")
    parser.add_argument("--output")
    args = parser.parse_args()
    source = Path(args.input)
    data = json.loads(source.read_text(encoding="utf-8-sig"))
    if args.action == "migrate":
        output = migrate_v1_state(data)
        target = (
            Path(args.output)
            if args.output
            else source.with_name("workflow.json")
        )
        target.write_text(
            json.dumps(output, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(target)
        return

    schema = json.loads(
        (
            Path(__file__).resolve().parents[2]
            / "schemas"
            / "workflow-state-v2.schema.json"
        ).read_text(encoding="utf-8-sig")
    )
    errors = validate_document(data, schema)
    print(
        json.dumps(
            {"status": "ok" if not errors else "error", "errors": errors},
            ensure_ascii=False,
        )
    )
    raise SystemExit(bool(errors))


if __name__ == "__main__":
    main()
