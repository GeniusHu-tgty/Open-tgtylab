import json
from pathlib import Path


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
