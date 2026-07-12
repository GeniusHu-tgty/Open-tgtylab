#!/usr/bin/env python3
"""Extract compact, resumable security-research checkpoints from Codex JSONL sessions."""
from __future__ import annotations
import argparse, hashlib, json, re, shutil
from pathlib import Path
from typing import Any

class CodexSessionAdapter:
 def __init__(self,path:str|Path,max_items:int=50,max_text:int=1000): self.path=Path(path).expanduser().resolve(); self.max_items=max_items; self.max_text=max_text
 def _clip(self,value:Any)->str:
  text=value if isinstance(value,str) else json.dumps(value,ensure_ascii=False)
  return text[:self.max_text]+('…' if len(text)>self.max_text else '')
 def extract(self)->dict[str,Any]:
  session_id=''; cwd=''; token_usage={}; calls=[]; outputs=[]; messages=[]; errors=[]
  for number,raw in enumerate(self.path.read_text(encoding='utf-8-sig',errors='replace').splitlines(),1):
   try: item=json.loads(raw)
   except Exception: errors.append({'line':number,'error':'invalid_json'}); continue
   typ=item.get('type'); p=item.get('payload',{})
   if typ=='session_meta': session_id=p.get('session_id') or p.get('id') or session_id; cwd=p.get('cwd',cwd)
   elif typ=='event_msg' and p.get('type')=='token_count': token_usage=p.get('info',{}).get('total_token_usage',token_usage)
   elif typ=='response_item' and p.get('type')=='function_call': calls.append({'name':p.get('name'),'namespace':p.get('namespace'),'arguments':self._clip(p.get('arguments',''))})
   elif typ=='response_item' and p.get('type')=='function_call_output': outputs.append(self._clip(p.get('output','')))
   elif typ=='event_msg' and p.get('type') in {'agent_message','user_message'}: messages.append(self._clip(p.get('message','')))
  text='\n'.join(messages+outputs); next_steps=[]; findings=[]
  for part in text.splitlines():
   low=part.lower().strip()
   if any(k in low for k in ('next step','next_steps','下一步','继续')): next_steps.append(part.strip())
   if any(k in low for k in ('finding','vulnerability','confirmed','漏洞','证据','evidence')): findings.append(part.strip())
  return {'session_id':session_id or self.path.stem,'cwd':cwd,'source':str(self.path),'token_usage':token_usage,'tool_calls':calls[-self.max_items:],'tool_outputs':outputs[-10:],'findings':findings[-self.max_items:],'next_steps':next_steps[-self.max_items:],'messages':messages[-20:],'parse_errors':errors}

def build_checkpoint(session_path:str|Path,output_path:str|Path,dry_run:bool=False,backup:bool=True)->dict[str,Any]:
 session=Path(session_path).expanduser().resolve(); output=Path(output_path).expanduser().resolve(); extracted=CodexSessionAdapter(session).extract()
 checkpoint={'schema_version':'1.0','kind':'codex-security-research-checkpoint','session_id':extracted['session_id'],'workspace':extracted['cwd'],'objective':next((m for m in extracted['messages'] if m),''),'findings':extracted['findings'],'next_steps':extracted['next_steps'],'tool_calls':extracted['tool_calls'],'token_usage':extracted['token_usage'],'source':{'path':str(session),'sha256':hashlib.sha256(session.read_bytes()).hexdigest()},'resume_hint':'Read this checkpoint, validate artifacts/case state, then continue next_steps without replaying completed tools.'}
 rendered=json.dumps(checkpoint,ensure_ascii=False,indent=2)+'\n'; result={'checkpoint':checkpoint,'metrics':{'source_bytes':session.stat().st_size,'checkpoint_bytes':len(rendered.encode()),'reduction_ratio':round(1-len(rendered.encode())/max(1,session.stat().st_size),4)},'output':str(output),'dry_run':dry_run}
 if not dry_run:
  output.parent.mkdir(parents=True,exist_ok=True)
  if backup and output.exists(): shutil.copy2(output,output.with_suffix(output.suffix+'.bak'))
  output.write_text(rendered,encoding='utf-8')
 return result

def latest_session(root:Path)->Path:
 files=sorted(root.rglob('*.jsonl'),key=lambda p:p.stat().st_mtime,reverse=True)
 if not files: raise FileNotFoundError(root)
 return files[0]

def main()->int:
 ap=argparse.ArgumentParser(); ap.add_argument('--session'); ap.add_argument('--latest',action='store_true'); ap.add_argument('--session-root',default=str(Path.home()/'.codex'/'sessions')); ap.add_argument('--output'); ap.add_argument('--dry-run',action='store_true'); ap.add_argument('--no-backup',action='store_true'); a=ap.parse_args()
 session=latest_session(Path(a.session_root)) if a.latest or not a.session else Path(a.session); output=Path(a.output) if a.output else Path.cwd()/'exports'/'checkpoints'/f'{session.stem}.checkpoint.json'; print(json.dumps(build_checkpoint(session,output,a.dry_run,not a.no_backup),ensure_ascii=False,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
