import json
from pathlib import Path
from scripts.misc.session_checkpoint import ClaudeCodeAdapter, OpenCodeAdapter, build_unified_checkpoint


def test_claude_and_opencode_adapters_extract_minimal_resume_state(tmp_path):
    claude=tmp_path/'claude.jsonl'
    claude.write_text('\n'.join([
      json.dumps({'type':'user','message':{'content':'analyze apk'}}),
      json.dumps({'type':'assistant','message':{'content':[{'type':'tool_use','name':'android_app_baseline','input':{'package_name':'x'}}]}}),
      json.dumps({'type':'assistant','message':{'content':'Evidence: native library. Next step: inspect JNI'}}),
    ]),encoding='utf-8')
    data=ClaudeCodeAdapter(claude).extract()
    assert data['tool_calls'][0]['name']=='android_app_baseline'
    assert data['next_steps']

    opencode=tmp_path/'open.jsonl'
    opencode.write_text('\n'.join([
      json.dumps({'role':'user','content':'inspect PE'}),
      json.dumps({'role':'assistant','content':'Finding: packed. Next step: run die_scan','tool_calls':[{'function':{'name':'die_scan','arguments':'{}'}}]})
    ]),encoding='utf-8')
    data2=OpenCodeAdapter(opencode).extract()
    assert data2['tool_calls'][0]['name']=='die_scan'
    assert data2['findings']


def test_unified_checkpoint_detects_format_and_merges_case_delta(tmp_path):
    session=tmp_path/'open.jsonl'
    session.write_text(json.dumps({'role':'assistant','content':'Next step: validate proof'}),encoding='utf-8')
    out=tmp_path/'cp.json'
    result=build_unified_checkpoint(session,out,case_state={'workflow_id':'wf','phase':'validation'})
    assert result['checkpoint']['adapter']=='opencode'
    assert result['checkpoint']['case_delta']['phase']=='validation'
    assert out.exists()
