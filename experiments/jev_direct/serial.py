"""One batch-wide request lock and an immutable end-to-start interval ledger.

An exception or process interruption leaves an unknown intent and blocks all later
requests. A local timeout does not establish remote completion. No retry/recovery
override is provided here. Injected clocks are solely for offline tests.
"""
from pathlib import Path
import time
from experiments.typed_decision.relationship_runtime import _locked, save
from experiments.typed_decision.session import read_record, RecoveryRequired
from experiments.typed_decision.contracts import require


class SerialRequests:
    gap = 60

    def __init__(self, root, *, clock=time.time, sleep=time.sleep):
        self.root = Path(root)
        self.clock, self.sleep = clock, sleep

    def call(self, label, invoke):
        with _locked(self.root/'.lock'):
            intents = sorted(self.root.glob('*/intent.json'))
            previous_end = None
            for intent in intents:
                outcome = intent.with_name('completion.json')
                if not outcome.exists():
                    raise RecoveryRequired('serial_unknown_request_no_resubmit')
                previous_end = read_record(outcome)['ended_at_epoch']
            while previous_end is not None and self.clock()-previous_end < self.gap:
                self.sleep(min(60, self.gap-(self.clock()-previous_end)))
            start = self.clock()
            directory = self.root/f'{len(intents):06d}'
            save(directory/'intent.json', {'label':label,'started_at_epoch':start,
                 'previous_end_epoch':previous_end,
                 'actual_gap_seconds':None if previous_end is None else start-previous_end})
            result = invoke()
            end = self.clock()
            require(end>=start,'serial_clock_reversed')
            save(directory/'completion.json', {'ended_at_epoch':end,
                 'request_elapsed_seconds':end-start,'status':'returned'})
            return result
