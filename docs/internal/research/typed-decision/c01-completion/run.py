"""One bounded feedback batch for the completed C01 integration path."""
import json
from pathlib import Path
import sys
import time
REPO=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(REPO))
from experiments.typed_decision import c01_host,handoff
from experiments.typed_decision.contracts import digest,require
from experiments.typed_decision.providers import TypeSafeJevProvider
from experiments.typed_decision.session import read_record,write_once,implementation_digest
DOCS=Path(__file__).resolve().parent
METHODS=DOCS.parent/'language-diagnostic/english'
SOURCE=Path('/Users/william/Documents/Codex/2026-09-22/mindthus-c01-implementation/trial')
IDS=['L27','L28','L22','N03']

def prepare():
    original={c['id']:c for c in json.loads((DOCS.parent/'c01-implementation/cases.json').read_text())['cases']}
    rows={r['case_id']:r for r in read_record(SOURCE/'summary.json')['rows']}
    bundles={ident:handoff.prepare(SOURCE/ident,rows[ident]['run_id'],original[ident]['context'],METHODS) for ident in IDS}
    manifest=c01_host.admission(json.loads((DOCS/'E01-context.json').read_text()),METHODS,'deepseek-v4.1-flash',
                               'Owner requested uninterrupted C01 implementation; c01-completion/protocol.md')
    files=[Path(__file__).resolve(),DOCS/'protocol.md',DOCS/'E01-context.json',DOCS/'technical-recovery.md']
    frozen={'implementation':implementation_digest(),'files':{str(p.relative_to(REPO)):__import__('hashlib').sha256(p.read_bytes()).hexdigest() for p in files},
            'host_requests':{i:digest(c01_host.host_body(b,'deepseek-v4.1-flash')) for i,b in bundles.items()},
            'handoff_digests':{i:digest(b) for i,b in bundles.items()},'chain_manifest':manifest,
            'max_host_calls':5,'max_jev_calls':3,'host_model':'deepseek-v4.1-flash','semantic_revisions':0,'retries':0}
    return frozen,bundles

def run(root,key,*,freeze_path=DOCS/'freeze.json'):
    frozen,bundles=prepare()
    require(frozen==json.loads(freeze_path.read_text()),'frozen source/input changed')
    require(not root.exists(),'batch terminal; do not replay paid feedback')
    write_once(root/'manifest.json',frozen)
    started=time.monotonic();rows=[];stop=None
    for ident in IDS:
        bundle=bundles[ident]
        write_once(root/ident/'handoff.json',bundle)
        outcome=c01_host.consume(bundle,root/ident/'host',frozen['host_model'],key)
        rows.append({'case_id':ident,'source':'historical-routing/new-handoff','host':outcome})
        print(json.dumps({'case':ident,'host_status':outcome['status']}),flush=True)
        if outcome['status']!='complete':stop='host_failed';break
    chain=None;cached=False
    if stop is None:
        manifest=frozen['chain_manifest']
        write_once(root/'E01-admission.json',manifest)
        chain=c01_host.run(manifest,root/'E01',key)
        rows.append({'case_id':'E01','source':'fresh-route-and-host','host':chain['host'],'routing':chain['routing']['result']})
        print(json.dumps({'case':'E01','status':chain['status'],'route':chain['routing']['result']['route'],
                          'owner':chain['routing']['result']['owner']}),flush=True)
        if chain['status']!='complete':stop=chain['status']
        else:
            def forbidden(*args,**kwargs):raise AssertionError('cached reentry attempted inference')
            cached=c01_host.run(manifest,root/'E01',key,
                               provider=TypeSafeJevProvider(choice_rounding=True,transport=forbidden),
                               host_transport=forbidden)==chain
            require(cached,'cached reentry changed outcome')
    summary={'complete':len(rows)==5 and stop is None,'stop_reason':stop,'rows':rows,'unrun':5-len(rows),
             'wall_seconds':time.monotonic()-started,'new_host_attempts':len(list(root.glob('*/host/intent.json'))),
             'new_jev_attempts':len(list((root/'E01/routing/calls').glob('*/intent.json'))),
             'cached_reentry_verified':cached,'native_skill_load':'not_observed','qualification':False}
    write_once(root/'summary.json',summary)
    print(json.dumps({k:v for k,v in summary.items() if k!='rows'}),flush=True)
    return summary

if __name__=='__main__':
    path=DOCS/'freeze.json';require(not path.exists(),'freeze exists')
    frozen,_=prepare();path.write_text(json.dumps(frozen,indent=2)+'\n')
