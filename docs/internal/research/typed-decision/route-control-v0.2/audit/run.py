"""One isolated design review, reusing the existing bounded CPA transport; no runtime changes."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

REPO = Path('/srv/agentdock/projects/Mindthus')
sys.path.insert(0, str(REPO))
from experiments.typed_decision.contracts import canonical
from experiments.typed_decision.relationship_live import deadline_post_json, no_secrets
from experiments.typed_decision.session import safe_failure_reason
ROOT = Path(__file__).resolve().parent
NEW = ROOT.parent
BASE = NEW.parent / 'mainline-composition-v0.1'
TARGET = '9054cb3a29ca105ee7ca9d6432be19c7b4592c3e'
MODEL = 'deepseek-v4.1-flash'
ENDPOINT = 'https://cpa.72live.com/v1/chat/completions'
SYSTEM = '''你是未参与这份方案编写的独立设计评审者，只按所给完整新设计、继承题文和正式来源判断，不引用外部知识或猜测运行效果。用户已确定：using-mindthus中快速模型做多维观察与有边界路由判断，薄策略默认落实路由，LLM执行方法但可提出具名局部异议；保留Skills/4K定点纠偏。用户允许合理可恢复偏差，要求轻量，不是造核弹。评审该方向是否在本次具体合同中自洽，不是预设PASS，也不是要求零错。
重点核查：是否仍能无声重判；是否反而固化错误且无法纠正；原文与事实/权限是否被误替代；三型用途、多方法主辅和产物依赖是否保留；继承的旧前提/消费是否与新profile冲突；宿主程序控制与仅提示建议是否分清；Score/概率是否越权；已知局部噪声是否触发过重循环。只报最多4个真正影响小实现的发现。可后验验证的精度、概率参数、语义执行不确定性不能自动成为需要再造一层系统的blocker。问题模板数不等于每次问题数。只审这个新差量，旧19题作为继承依据，不重新要求完整平台。
返回一个简短JSON对象：verdict=PASS_WITH_NOTES|REVISE|BLOCKED；summary（最多180汉字）；findings（最多4项，每项id,severity=blocking|tolerable|implementation_test,source_refs,problem,minimal_change）；preserved（最多5项）；implementation_admission（允许什么，不代表什么）；runtime_validation_focus（最多4项）。源引用必须实际存在。没有发现就空数组，不为格式凑缺陷。不要给大改方案、统计样本数量或通用安全阈值。'''

def sha(b): return hashlib.sha256(b).hexdigest()
def read(p): return json.loads(p.read_bytes())
def once(p, x):
    p.parent.mkdir(parents=True, exist_ok=True)
    b=canonical(x)+b'\n'
    if p.exists():
        if p.read_bytes()!=b: raise ValueError('immutable record mismatch')
    else:
        with p.open('xb') as f: f.write(b)

def prepare():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()==TARGET
    hashes={}; files=[]
    def add(p, ranges=None):
        data=p.read_bytes(); hashes[str(p.relative_to(REPO))]=sha(data)
        if ranges:
            lines=data.decode().splitlines()
            content=[{'start_line':lo,'end_line':min(hi,len(lines)), 'text':'\n'.join(f'{i+1}: {lines[i]}' for i in range(lo-1,min(hi,len(lines))))} for lo,hi in ranges]
        else: content=json.loads(data) if p.suffix=='.json' else data.decode()
        files.append({'path':str(p.relative_to(REPO)), 'scope':ranges or 'complete', 'content':content})
    for n in ['design.md','profile.json','acceptance.md']: add(NEW/n)
    for n in ['questions.json','method-bindings.json']: add(BASE/n)
    add(REPO/'skills/using-mindthus/SKILL.md')
    add(REPO/'docs/methodologies/typed-decision-principles.md',[(7,33),(44,68),(91,188)])
    add(REPO/'docs/methodologies/primitives/aspect-ownership.md')
    for method in read(BASE/'method-bindings.json')['methods']:
        add(REPO/method['source_path'],method['contract_review_ranges'])
    add(REPO/'experiments/typed_decision/entry.py',[(155,181)])
    packet={'target_commit':TARGET,'request':'按最新控制权共识定稿并简短独立评审；仅设计，不实施/上线。','files':files,'no_prior_reviews_included':True}
    body={'model':MODEL,'temperature':0,'max_tokens':2800,'stream':False,'response_format':{'type':'json_object'},'messages':[{'role':'system','content':SYSTEM},{'role':'user','content':canonical(packet).decode()}]}
    no_secrets(body); assert len(canonical(body))<=180000
    once(ROOT/'request.json',body)
    once(ROOT/'snapshot.json',{'target_commit':TARGET,'sources':hashes,'request_sha256':sha(canonical(body)),'request_bytes':len(canonical(body)),'model':MODEL,'endpoint':ENDPOINT,'max_calls':1,'retries':0,'max_output_tokens':2800,'deadline_seconds':90,'cost_usd':'unknown unless explicitly returned','isolation':'one fresh context; no old audit opinions; source sections as shown'})
    print(json.dumps({'prepared':True,'source_files':len(hashes),'request_bytes':len(canonical(body)),'calls':0}))

def run():
    m=read(ROOT/'snapshot.json'); body=read(ROOT/'request.json')
    assert sha(canonical(body))==m['request_sha256']
    for name,h in m['sources'].items(): assert sha((REPO/name).read_bytes())==h
    if (ROOT/'outcome.json').exists(): print('already_completed_no_call'); return
    if (ROOT/'intent.json').exists(): raise ValueError('unknown intent: reconcile, no repeat')
    key=os.environ.get('MINDTHUS_HOST_API_KEY'); assert key
    no_secrets(body)
    once(ROOT/'intent.json',{'request_sha256':m['request_sha256'],'time':datetime.now(timezone.utc).isoformat(),'model':MODEL,'retries':0})
    started=time.monotonic(); out={'status':'failed','reported_model':None,'usage':None,'verdict':None,'error':None}
    try:
        raw=deadline_post_json(ENDPOINT,{'Authorization':'Bearer '+key,'Content-Type':'application/json','User-Agent':'Mindthus-Route-Control-Audit/1'},body,90)
        no_secrets(raw); once(ROOT/'response.json',raw)
        out['reported_model']=raw.get('model'); out['usage']=raw.get('usage')
        assert raw.get('model')==MODEL and len(raw['choices'])==1
        c=raw['choices'][0]; assert c['finish_reason']=='stop' and not c['message'].get('tool_calls')
        report=json.loads(c['message']['content'])
        assert report['verdict'] in ('PASS_WITH_NOTES','REVISE','BLOCKED')
        assert isinstance(report['findings'],list) and len(report['findings'])<=4
        once(ROOT/'review.json',report)
        out.update(status='complete',verdict=report['verdict'])
    except Exception as e:
        out['error']=safe_failure_reason(e)
    finally:
        out['elapsed_seconds']=time.monotonic()-started
        once(ROOT/'outcome.json',out)
        print(json.dumps(out,ensure_ascii=False))

if __name__=='__main__':
    {'prepare':prepare,'run':run}[sys.argv[1]]()
