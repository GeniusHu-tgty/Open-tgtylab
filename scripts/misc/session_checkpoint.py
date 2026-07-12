#!/usr/bin/env python3
"""Read-only multi-client security session adapters and compact workflow checkpoints."""
from __future__ import annotations
import hashlib, json, shutil
from pathlib import Path
from typing import Any
from scripts.misc.codex_security_checkpoint import CodexSessionAdapter

class BaseAdapter:
 def __init__(self,path,max_items=50,max_text=1000): self.path=Path(path).resolve(); self.max_items=max_items; self.max_text=max_text
 def clip(self,value):
  text=value if isinstance(value,str) else json.dumps(value,ensure_ascii=False); return text[:self.max_text]+('…' if len(text)>self.max_text else '')
 def finish(self,messages,calls):
  findings=[];steps=[]
  for line in '\n'.join(messages).splitlines():
   low=line.lower()
   if any(x in low for x in ('finding','evidence','confirmed','漏洞','证据')): findings.append(line.strip())
   if any(x in low for x in ('next step','next_steps','下一步','继续')): steps.append(line.strip())
  return {'messages':messages[-20:],'tool_calls':calls[-self.max_items:],'findings':findings[-self.max_items:],'next_steps':steps[-self.max_items:]}

class ClaudeCodeAdapter(BaseAdapter):
 def extract(self):
  messages=[];calls=[]
  for raw in self.path.read_text(encoding='utf-8-sig',errors='replace').splitlines():
   try: row=json.loads(raw)
   except Exception: continue
   msg=row.get('message',{}); content=msg.get('content','') if isinstance(msg,dict) else row.get('content','')
   if isinstance(content,str): messages.append(self.clip(content))
   elif isinstance(content,list):
    for item in content:
     if not isinstance(item,dict): continue
     if item.get('type')=='tool_use': calls.append({'name':item.get('name'),'arguments':self.clip(item.get('input',{}))})
     if item.get('text'): messages.append(self.clip(item['text']))
  return self.finish(messages,calls)

class OpenCodeAdapter(BaseAdapter):
 def extract(self):
  messages=[];calls=[]
  for raw in self.path.read_text(encoding='utf-8-sig',errors='replace').splitlines():
   try: row=json.loads(raw)
   except Exception: continue
   if row.get('content'): messages.append(self.clip(row['content']))
   for call in row.get('tool_calls',[]) or []:
    fn=call.get('function',call); calls.append({'name':fn.get('name'),'arguments':self.clip(fn.get('arguments',{}))})
  return self.finish(messages,calls)

def detect_adapter(path):
 p=Path(path); first={}
 for raw in p.read_text(encoding='utf-8-sig',errors='replace').splitlines():
  try: first=json.loads(raw); break
  except Exception: pass
 if first.get('type') in {'session_meta','event_msg','response_item'}: return 'codex',CodexSessionAdapter(p)
 if 'message' in first and first.get('type') in {'user','assistant','system'}: return 'claude-code',ClaudeCodeAdapter(p)
 return 'opencode',OpenCodeAdapter(p)

def build_unified_checkpoint(session_path,output_path,case_state=None,dry_run=False,backup=True):
 session=Path(session_path).resolve(); output=Path(output_path).resolve(); name,adapter=detect_adapter(session); extracted=adapter.extract()
 delta={k:case_state[k] for k in ('workflow_id','phase','lane','next_steps') if case_state and k in case_state}
 cp={'schema_version':'2.0','kind':'security-workflow-checkpoint','adapter':name,'session_id':extracted.get('session_id',session.stem),'objective':next(iter(extracted.get('messages',[])),''),'findings':extracted.get('findings',[]),'next_steps':extracted.get('next_steps',[]),'tool_calls':extracted.get('tool_calls',[]),'case_delta':delta,'source':{'path':str(session),'sha256':hashlib.sha256(session.read_bytes()).hexdigest()},'resume_hint':'Load case workflow state, merge this bounded delta, skip completed tool runs and dead ends, then continue next_steps.'}
 rendered=json.dumps(cp,ensure_ascii=False,indent=2)+'\n'
 if not dry_run:
  output.parent.mkdir(parents=True,exist_ok=True)
  if backup and output.exists(): shutil.copy2(output,output.with_suffix(output.suffix+'.bak'))
  output.write_text(rendered,encoding='utf-8')
 return {'checkpoint':cp,'metrics':{'source_bytes':session.stat().st_size,'checkpoint_bytes':len(rendered.encode()),'reduction_ratio':round(1-len(rendered.encode())/max(1,session.stat().st_size),4)},'output':str(output),'dry_run':dry_run}
