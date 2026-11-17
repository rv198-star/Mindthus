from __future__ import annotations
import copy,hashlib,json,sys
from pathlib import Path
ROOT=Path('/Users/william/.codex/worktrees/mindthus-246-collaboration/Mindthus')
sys.path[:0]=[str(ROOT/'skills/tplan/scripts')]
import collaboration as col
import collaboration_runtime as api
import tplan_runtime as rt
WORLD=Path(Path('/private/tmp/mindthus246-live-location').read_text().strip())
MISSION=WORLD/'mission'
A='01a1e806-292f-76d0-af7e-f4786d70b3e1'
B='01a1e873-14df-76b0-bead-411483962104'
C='01a1ea10-30b5-7af3-8f00-0c6b4dca2daa'
AUTH='source-user-approval-after-R5-2026-11-17'

def state():return rt.read_mission(MISSION)
def log(event):
 record={'timestamp':rt.now_iso(),'source_thread_id':A,'code_head':'223b7d2b99969c6a6ee9549730d2b8a2271d2401','evidence_class':'live_host_bounded_canary_exercise',**event}
 with (WORLD/'audit/host-events.jsonl').open('a') as out:out.write(json.dumps(record,ensure_ascii=False)+'\n')
def view():
 s=state();c=s.get('collaboration',{})
 return {'objective':s['mission']['objective'],'acceptance':s['mission']['acceptance_evidence'],'mission_status':s['mission']['status'],'focus':s['active_task_id'],'tasks':{t['id']:t['status'] for t in s['tasks']},'delegations':copy.deepcopy(c.get('delegations',{})),'intents':copy.deepcopy(c.get('intents',{})),'pending':{k:v for k,v in c.get('feedback',{}).items() if v['status']=='pending'},'coordination':copy.deepcopy(c.get('coordination',{}))}
def request(action,payload,command_id,expected_snapshot):
 return {'protocol':col.PROTOCOL,'action':action,'mission_id':'mindthus246-live-host','command_id':command_id,'expected_build_hash':rt.runtime_fingerprint()['build_hash'],'expected_snapshot':expected_snapshot,'payload':payload}
def snapshot():
 r,k=api.execute(MISSION,request('snapshot.get',{},'host-read',None),principal='host-a');assert k==0,r
 return r

def call(action,payload,*,command_id=None,decision):
 before=state();snap=snapshot()
 number=len((WORLD/'audit/host-events.jsonl').read_text().splitlines()) if (WORLD/'audit/host-events.jsonl').exists() else 0
 req=request(action,payload,command_id or f'host-{number}-{action.replace(".","-")}',snap['data']['expected_snapshot'])
 result,code=api.execute(MISSION,req,principal='host-a')
 log({'operation':action,'source_decision':decision,'request':req,'response':result,'exit_code':code,'before':before,'after':state()})
 assert code==0,result
 return result

def prepare(delegation,round_no,input_refs,instruction):
 return call('delegation.prepare',{'coordinator_generation':1,'delegation_id':delegation,'intent_id':'I'+delegation[1:],'task_id':'T1','round':round_no,'assignee_id':'B','write_scope':'host-artifact-normalizer','contract_version':'host-normalizer-v1','instruction_summary':instruction,'input_refs':input_refs,'dependency_versions':{'contract':'host-normalizer-v1','runtime':'223b7d2b9'},'required_review':{'required':True,'reviewer_id':'C','scope_refs':['contract://host-normalizer-v1/all']}},decision='A retains contract and acceptance; B receives only this bounded artifact task')

def dispatch(intent,send,execution,refs,reason,*,stop=False):
 return call('dispatch.record',{'coordinator_generation':1,'intent_id':intent,'send_state':send,'execution_state':execution,'stop_requested':stop,'native_refs':refs,'observed_at':rt.now_iso(),'reason':reason},decision=reason)

def record(role,event_ref,summary,delegation,round_no,*,kind,artifact=None,original_ref,attachments=()):
 return call('feedback.record',{'coordinator_generation':1,'kind':kind,'source_event_ref':event_ref,'source_thread_ref':B if role=='B' else C,'source_host_ref':'local','source_role_id':role,'delegation_id':delegation,'round':round_no,'contract_version':'host-normalizer-v1','artifact_ref':artifact['ref'] if artifact else None,'artifact_digest':artifact['digest'] if artifact else None,'summary':summary,'original_ref':original_ref,'attachment_refs':list(attachments)},decision='A imports an observed ordinary peer return as candidate facts; preserves source and current work focus')

def resolve(feedback,disposition,rationale,*,artifact=None,review=None,changes=(),next_action='Continue A contract/evidence checks while the current peer batch proceeds',focus='T2',evidence_refs=()):
 return call('feedback.resolve',{'coordinator_generation':1,'feedback_id':feedback,'disposition':disposition,'goal_relation':{'responsibility':'A owns user goal, contract, evidence qualification and acceptance; B implements and C independently reviews','acceptance_ids':['ART','HOST','FOCUS'],'rationale':rationale},'evidence_refs':list(evidence_refs),'artifact_ref':artifact,'review':review,'task_changes':list(changes),'new_tasks':[],'next_delegation':None,'coordination':{'state':'working','focus_task_id':focus,'gap_summary':'Need fixed current artifact, independent review and observed host evidence before final acceptance','next_action':next_action,'resume_basis':[focus] if focus else [],'waiting_on':[],'rationale':rationale}},decision=rationale)

def artifact(directory):
 p=Path(directory);files={str(f.relative_to(p)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(p.rglob('*')) if f.is_file() and '__pycache__' not in f.parts}
 return {'ref':str(p),'digest':col.digest(files),'files':files}
