"""Known-ended wire clarification for this exact eight-case batch, never an unknown unlock."""
from pathlib import Path
import subprocess
from . import runtime as rt
from experiments.typed_decision.contracts import digest, require
from experiments.typed_decision.relationship_runtime import _locked
from experiments.jev_direct.serial import SerialRequests

BATCH='d91af49c938602c289608fa61e3a0eb4b1fa4e0ddc44b6c7adef3cc26a2ec8ff'
NAME='read-contract-successor.json'
REPO=Path(__file__).resolve().parents[2]
RUNNER='docs/internal/research/typed-decision/grounded-judgment-v0/extended-exploratory-v1/run.py'


def verified(root):
    root=Path(root);x=rt.read(root/NAME)
    require(digest(rt.read(root/'batch.json'))==BATCH==x['batch_sha256'],'read_repair_exact_batch')
    require(digest((REPO/RUNNER).read_text())==x['runner_sha256'],'read_repair_runner_changed')
    require(x['kind']=='read_contract_sending_clarification' and x['retry_call_key'] is None,'read_repair_no_retry')
    require([p.name for p in root.glob('STOP*.json')]==['STOP.json'],'read_repair_no_new_stop')
    for path,h in x['preserved'].items():require(digest(rt.read(root/path))==h,'read_repair_history_changed')
    require(rt.read(root/'STOP.json')['reason']=='technical_pause_read_contract_omission','read_repair_pause_only')
    # All physical work must have a returned, bound terminal before this technical continuation.
    for n in x['prior_calls']:
        require(rt.read(root/'calls'/n/'terminal.json')['status']=='returned','read_repair_no_unknown')
        require((root/'serial'/n/'completion.json').is_file(),'read_repair_explicit_completion')
    return x


def register(root):
    root=Path(root)
    with _locked(root/'.execution.lock'), _locked(root/'.dispatch.lock'):
        require(not (root/NAME).exists(),'read_repair_already_registered')
        config=rt.read(root/'batch.json');require(digest(config)==BATCH,'read_repair_exact_batch')
        stop=rt.read(root/'STOP.json')
        require(stop['reason']=='technical_pause_read_contract_omission','read_repair_pause_only')
        require(len(list(root.glob('STOP*.json')))==1,'read_repair_no_other_stop')
        SerialRequests(root/'serial').validate()
        calls=sorted((root/'calls').iterdir());require(len(calls)==34,'read_repair_34_calls')
        for d in calls:
            require(rt.read(d/'terminal.json')['status']=='returned' and (d/'import.json').exists(),'read_repair_no_unknown_or_unimported')
            require(rt.read(d/'raw.json')['binding']==rt.read(d/'terminal.json')['binding'],'read_repair_terminal_binding')
            require((root/'serial'/d.name/'completion.json').is_file(),'read_repair_explicit_completion')
        for n in ('000011','000029'):
            raw=rt.read(root/'calls'/n/'envelope.json')['response']
            require(raw['kind']=='read' and bool(raw['text']),'read_repair_original_failure')
        source=dict(config['source_sha256'])
        changed=[p for p,h in source.items() if digest((REPO/p).read_text())!=h]
        require(set(changed)=={'experiments/grounded_judgment/runtime.py','experiments/grounded_judgment/dispatch.py',
                               'experiments/grounded_judgment/resume_000007.py'},'read_repair_minimal_sources')
        source={p:digest((REPO/p).read_text()) for p in source}
        source[str(Path(__file__).resolve().relative_to(REPO))]=digest(Path(__file__).read_text())
        preserved={str(p.relative_to(root)):digest(rt.read(p)) for folder in ('calls','serial','runs')
                   for p in (root/folder).rglob('*.json')}
        preserved['STOP.json']=digest(stop)
        x={'kind':'read_contract_sending_clarification','batch_sha256':BATCH,'retry_call_key':None,
           'source_sha256':source,'preserved':preserved,'prior_calls':[d.name for d in calls],
           'runner_sha256':digest((REPO/RUNNER).read_text()),
           'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
           'authority':'Owner-authorized normal interface implementation within the eight-case 176-call batch; no judgment contract change',
           'budgets_reset':False,'failed_paths_retry':False,'unknown_or_safety_exception':False,
           'note':'Stop file retained. Only its exact known-ended technical pause is resolved; any new stop blocks.'}
        rt.write(root/NAME,x)
        return verified(root)
