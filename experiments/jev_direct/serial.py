"""Batch-bound serial dispatch; wall timestamps are not cooldown clocks.

Two independently located record sets plus business-intent reconciliation detect
incomplete recovery. Unknown requests never become a fresh batch. This is local
crash/evidence integrity, not protection against an adversary rewriting all files.
"""
from pathlib import Path
import math
import time
from experiments.typed_decision.relationship_runtime import _locked, save
from experiments.typed_decision.session import read_record, RecoveryRequired
from experiments.typed_decision.contracts import require, digest


class SerialRequests:
    gap = 60

    def __init__(self, root, *, clock=time.time, monotonic=time.monotonic, sleep=time.sleep):
        self.root = Path(root).resolve()
        self.clock, self.monotonic, self.sleep = clock, monotonic, sleep
        self.batch = self.root.parent if (self.root.parent/'freeze.json').exists() else None
        self.anchors = self.batch/'serial-bindings' if self.batch else self.root/'bindings'
        self._last_completion = None
        self._last_end = None

    def _number(self, x):
        return type(x) in (int,float) and math.isfinite(x)

    def _accepted_unknown(self,directory,intent):
        from .b1_compensation import accepted
        return accepted(self.batch,directory,intent)

    def _validate(self):
        directories = sorted(p for p in self.root.glob('[0-9]*') if p.is_dir())
        anchors = sorted(p for p in self.anchors.glob('[0-9]*') if p.is_dir())
        require([p.name for p in directories]==[f'{i:06d}' for i in range(len(directories))], 'serial_sequence_gap')
        require([p.name for p in anchors]==[p.name for p in directories], 'serial_binding_missing')
        labels={};last=None
        for directory,anchor in zip(directories,anchors):
            intent=read_record(directory/'intent.json')
            require(read_record(anchor/'intent.json')=={'intent_sha256':digest(intent)},'serial_intent_binding_changed')
            require(isinstance(intent['label'],str) and intent['label'] not in labels,'serial_duplicate_label')
            require(self._number(intent['started_at_epoch']),'serial_start_time_invalid')
            prior_unknown=last is not None and last['status']=='risk_accepted_remote_unknown'
            require(intent['previous_completion_sha256']==(digest(last) if last and not prior_unknown else None),'serial_chain_changed')
            require(intent.get('previous_disposition_sha256')==(digest(last) if prior_unknown else None),'serial_disposition_chain_changed')
            gap=intent['actual_gap_seconds']
            require((last is None and gap is None) or (last is not None and self._number(gap) and gap>=self.gap),'serial_gap_invalid')
            outcome=directory/'completion.json'
            failure=directory/'failure.json'
            require(not (outcome.exists() and failure.exists()),'serial_conflicting_terminal')
            disposition=directory/'accepted-unknown.json'
            if disposition.exists():
                require(not outcome.exists() and not failure.exists(),'serial_conflicting_disposition')
                end=self._accepted_unknown(directory,intent)
            elif failure.exists():
                from .host_boundary import validate_reconciliation
                end=read_record(failure);host=Path(end['host_directory'])
                require(self.batch is not None and host.is_relative_to(self.batch/'runs')
                        and intent['label']=='host:'+str(host),'serial_failure_identity')
                receipt=validate_reconciliation(host)
                require(read_record(anchor/'failure.json')=={'failure_sha256':digest(end)},'serial_failure_binding_changed')
                require(end['status']=='confirmed_request_failure' and end['intent_sha256']==digest(intent)
                        and end['reconciliation_sha256']==digest(read_record(host/'reconciliation.json'))
                        and end['ended_at_epoch']==receipt['ended_at_epoch']
                        and receipt['started_at_epoch']>=intent['started_at_epoch']
                        and end['request_elapsed_seconds'] is None,'serial_failure_receipt_changed')
            else:
                if not outcome.exists():raise RecoveryRequired('serial_unknown_request_no_resubmit')
                end=read_record(outcome)
                require(read_record(anchor/'completion.json')=={'completion_sha256':digest(end)},'serial_completion_binding_changed')
                require(end['intent_sha256']==digest(intent) and end['status']=='returned','serial_completion_identity')
                require(self._number(end['request_elapsed_seconds']) and end['request_elapsed_seconds']>=0,'serial_end_time_invalid')
            require(self._number(end['local_disposition_at_epoch'] if end['status']=='risk_accepted_remote_unknown' else end['ended_at_epoch']),'serial_end_time_invalid')
            labels[intent['label']]=end;last=end
        if self.batch:
            # Use actual host/provider intents, including other scenarios/arms and reviews.
            locations=[(self.batch/'runs','*/*/host/*'),
                       (self.batch/'reviews','**'),
                       (self.batch/'runs','*/*/route/level-*/journal/calls/*'),
                       (self.batch/'runs/B1/direct','route-compensation/level-*/journal/calls/*')]
            paths=set()
            for root,pattern in locations:
                # Discover from BOTH directions. Request/prompt/schema-only
                # preparation is not evidence that anything was sent.
                for name in ('intent.json','outcome.json','reply.json','provider-receipt.json','reconciliation.json','schema-failure-receipt.json'):
                    for evidence in root.glob(pattern+'/'+name):
                        intent_path=evidence.with_name('intent.json')
                        require(intent_path.is_file(),'serial_orphan_response_evidence')
                        paths.add(intent_path)
            observed=set()
            for path in paths:
                read_record(path)
                label=('jev:'+str(path.parents[3]) if path.parent.parent.name=='calls' else 'host:'+str(path.parent))
                require(label in labels,'serial_business_binding_missing')
                if not path.with_name('outcome.json').exists():
                    if labels[label]['status']!='confirmed_request_failure':raise RecoveryRequired('serial_business_outcome_unknown')
                    from .host_boundary import validate_reconciliation
                    validate_reconciliation(path.parent)
                else:read_record(path.with_name('outcome.json'))
                observed.add(label)
            bound={label for label in labels if label.startswith(('host:','jev:'))}
            require(bound==observed,'serial_business_evidence_missing')
        return directories,last,labels

    def validate(self):
        with _locked(self.root/'.lock'):
            return self._validate()

    def call(self, label, invoke):
        with _locked(self.root/'.lock'):
            if self.batch:
                from .transport_profile import guard
                guard(self.batch)
                from .b1_compensation import guard_label
                guard_label(self.batch,label)
            directories,previous,labels=self._validate()
            require(label not in labels,'serial_request_already_completed')
            began_wait=self.monotonic()
            continuous=previous is not None and digest(previous)==self._last_completion
            end_mono=self._last_end if continuous else began_wait
            waited=0.0
            if previous is not None:
                while self.monotonic()-end_mono < self.gap:
                    wait_start=self.monotonic()
                    self.sleep(min(60,self.gap-(self.monotonic()-end_mono)))
                    waited+=self.monotonic()-wait_start
            start_mono=self.monotonic();start=self.clock()
            gap=None if previous is None else start_mono-end_mono
            accepted_unknown=previous is not None and previous['status']=='risk_accepted_remote_unknown'
            reference_epoch=None if previous is None else previous['local_disposition_at_epoch'] if accepted_unknown else previous['ended_at_epoch']
            intent={'label':label,'started_at_epoch':start,
                    'previous_completion_sha256':digest(previous) if previous and not accepted_unknown else None,
                    'previous_end_epoch':reference_epoch if not accepted_unknown else None,
                    'actual_gap_seconds':gap,
                    'active_wait_seconds':waited,
                    'gap_basis':'first_call' if previous is None else 'monotonic' if continuous else 'restart_conservative_lower_bound',
                    'wall_gap_seconds':None if previous is None else start-reference_epoch}
            if accepted_unknown:
                intent.update(previous_disposition_sha256=digest(previous),previous_disposition_epoch=reference_epoch,gap_basis='monotonic_wait_after_risk_acceptance_not_remote_completion')
            directory=self.root/f'{len(directories):06d}';anchor=self.anchors/directory.name
            save(directory/'intent.json',intent)
            save(anchor/'intent.json',{'intent_sha256':digest(intent)})
            result=invoke()
            end=self.clock();end_mono=self.monotonic()
            require(end_mono>=start_mono,'serial_monotonic_reversed')
            completion={'ended_at_epoch':end,'request_elapsed_seconds':end_mono-start_mono,
                        'status':'returned','intent_sha256':digest(intent)}
            save(directory/'completion.json',completion)
            save(anchor/'completion.json',{'completion_sha256':digest(completion)})
            self._last_completion=digest(completion);self._last_end=end_mono
            return result
