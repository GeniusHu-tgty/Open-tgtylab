#!/usr/bin/env python3
"""Schema-validated event-sourced workflow state for OpenTgtyLab cases."""
from __future__ import annotations
import argparse, json, os, uuid
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PHASES=('intake','triage','map','hypothesis','deep-analysis','validation','evidence','report','final')
TRANSITIONS={p:{PHASES[i+1]} for i,p in enumerate(PHASES[:-1])}; TRANSITIONS['validation'].add('hypothesis'); TRANSITIONS['final']=set()
LANES={'web','api','source','javascript','pe','apk','firmware','script','document','protocol','capture','pwn','crypto','mixed'}

def now(): return datetime.now(timezone.utc).isoformat()
def validate_document(doc:dict[str,Any],schema:dict[str,Any])->list[str]:
 errors=[]
 for k in schema.get('required',[]):
  if k not in doc: errors.append(f'missing required property: {k}')
 for k,spec in schema.get('properties',{}).items():
  if k not in doc: continue
  v=doc[k]; typ=spec.get('type')
  if typ=='object' and not isinstance(v,dict): errors.append(f'{k} must be object')
  if typ=='array' and not isinstance(v,list): errors.append(f'{k} must be array')
  if typ=='string' and not isinstance(v,str): errors.append(f'{k} must be string')
  if 'const' in spec and v!=spec['const']: errors.append(f'{k} must equal {spec["const"]}')
  if 'enum' in spec and v not in spec['enum']: errors.append(f'{k} invalid value')
  if isinstance(v,dict):
   for req in spec.get('required',[]):
    if req not in v: errors.append(f'{k}.{req} is required')
 return errors

def migrate_v1_state(old):
 slug=old.get('slug') or old.get('case',{}).get('slug') or 'case'
 findings=[]
 for i,x in enumerate(old.get('findings',[]),1):
  x=dict(x) if isinstance(x,dict) else {'title':str(x)}; x.setdefault('id',f'finding-{i:04d}'); x.setdefault('status','lead'); findings.append(x)
 return {'schema_version':'2.0','workflow_id':old.get('workflow_id') or f'wf-{slug}','slug':slug,'case':{'slug':slug},'objective':{'text':old.get('objective',''),'success_conditions':[],'proof_types':[]},'scope':{'targets':[old['target']] if old.get('target') else [],'allowed_actions':[],'constraints':[]},'policy':{'mode':'guided','max_escalation':2},'phase':old.get('phase','intake') if old.get('phase') in PHASES else 'intake','lane':old.get('lane','mixed') if old.get('lane') in LANES else 'mixed','lane_history':[],'assets':[],'artifacts':[],'signals':[],'hypotheses':[],'decisions':[],'tool_runs':[],'evidence':[],'findings':findings,'dead_ends':[],'blockers':old.get('blockers',[]),'budgets':{},'checkpoints':[],'metrics':{},'next_steps':old.get('next_steps',[])}

class WorkflowStore:
 def __init__(self,case_dir): self.case_dir=Path(case_dir).resolve(); self.state_path=self.case_dir/'workflow.json'; self.events_path=self.case_dir/'workflow.events.jsonl'
 def _write(self,state):
  self.case_dir.mkdir(parents=True,exist_ok=True); tmp=self.state_path.with_suffix('.tmp'); tmp.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); os.replace(tmp,self.state_path)
 def _event(self,state,typ,payload,actor='system'):
  event={'event_id':f'evt-{uuid.uuid4().hex}','schema_version':'1.0','workflow_id':state['workflow_id'],'type':typ,'timestamp':now(),'actor':actor,'payload':payload}
  self.case_dir.mkdir(parents=True,exist_ok=True)
  with self.events_path.open('a',encoding='utf-8') as f: f.write(json.dumps(event,ensure_ascii=False)+'\n')
  return event
 def create(self,slug,objective,targets,lane='mixed',mode='guided'):
  state=migrate_v1_state({'slug':slug,'objective':objective,'target':targets[0] if targets else None,'lane':lane}); state['scope']['targets']=list(targets); state['policy']['mode']=mode
  self._event(state,'workflow.created',{'state':deepcopy(state)}); self._write(state); return state
 def load(self): return json.loads(self.state_path.read_text(encoding='utf-8-sig'))
 def transition(self,to_phase,actor='system'):
  state=self.load(); current=state['phase']
  if to_phase not in TRANSITIONS.get(current,set()): raise ValueError(f'invalid transition: {current} -> {to_phase}')
  state['phase']=to_phase; state['case']['updated_at']=now(); self._event(state,'phase.transitioned',{'from':current,'to':to_phase},actor); self._write(state); return state
 def append(self,typ,payload,actor='system'):
  state=self.load(); event=self._event(state,typ,payload,actor)
  key={'hypothesis.added':'hypotheses','evidence.registered':'evidence','finding.promoted':'findings','decision.recorded':'decisions','dead_end.recorded':'dead_ends'}.get(typ)
  if key: state[key].append(payload)
  self._write(state); return event,state

def main():
 p=argparse.ArgumentParser(); p.add_argument('action',choices=['migrate','validate']); p.add_argument('input'); p.add_argument('--output'); a=p.parse_args(); source=Path(a.input); data=json.loads(source.read_text(encoding='utf-8-sig'))
 if a.action=='migrate': out=migrate_v1_state(data); target=Path(a.output) if a.output else source.with_name('workflow.json'); target.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(target)
 else:
  schema=json.loads((Path(__file__).resolve().parents[2]/'schemas'/'workflow-state-v2.schema.json').read_text(encoding='utf-8-sig')); errors=validate_document(data,schema); print(json.dumps({'status':'ok' if not errors else 'error','errors':errors},ensure_ascii=False)); raise SystemExit(bool(errors))
if __name__=='__main__': main()
