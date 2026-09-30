"""One authorized 24-path batch. No retry, evaluator model, or unknown disposition."""
import json
import time
from pathlib import Path

from experiments.grounded_judgment import runtime as rt
from experiments.grounded_judgment.dispatch import Dispatcher, OfficialAdapters
from experiments.grounded_judgment.resume_000007 import load_official_credential
from experiments.typed_decision.contracts import digest
from experiments.typed_decision.relationship_runtime import _locked

HERE=Path(__file__).resolve().parent
BATCH=Path('/Users/william/.codex/tmp/gj-extended-v1-run')


def checkpoint():
    rows=[]
    for run in sorted((BATCH/'runs').iterdir()):
        s=rt.state(run)
        row={'path':run.name,'status':'delivered' if s['phase']=='done' and not s['stopped'] else s['stopped'] or 'not_finished',
             'phase':s['phase'],'calls':s['call_count'],'host_calls':s['host_logical_calls'],
             'jev_calls':s['call_count']-s['host_logical_calls'],'reads':s['read_count'],
             'checks':s['check_count'],'revisions':s['revision_count'],
             'draft':s['draft'],'check':s.get('check'),'final':s['final'],
             'atoms':s['atoms'],'composition':s['composition'],'measurements':s['measurements'],
             'session_seconds':sum(x.get('session_seconds') or 0 for x in s['measurements']),
             'active_wait_seconds':sum(x.get('active_wait_seconds') or 0 for x in s['measurements'])}
        rows.append(row)
        if s['phase']=='done' or s['stopped']:
            directory=HERE/'answers';directory.mkdir(exist_ok=True)
            # Checkpoints may be refreshed, but request/response/event evidence is immutable.
            (directory/(run.name+'.json')).write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n')
            text='# '+run.name+'\n\n状态：'+row['status']+'\n\n## 首稿\n\n'+(s['draft'] or '无')
            text+='\n\n## 检查\n\n```json\n'+json.dumps(s.get('check'),ensure_ascii=False,indent=2)+'\n```'
            text+='\n\n## 最终稿\n\n'+(s['final'] or '无')+'\n'
            (directory/(run.name+'.md')).write_text(text)
    summary={'paths':rows,'batch_sha256':digest(rt.read(BATCH/'batch.json')),
             'logical_calls':sum(x['calls'] for x in rows),'host_calls':sum(x['host_calls'] for x in rows),
             'jev_calls':sum(x['jev_calls'] for x in rows),'simulation':False,'holdout':False,
             'cost':None,'exact_http_requests':None,
             'session_seconds':sum(x['session_seconds'] for x in rows),
             'active_wait_seconds':sum(x['active_wait_seconds'] for x in rows)}
    (HERE/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    return summary


def main():
    print(json.dumps({'credential':load_official_credential()},ensure_ascii=False),flush=True)
    cases=list(rt.read(BATCH/'inputs.json'))
    # Balance the order across eight cases, without sharing outputs between arms.
    orders=(('A','B','C'),('C','B','A'),('B','C','A'),('A','C','B'),
            ('C','A','B'),('B','A','C'),('A','B','C'),('C','B','A'))
    order=[name+'-'+arm for name,arms in zip(cases,orders) for arm in arms]
    print(json.dumps({'order':order,'no_retries':True,'started_epoch':time.time()}),flush=True)
    driver=Dispatcher(BATCH,OfficialAdapters())
    with _locked(BATCH/'.execution.lock'):
        for name in order:
            while True:
                s=rt.state(BATCH/'runs'/name)
                if s['phase']=='done' or s['stopped']:break
                print(json.dumps({'dispatch':name,'phase':s['phase'],'prior_calls':s['call_count'],'at_epoch':time.time()}),flush=True)
                s=driver.step(name)
                summary=checkpoint()
                print(json.dumps({'returned':name,'phase':s['phase'],'stopped':s['stopped'],
                                  'batch_calls':summary['logical_calls'],'at_epoch':time.time()}),flush=True)
                if list(BATCH.glob('STOP*.json')):
                    print(json.dumps({'batch_stop':True,'path':name,'reason':s['stopped']}),flush=True)
                    return
            checkpoint()
            print(json.dumps({'path_end':name,'phase':s['phase'],'stopped':s['stopped']}),flush=True)
        print(json.dumps({'completed_batch':True,'counts':{k:checkpoint()[k] for k in ('logical_calls','host_calls','jev_calls')}}),flush=True)


if __name__=='__main__':main()
