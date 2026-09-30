"""Owner's final named attempt; the existing adapter/dispatcher owns all sends."""
import json,time
from experiments.grounded_judgment import runtime as rt
from experiments.grounded_judgment.dispatch import Dispatcher,OfficialAdapters
from experiments.grounded_judgment.complete_missing import PATHS,verified
from experiments.typed_decision.relationship_runtime import _locked
from run import BATCH,checkpoint


def main():
    with _locked(BATCH/'.execution.lock'):
        verified(BATCH)
        driver=Dispatcher(BATCH,OfficialAdapters())
        print(json.dumps({'order':PATHS,'started_epoch':time.time(),'automatic_driver_retries':False,'last_named_attempt':'000077'}),flush=True)
        for name in PATHS:
            while True:
                s=rt.state(BATCH/'runs'/name)
                if s['stopped']:
                    print(json.dumps({'completion_attempt_abandoned':True,'path':name,'reason':s['stopped']}),flush=True)
                    checkpoint();return
                if s['phase']=='done':break
                print(json.dumps({'dispatch':name,'phase':s['phase'],'prior_calls':s['call_count'],'at_epoch':time.time()}),flush=True)
                s=driver.step(name);summary=checkpoint()
                print(json.dumps({'returned':name,'phase':s['phase'],'stopped':s['stopped'],'batch_calls':summary['logical_calls'],'at_epoch':time.time()}),flush=True)
                if s['stopped']:
                    print(json.dumps({'completion_attempt_abandoned':True,'path':name,'reason':s['stopped']}),flush=True)
                    return
                verified(BATCH)
            print(json.dumps({'path_end':name,'phase':s['phase']}),flush=True)
        print(json.dumps({'completed_batch':True,'counts':{k:checkpoint()[k] for k in ('logical_calls','host_calls','jev_calls')}}),flush=True)


if __name__=='__main__':main()
