import subprocess, selectors, json, time, hashlib
from pathlib import Path

BINARY='/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex'
ROOT=Path('/tmp/mindthus-211-transport-check');ROOT.mkdir(exist_ok=True)
SAFE=('name','wire_api','request_max_retries','stream_max_retries','supports_websockets','requires_openai_auth')

def check(label, overrides):
    cmd=[BINARY,'app-server','--stdio','--strict-config','-c','model="gpt-6-sol"','-c','model_reasoning_effort="xhigh"']
    for value in overrides:cmd+=['-c',value]
    messages=[{'id':1,'method':'initialize','params':{'clientInfo':{'name':'mindthus_config_read_only','version':'1'},'capabilities':{'experimentalApi':True}}},
              {'id':2,'method':'config/read','params':{'includeLayers':False}}]
    # The only protocol methods used are initialize, initialized and config/read.
    # No thread, turn, prompt, credentials, provider request or model probe.
    began=time.monotonic();result={'label':label,'overrides':overrides,'methods_sent':[]}
    with (ROOT/(label+'.stderr.txt')).open('w') as err:
        proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,text=True,cwd=ROOT)
        selector=selectors.DefaultSelector();selector.register(proc.stdout,selectors.EVENT_READ)
        try:
            for msg in messages:
                proc.stdin.write(json.dumps(msg)+'\n');proc.stdin.flush();result['methods_sent'].append(msg['method'])
                deadline=time.monotonic()+15
                while time.monotonic()<deadline:
                    if not selector.select(timeout=0.5):
                        if proc.poll() is not None:break
                        continue
                    line=proc.stdout.readline()
                    if not line:break
                    data=json.loads(line)
                    if data.get('id')!=msg['id']:continue
                    if 'error' in data:result['error']=data['error']
                    elif msg['id']==1:result['initialize']=data['result']
                    else:
                        config=data['result']['config']
                        result['parsed_config']={k:config.get(k) for k in ('model','model_provider','model_reasoning_effort')}
                        result['parsed_config']['model_providers']={k:{field:v.get(field) for field in SAFE if field in v} for k,v in config.get('model_providers',{}).items()}
                        result['parsed_config']['unbounded_connection_retries']=config.get('features',{}).get('unbounded_connection_retries')
                    break
                if msg['id']==1 and 'initialize' in result:
                    proc.stdin.write(json.dumps({'method':'initialized'})+'\n');proc.stdin.flush();result['methods_sent'].append('initialized')
                if proc.poll() is not None:break
        except BrokenPipeError:result['stdin_closed']=True
        finally:
            proc.stdin.close()
            try:proc.wait(timeout=5)
            except subprocess.TimeoutExpired:proc.terminate();proc.wait(timeout=5)
            selector.close()
        result.update(returncode=proc.returncode,elapsed_seconds=time.monotonic()-began)
    result['stderr']= (ROOT/(label+'.stderr.txt')).read_text()
    # Whitelisted projections above deliberately exclude auth/config secret fields.
    (ROOT/(label+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)

check('baseline',[])
check('builtin-override',['model_providers.openai.name="OpenAI"','model_providers.openai.request_max_retries=0','model_providers.openai.stream_max_retries=0','model_providers.openai.supports_websockets=false'])
check('candidate-official-alias',['model_provider="mindthus_official_http"','model_providers.mindthus_official_http.name="OpenAI"','model_providers.mindthus_official_http.requires_openai_auth=true','model_providers.mindthus_official_http.request_max_retries=0','model_providers.mindthus_official_http.stream_max_retries=0','model_providers.mindthus_official_http.supports_websockets=false','features.unbounded_connection_retries=false'])
