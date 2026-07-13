import json
import multiprocessing
import sys
import threading
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import pytest


def _append_hypothesis(case_dir, index):
    from scripts.misc.workflow_state import WorkflowStore

    return WorkflowStore(case_dir).append(
        "hypothesis.added",
        {"id": f"h-{index}", "claim": f"hypothesis-{index}"},
    )[0]["event_id"]


def _acquire_workflow_lock(lock_path):
    from scripts.misc.workflow_lock import WorkflowFileLock

    with WorkflowFileLock(lock_path,timeout=0.5):
        return True


def test_workflow_state_schema_accepts_full_case():
    root=Path(__file__).resolve().parents[1]
    schema=json.loads((root/'schemas'/'workflow-state-v2.schema.json').read_text(encoding='utf-8'))
    from scripts.misc.workflow_state import validate_document
    case={
      'schema_version':'2.0','workflow_id':'wf-demo','slug':'demo','case':{'slug':'demo'},
      'objective':{'text':'obtain proof','success_conditions':['proof confirmed'],'proof_types':['flag']},
      'scope':{'targets':['fixture'],'allowed_actions':[],'constraints':[]},
      'policy':{'mode':'autopilot','max_escalation':2},'phase':'triage','lane':'mixed',
      'lane_history':[],'assets':[],'artifacts':[],'signals':[],'hypotheses':[],
      'decisions':[],'tool_runs':[],'evidence':[],'findings':[],'dead_ends':[],
      'blockers':[],'budgets':{},'checkpoints':[],'metrics':{},'next_steps':[]
    }
    assert validate_document(case,schema)==[]


def test_event_store_materializes_and_rejects_bad_transition(tmp_path):
    from scripts.misc.workflow_state import WorkflowStore
    store=WorkflowStore(tmp_path/'case')
    state=store.create('demo','obtain flag',['sample.exe'],lane='pe')
    assert state['phase']=='intake'
    state=store.transition('triage',actor='test')
    assert state['phase']=='triage'
    assert (tmp_path/'case'/'workflow.events.jsonl').read_text(encoding='utf-8').count('\n')>=2
    try:
        store.transition('report')
    except ValueError as exc:
        assert 'transition' in str(exc).lower()
    else:
        raise AssertionError('invalid transition accepted')


def test_v1_migration_preserves_findings_and_next_steps(tmp_path):
    from scripts.misc.workflow_state import migrate_v1_state
    old={'slug':'legacy','target':'https://fixture','status':'active','findings':[{'type':'lead','evidence':'x'}], 'next_steps':['verify']}
    new=migrate_v1_state(old)
    assert new['schema_version']=='2.0'
    assert new['case']['slug']=='legacy'
    assert new['findings'][0]['status']=='lead'
    assert new['next_steps']==['verify']


def test_workflow_store_is_compatible_with_hunter_event_shape(tmp_path):
    from scripts.misc.workflow_state import WorkflowStore
    store=WorkflowStore(tmp_path/"case")
    state=store.create("demo","proof",["a.exe"],lane="pe")
    event=json.loads((tmp_path/"case"/"workflow.events.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert event["schema_version"]=="1.0"
    assert event["workflow_id"]==state["workflow_id"]
    assert event["payload"]["state"]["slug"]=="demo"
    assert state["slug"]=="demo"


def test_event_payloads_match_hunter_materializer_contract(tmp_path):
    from scripts.misc.workflow_state import WorkflowStore
    store=WorkflowStore(tmp_path/"case"); store.create("demo","proof",["a.exe"],lane="pe")
    store.transition("triage",deliverables={"objective":True,"artifact_inventory":True})
    store.append("hypothesis.added",{"id":"h1","claim":"x"})
    events=[json.loads(x) for x in store.events_path.read_text().splitlines()]
    assert events[1]["payload"]["phase"]=="triage"
    assert events[1]["payload"]["to"]=="triage"
    assert events[2]["payload"]["hypothesis"]["id"]=="h1"


def test_minimum_validator_rejects_nested_type_mismatch():
    from scripts.misc.workflow_state import validate_document
    schema={"type":"object","properties":{"objective":{"type":"object","properties":{"text":{"type":"string"},"items":{"type":"array"}}}}}
    errors=validate_document({"objective":{"text":123,"items":"bad"}},schema)
    assert "objective.text must be string" in errors
    assert "objective.items must be array" in errors


def test_events_have_revision_and_hash_chain(tmp_path):
    from scripts.misc.workflow_state import WorkflowStore
    store=WorkflowStore(tmp_path/"case"); store.create("demo","proof",[])
    store.append("hypothesis.added",{"id":"h1"})
    events=[json.loads(x) for x in store.events_path.read_text().splitlines()]
    assert [e["revision"] for e in events]==[1,2]
    assert events[1]["previous_event_hash"]==events[0]["event_hash"]


def test_store_load_rejects_tampered_event_chain(tmp_path):
    from scripts.misc.workflow_state import WorkflowStore
    store=WorkflowStore(tmp_path/"case"); store.create("demo","proof",[])
    event=json.loads(store.events_path.read_text().splitlines()[0]); event["payload"]["state"]["phase"]="final"
    store.events_path.write_text(json.dumps(event)+"\n")
    try: store.load()
    except ValueError as exc: assert "event hash" in str(exc)
    else: raise AssertionError("tampered event accepted")


def test_append_rejects_stale_expected_revision(tmp_path):
    from scripts.misc.workflow_state import WorkflowStore
    store=WorkflowStore(tmp_path/"case"); store.create("demo","proof",[])
    try: store.append("hypothesis.added",{"id":"h"},expected_revision=0)
    except ValueError as exc: assert "revision conflict" in str(exc)
    else: raise AssertionError("stale write accepted")


def test_concurrent_workflow_store_writers_preserve_event_chain(tmp_path):
    from scripts.misc.workflow_state import WorkflowStore

    case_dir=tmp_path/"case"
    WorkflowStore(case_dir).create("demo","proof",[])
    with ProcessPoolExecutor(
        max_workers=8,
        mp_context=multiprocessing.get_context("spawn"),
    ) as pool:
        futures=[
            pool.submit(_append_hypothesis,str(case_dir),index)
            for index in range(16)
        ]
        assert [future.result() for future in futures]

    store=WorkflowStore(case_dir)
    events=[
        json.loads(line)
        for line in store.events_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert [event["revision"] for event in events]==list(range(1,18))
    for previous,current in zip(events,events[1:]):
        assert current["previous_event_hash"]==previous["event_hash"]
    assert len(store.load()["hypotheses"])==16


def test_load_rebuilds_and_repairs_stale_workflow_cache(tmp_path):
    from scripts.misc.workflow_state import WorkflowStore

    store=WorkflowStore(tmp_path/"case")
    state=store.create("demo","proof",[])
    hypothesis={"id":"h-stale","claim":"event log is authoritative"}
    store._event(
        state,
        "hypothesis.added",
        {"hypothesis":hypothesis},
        actor="test",
    )

    loaded=store.load()
    cached=json.loads(store.state_path.read_text(encoding="utf-8"))
    assert loaded["hypotheses"]==[hypothesis]
    assert cached["hypotheses"]==[hypothesis]


def test_materializer_handles_current_hunter_event_types(tmp_path):
    from scripts.misc.workflow_state import (
        WorkflowStore,
        materialize_events,
        validate_events,
    )

    store=WorkflowStore(tmp_path/"case")
    state=store.create("demo","proof",[])
    events=[
        ("phase.transitioned",{"phase":"triage","gate":{"satisfied":True}}),
        ("policy.changed",{"policy":{"mode":"autopilot","stop_on_proof":True}}),
        ("decision.recorded",{"decision":{"id":"d-local","summary":"continue"}}),
        ("evidence.registered",{"evidence":{"id":"ev-1","summary":"proof"}}),
        (
            "finding.promoted",
            {"finding":{"id":"f-1","status":"confirmed","satisfies":[]}},
        ),
        (
            "checkpoint.created",
            {"checkpoint":{"checkpoint_id":"cp-1","path":"checkpoint.json"}},
        ),
        (
            "orchestrator.initialized",
            {"orchestrator":{"profile":"deep","modules":["api"]}},
        ),
        (
            "orchestrator.approval.recorded",
            {
                "approval":{
                    "approved":True,
                    "decision_id":"decision-1",
                    "confirmation_id":"confirmation-1",
                }
            },
        ),
        (
            "orchestrator.approval.consumed",
            {
                "decision_id":"decision-1",
                "confirmation_id":"confirmation-1",
                "consumed_at":"2026-07-13T00:00:00+00:00",
            },
        ),
        (
            "orchestrator.stage.completed",
            {"stage":"report","result":{"report_path":"reports/demo.md"}},
        ),
    ]
    for event_type,payload in events:
        store._event(state,event_type,payload,actor="hunter_tools")

    materialized=materialize_events(validate_events(store.events_path))
    assert materialized["phase"]=="triage"
    assert materialized["policy"]["mode"]=="autopilot"
    assert materialized["decisions"][0]["id"]=="d-local"
    assert materialized["evidence"][0]["id"]=="ev-1"
    assert materialized["findings"][0]["id"]=="f-1"
    assert materialized["checkpoints"][0]["checkpoint_id"]=="cp-1"
    assert materialized["metrics"]["checkpoints"]==1
    assert materialized["orchestrator"]["profile"]=="deep"
    assert materialized["orchestrator"]["modules"]==["api"]
    assert materialized["orchestrator"]["approvals"][0]["consumed"] is True
    assert materialized["report_path"]=="reports/demo.md"


def test_unknown_event_types_are_history_only(tmp_path):
    from scripts.misc.workflow_state import WorkflowStore

    store=WorkflowStore(tmp_path/"case")
    state=store.create("demo","proof",[])
    updated_at=state["updated_at"]
    store._event(
        state,
        "future.capability.observed",
        {"unexpected":{"nested":True}},
        actor="future-hunter",
    )

    loaded=store.load()
    assert loaded["phase"]=="intake"
    assert loaded["updated_at"]==updated_at
    assert loaded["history"][-1]["type"]=="future.capability.observed"


def test_workflow_file_lock_is_reentrant_for_same_instance(tmp_path):
    from scripts.misc.workflow_lock import WorkflowFileLock

    lock_path=tmp_path/"case"/".workflow.lock"
    lock=WorkflowFileLock(lock_path,timeout=0.5)
    with lock:
        with lock:
            pass

    with ProcessPoolExecutor(
        max_workers=1,
        mp_context=multiprocessing.get_context("spawn"),
    ) as pool:
        assert pool.submit(
            _acquire_workflow_lock,
            str(lock_path),
        ).result() is True


def test_workflow_file_lock_uses_one_total_timeout(tmp_path, monkeypatch):
    import scripts.misc.workflow_lock as locking

    path=tmp_path/".workflow.lock"
    clock=[0.0]

    class DelayedProcessLock:
        def acquire(self,timeout):
            clock[0]+=0.06
            return True

        def release(self):
            return None

    monkeypatch.setattr(
        locking,
        "_lock_handle",
        lambda handle: (_ for _ in ()).throw(PermissionError("busy")),
    )
    monkeypatch.setattr(locking.time,"monotonic",lambda:clock[0])
    monkeypatch.setattr(
        locking.time,
        "sleep",
        lambda duration:clock.__setitem__(0,clock[0]+duration),
    )
    lock=locking.WorkflowFileLock(path,timeout=0.1)
    lock._process_lock=DelayedProcessLock()
    with pytest.raises(TimeoutError):
        with lock:
            pass
    assert clock[0]==pytest.approx(0.1)


def test_workflow_file_lock_releases_after_open_failure(tmp_path,monkeypatch):
    import scripts.misc.workflow_lock as locking

    path=tmp_path/".workflow.lock"
    original_open=locking.Path.open

    def fail_open(self,*args,**kwargs):
        if self.resolve()==path.resolve():
            raise OSError("cannot open lock")
        return original_open(self,*args,**kwargs)

    monkeypatch.setattr(locking.Path,"open",fail_open)
    with pytest.raises(OSError,match="cannot open lock"):
        with locking.WorkflowFileLock(path,timeout=0.1):
            pass
    monkeypatch.setattr(locking.Path,"open",original_open)
    acquired=threading.Event()

    def acquire_after_failure():
        with locking.WorkflowFileLock(path,timeout=0.1):
            acquired.set()

    thread=threading.Thread(target=acquire_after_failure)
    thread.start()
    thread.join(1)
    assert acquired.is_set()


def test_workflow_file_lock_unix_branch_uses_flock(monkeypatch,tmp_path):
    import scripts.misc.workflow_lock as locking

    calls=[]
    fake_fcntl=SimpleNamespace(
        LOCK_EX=1,
        LOCK_NB=2,
        LOCK_UN=4,
        flock=lambda fileno,operation:calls.append((fileno,operation)),
    )
    monkeypatch.setitem(sys.modules,"fcntl",fake_fcntl)
    monkeypatch.setattr(locking,"_platform_name",lambda:"posix")
    with (tmp_path/"unix.lock").open("w+b") as handle:
        handle.write(b"\0")
        handle.flush()
        locking._lock_handle(handle)
        locking._unlock_handle(handle)
    assert calls[0][1]==fake_fcntl.LOCK_EX|fake_fcntl.LOCK_NB
    assert calls[1][1]==fake_fcntl.LOCK_UN
