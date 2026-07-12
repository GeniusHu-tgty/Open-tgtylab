import json
from pathlib import Path
from scripts.misc.codex_security_checkpoint import CodexSessionAdapter, build_checkpoint


def line(t,p): return json.dumps({'timestamp':'2026-01-01T00:00:00Z','type':t,'payload':p},ensure_ascii=False)

def test_adapter_extracts_goal_tools_findings_and_cost(tmp_path):
    f=tmp_path/'rollout.jsonl'
    f.write_text('\n'.join([
      line('session_meta',{'session_id':'abc','cwd':'D:/lab'}),
      line('event_msg',{'type':'token_count','info':{'total_token_usage':{'total_tokens':1200,'cached_input_tokens':400}}}),
      line('response_item',{'type':'function_call','name':'hunter_recon','arguments':'{"target":"x"}'}),
      line('response_item',{'type':'function_call_output','output':'{"status":"ok","findings":["admin endpoint"]}'}),
      line('event_msg',{'type':'agent_message','message':'Next steps: verify IDOR'}),
    ]),encoding='utf-8')
    data=CodexSessionAdapter(f).extract()
    assert data['session_id']=='abc'; assert data['token_usage']['total_tokens']==1200
    assert data['tool_calls'][0]['name']=='hunter_recon'; assert 'verify IDOR' in data['next_steps'][0]

def test_checkpoint_is_compact_dry_run_backup_and_idempotent(tmp_path):
    session=tmp_path/'s.jsonl'; session.write_text(line('session_meta',{'session_id':'s','cwd':str(tmp_path)})+'\n'+line('response_item',{'type':'function_call_output','output':'X'*100000}),encoding='utf-8')
    out=tmp_path/'checkpoint.json'; preview=build_checkpoint(session,out,dry_run=True)
    assert not out.exists(); assert preview['metrics']['source_bytes']>preview['metrics']['checkpoint_bytes']
    first=build_checkpoint(session,out,backup=True); second=build_checkpoint(session,out,backup=True)
    assert out.exists(); assert first['checkpoint']==second['checkpoint']
