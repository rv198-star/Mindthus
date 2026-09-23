"""One-shot independent design review; uses the existing bounded HTTP adapter.
No router changes or business trials. A saved unknown intent is never resubmitted.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime, timezone

REPO = Path('/srv/agentdock/projects/Mindthus')
sys.path.insert(0, str(REPO))
from experiments.typed_decision.contracts import canonical
from experiments.typed_decision.relationship_live import deadline_post_json, no_secrets
from experiments.typed_decision.session import safe_failure_reason

TARGET = '9cc8f846e638aa81317c3c2982423760f7d8fcca'
BASE = REPO / 'docs/internal/research/typed-decision/mainline-composition-v0.1'
OUT = BASE / 'pragmatic-audit-20260923'
MODEL = 'deepseek-v4.1-flash'
ENDPOINT = 'https://cpa.72live.com/v1/chat/completions'
FILES = ['design.md', 'questions.json', 'method-bindings.json', 'policy.json', 'dag.json',
         'acceptance.json', 'evaluation.md', 'iteration-policy.json', 'worked-examples.md', 'verification.json']
USER = '行吧，审计把，其实我有点担心我们做的太重太复杂了，其实也不是要造核弹，是允许一定偏差的'
SYSTEM = '''你是Mindthus主线路由设计的独立审计员。你没有参与该设计，也没有其他审计意见。只依据本次提供的完整设计及正式来源审计，不用外部知识替换方法合同。用户最新要求：关注过重、过复杂，允许一定可恢复语义偏差；不是要求零错，也不是要求以轻量名义删除多方法能力。审计不是寻找尽可能多的缺陷，不预设必须REVISE/PASS。
目标是辅助一个仍对结果负责的LLM更快选对有用的方法和组合，不是把LLM换成自主高风险决策系统。问题模板数不等于每次实例数，DAG节点不等于API调用；阅读实际activation和消费规则后再判复杂。三种原语应在复杂路径各有实际作用，但不要求每个简单任务凑三型。保留合法范围/授权、真实引用与已知未知、调用恢复、方法正式边界。允许非唯一合理路线、轻微排序/深度偏差和可恢复回退。请区分首版有用的低风险opt-in试用与严格统计非劣/全自动默认启用，不让后者的门槛阻塞前者。
对给定的19题逐题做保留/按需/合并/后置/删除判断，并分别说明方法组合、继承已有结果、依赖交接仍如何覆盖。重点查：G01/G02是否把普通输入过度阻断；M01/M02/M04的成本收益；M03/R02/R03/V02重叠；S01/S02是否有明确用途；CAL/LOCKED、多角色与非劣门槛适合哪个阶段；7请求/180秒是最大容量而非默认预算。不要以增加检查解决每个不确定，不新增平台。值得保留的复杂性也要明确。
只返回一个JSON对象，中文正文，字段：
verdict (PASS_WITH_NOTES|REVISE_BEFORE_IMPLEMENTATION|BLOCKED)、summary、reviewed_question_ids（19个ID），findings（最多6项；id, severity=must_fix_for_MVP|should_simplify|tolerable|later_validation, source_refs, problem, consequence, minimal_change, does_not_prove），question_disposition（19项；id, action=keep_core|conditional|merge|defer|remove, merge_with可为null, reason），minimum_viable_path（原语用途、正常与升级路径，列出保留的能力和暂不做的机制），tolerance_policy（acceptable, unacceptable, unresolved_does_not_always_mean_stop），acceptance_now（轻量可操作、不得声称统计证明），validation_later，implementation_admission（是否可开始哪个离线/建议型切片以及真正前置修订），risks_of_over_simplifying。引用必须来自包中实际文件/问题ID/章节；不凭空制造测量值。所有建议样本数/阈值/预算都标proposal，不宣称是已验证界限。'''

def sha(x): return hashlib.sha256(x).hexdigest()
def read(p): return json.loads(p.read_bytes())
def once(p, x):
    p.parent.mkdir(parents=True, exist_ok=True)
    blob = canonical(x) + b'\n'
    if p.exists():
        if p.read_bytes() != blob: raise RuntimeError('immutable audit record mismatch')
    else:
        with p.open('xb') as f: f.write(blob)
def git_head(): return subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip()

def prepare():
    assert git_head() == TARGET
    sources, inputs = {}, []
    for name in FILES:
        p=BASE/name; sources[str(p.relative_to(REPO))]=sha(p.read_bytes())
        inputs.append({'path':str(p.relative_to(REPO)), 'content':read(p) if p.suffix=='.json' else p.read_text()})
    canonical_sources=[]
    whole=['skills/using-mindthus/SKILL.md','docs/methodologies/typed-decision-principles.md','docs/methodologies/primitives/aspect-ownership.md']
    for name in whole:
        p=REPO/name; sources[name]=sha(p.read_bytes())
        canonical_sources.append({'path':name,'range':'complete','content':p.read_text()})
    for m in read(BASE/'method-bindings.json')['methods']:
        name=m['source_path']; p=REPO/name; lines=p.read_text().splitlines(); sources[name]=sha(p.read_bytes())
        assert sources[name]==m['source_sha256']
        chunks=[]
        for lo,hi in m['contract_review_ranges']:
            chunks.append({'start_line':lo,'end_line':hi,'content':'\n'.join(f'{i+1}: {lines[i]}' for i in range(lo-1,min(hi,len(lines))))})
        canonical_sources.append({'path':name,'declared_contract_review_ranges':chunks})
    packet={'task':'一轮实用性与比例性独立设计审计','target_commit':TARGET,'owner_latest_request':USER,
        'context':'八方法路由与必要多方法组合是主线；Skills/4K只为具体回归痛点。已有D3工程与有界实测，MR-01为未实现设计。无其他审计意见。',
        'design_files':inputs,'canonical_sources':canonical_sources}
    body={'model':MODEL,'temperature':0,'max_tokens':6500,'stream':False,'response_format':{'type':'json_object'},
          'messages':[{'role':'system','content':SYSTEM},{'role':'user','content':canonical(packet).decode()}]}
    no_secrets(body)
    assert len(canonical(body)) <= 262144
    meta={'target_commit':TARGET,'input_file_hashes':sources,'request_sha256':sha(canonical(body)),
          'request_bytes':len(canonical(body)),'provider':'CPA','endpoint':ENDPOINT,'model':MODEL,
          'max_tokens':6500,'timeout_seconds':90,'max_calls':1,'automatic_retries':0,'default_or_runtime_changes':False,
          'author_review_included':False,'historical_audit_outputs_included':False,'review_scope':'design_readonly; no semantic testing; one isolated context',
          'actual_cost':'unknown_unless_provider_reported'}
    once(OUT/'source-snapshot.json',meta); once(OUT/'request.json',body)
    print(json.dumps({'prepared':True,'source_files':len(sources),'request_bytes':meta['request_bytes'],'new_model_calls':0}))

def run():
    meta=read(OUT/'source-snapshot.json'); body=read(OUT/'request.json')
    assert git_head()==TARGET and sha(canonical(body))==meta['request_sha256']
    for name,h in meta['input_file_hashes'].items(): assert sha((REPO/name).read_bytes())==h
    if (OUT/'outcome.json').exists():
        print(json.dumps({'already_complete':True})); return
    if (OUT/'intent.json').exists(): raise RuntimeError('unknown intent; reconcile, do not repeat')
    key=os.environ.get('MINDTHUS_HOST_API_KEY',''); assert key
    no_secrets(body)
    once(OUT/'intent.json',{'request_sha256':meta['request_sha256'],'requested_model':MODEL,
                          'endpoint':ENDPOINT,'sent_at':datetime.now(timezone.utc).isoformat(),'retries':0})
    begin=time.monotonic(); out={'status':'failed','requested_model':MODEL,'reported_model':None,
        'usage':None,'elapsed_seconds':None,'error':None}
    try:
        raw=deadline_post_json(ENDPOINT,{'Authorization':'Bearer '+key,'Content-Type':'application/json',
                              'User-Agent':'Mindthus-Pragmatic-Audit/1'},body,90)
        no_secrets(raw)
        once(OUT/'response.json',raw)
        out['reported_model']=raw.get('model'); out['usage']=raw.get('usage')
        assert raw.get('model')==MODEL
        choices=raw.get('choices'); assert isinstance(choices,list) and len(choices)==1
        choice=choices[0]; out['finish_reason']=choice.get('finish_reason')
        assert choice.get('finish_reason')=='stop' and not choice['message'].get('tool_calls')
        report=json.loads(choice['message']['content']); assert isinstance(report,dict)
        wanted={q['id'] for q in read(BASE/'questions.json')['questions']}
        assert set(report['reviewed_question_ids'])==wanted
        assert {q['id'] for q in report['question_disposition']}==wanted and len(report['question_disposition'])==len(wanted)
        once(OUT/'review.json',report); out['status']='complete'; out['verdict']=report['verdict']
    except Exception as e:
        out['error']=safe_failure_reason(e)
    finally:
        out['elapsed_seconds']=time.monotonic()-begin
        once(OUT/'outcome.json',out)
        print(json.dumps(out,ensure_ascii=False))

if __name__=='__main__':
    if sys.argv[1]=='prepare': prepare()
    elif sys.argv[1]=='run': run()
    else: raise SystemExit(2)
