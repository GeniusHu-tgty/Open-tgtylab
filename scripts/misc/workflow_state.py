#!/usr/bin/env python3
"""Schema-validated event-sourced workflow state for OpenTgtyLab cases."""
from __future__ import annotations
import argparse, hashlib, json, os, uuid
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
 def walk(value,spec,path):
  typ=spec.get('type')
  checks={'object':dict,'array':list,'string':str,'integer':int,'number':(int,float),'boolean':bool}
  if typ in checks and not isinstance(value,checks[typ]): errors.append(f'{path or "document"} must be {typ}'); return
  if 'const' in spec and value!=spec['const']: errors.append(f'{path or "document"} must equal {spec["const"]}')
  if 'enum' in spec and value not in spec['enum']: errors.append(f'{path or "document"} invalid value')
  if isinstance(value,dict):
   for req in spec.get('required',[]):
    if req not in value: errors.append(f'{path+"." if path else ""}{req} is required')
   for key,child in spec.get('properties',{}).items():
    if key in value: walk(value[key],child,f'{path+"." if path else ""}{key}')
  if isinstance(value,list) and spec.get('items'):
   for i,item in enumerate(value): walk(item,spec['items'],f'{path}[{i}]')
 walk(doc,schema,'')
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
 def _event(self,state,typ,payload,actor='system',expected_revision=None):
  existing=[]
  if self.events_path.exists(): existing=[json.loads(x) for x in self.events_path.read_text(encoding='utf-8').splitlines() if x.strip()]
  if expected_revision is not None and expected_revision != len(existing): raise ValueError(f'revision conflict: expected {expected_revision}, current {len(existing)}')
  revision=len(existing)+1; previous=existing[-1].get('event_hash','') if existing else ''
  event={'event_id':f'evt-{uuid.uuid4().hex}','schema_version':'1.0','workflow_id':state['workflow_id'],'type':typ,'timestamp':now(),'actor':actor,'revision':revision,'previous_event_hash':previous,'payload':payload}
  canonical=json.dumps(event,ensure_ascii=False,sort_keys=True,separators=(',',':')); event['event_hash']=hashlib.sha256(canonical.encode()).hexdigest()
  self.case_dir.mkdir(parents=True,exist_ok=True)
  with self.events_path.open('a',encoding='utf-8') as f: f.write(json.dumps(event,ensure_ascii=False)+'\n'); f.flush(); os.fsync(f.fileno())
  return event
 def create(self,slug,objective,targets,lane='mixed',mode='guided'):
  state=migrate_v1_state({'slug':slug,'objective':objective,'target':targets[0] if targets else None,'lane':lane}); state['scope']['targets']=list(targets); state['policy']['mode']=mode
  self._event(state,'workflow.created',{'state':deepcopy(state)}); self._write(state); return state
 def load(self):
  previous=''; expected=1
  for line in self.events_path.read_text(encoding='utf-8').splitlines():
   if not line.strip(): continue
   event=json.loads(line); supplied=event.get('event_hash',''); unsigned={k:v for k,v in event.items() if k!='event_hash'}; calculated=hashlib.sha256(json.dumps(unsigned,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
   if supplied!=calculated: raise ValueError('event hash mismatch')
   if event.get('revision')!=expected or event.get('previous_event_hash','')!=previous: raise ValueError('event chain mismatch')
   previous=supplied; expected+=1
  return json.loads(self.state_path.read_text(encoding='utf-8-sig'))
 def transition(self,to_phase,actor='system',deliverables=None):
  state=self.load(); current=state['phase']
  if to_phase not in TRANSITIONS.get(current,set()): raise ValueError(f'invalid transition: {current} -> {to_phase}')
  state['phase']=to_phase; state['case']['updated_at']=now(); self._event(state,'phase.transitioned',{'from':current,'to':to_phase,'phase':to_phase,'gate':{'satisfied':True},'deliverables':deliverables or {}},actor); self._write(state); return state
 def append(self,typ,payload,actor='system',expected_revision=None):
  state=self.load(); wrappers={'hypothesis.added':'hypothesis','evidence.registered':'evidence','finding.promoted':'finding','decision.recorded':'decision','dead_end.recorded':'dead_end'}; event_payload={wrappers[typ]:payload} if typ in wrappers else payload; event=self._event(state,typ,event_payload,actor,expected_revision)
  key={'hypothesis.added':'hypotheses','evidence.registered':'evidence','finding.promoted':'findings','decision.recorded':'decisions','dead_end.recorded':'dead_ends'}.get(typ)
  if key: state[key].append(payload)
  self._write(state); return event,state

def main():
 p=argparse.ArgumentParser(); p.add_argument('action',choices=['migrate','validate']); p.add_argument('input'); p.add_argument('--output'); a=p.parse_args(); source=Path(a.input); data=json.loads(source.read_text(encoding='utf-8-sig'))
 if a.action=='migrate': out=migrate_v1_state(data); target=Path(a.output) if a.output else source.with_name('workflow.json'); target.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(target)
 else:
  schema=json.loads((Path(__file__).resolve().parents[2]/'schemas'/'workflow-state-v2.schema.json').read_text(encoding='utf-8-sig')); errors=validate_document(data,schema); print(json.dumps({'status':'ok' if not errors else 'error','errors':errors},ensure_ascii=False)); raise SystemExit(bool(errors))
if __name__=='__main__': main()
