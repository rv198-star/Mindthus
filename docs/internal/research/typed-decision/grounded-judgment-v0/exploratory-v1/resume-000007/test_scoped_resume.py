import tempfile,shutil
from pathlib import Path
from unittest.mock import patch
from experiments.grounded_judgment import resume_000007 as r,runtime as rt
from experiments.typed_decision.session import RecoveryRequired
from experiments.typed_decision.contracts import ContractError
from experiments.grounded_judgment.dispatch_demo import Clock
with tempfile.TemporaryDirectory() as tmp:
 root=Path(tmp)/'batch';shutil.copytree('/Users/william/.codex/tmp/gj-exploratory-v1-run',root)
 with patch.object(r,'load_official_credential',return_value={'loaded':True,'simulation':True}):r.register(root)
 s=rt.state(root/'runs/skills-validator-B')
 assert s['call_count']==2 and s['host_logical_calls']==2 and s['atoms'] and s['composition'] and s['pending'] is None
 assert rt.read(root/'calls/000007/terminal.json')['status']=='unknown' and not (root/'serial/000007/completion.json').exists()
 print('PASS: exact disposition preserves unknown, atoms/composition and 2/7 debit')
 clock=Clock();scheduler=r.NamedSerial(root/'serial',clock=clock.now,monotonic=clock.now,sleep=clock.sleep)
 def unknown():raise RecoveryRequired('new unknown')
 try:scheduler.call('skills-text-C:0',unknown)
 except RecoveryRequired:pass
 assert clock.now()>=60
 try:scheduler.validate()
 except RecoveryRequired:print('PASS: >=60s simulated cooldown; another unknown cannot inherit exception')
 else:raise AssertionError()
 rt.write(root/'STOP-new.json',{'status':'unknown'})
 try:r.guard(root)
 except ContractError:print('PASS: new STOP blocks; no generic ignore-unknown')
 else:raise AssertionError()
