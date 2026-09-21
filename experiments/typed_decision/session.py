"""Small immutable inference journal, not a Mission/task engine.

A batch is the cache unit: a chat model can couple answers within a batch. Completed
batches are reused only with the same projected input, questions, implementation,
provider and trial policy. Unknown in-flight calls are never silently repeated.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time

from .contracts import (BatchResult, ContractError, DecisionResult, DecisionSpec,
                        canonical, digest, number, project_context, require)
from .providers import ProviderError


class RecoveryRequired(RuntimeError):
    """Original external call may have occurred; reconcile before any resubmission."""


def implementation_digest() -> str:
    root = Path(__file__).resolve().parent
    return digest({p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.glob('*.py'))})


def _sync_directory(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def write_once(path: Path, payload: dict) -> None:
    """Atomically publish an immutable, checked JSON record on a POSIX filesystem."""
    path.parent.mkdir(parents=True, exist_ok=True)
    wrapper = {'schema': 'mindthus.decision-record.v1', 'payload': payload, 'sha256': digest(payload)}
    fd, temp = tempfile.mkstemp(prefix='.record-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(canonical(wrapper) + b'\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temp, path)  # atomic no-clobber; a partial final record is never visible
        _sync_directory(path.parent)
    finally:
        os.unlink(temp)


def read_record(path: Path) -> dict:
    try:
        raw = json.loads(path.read_bytes())
        require(isinstance(raw, dict) and set(raw) == {'schema', 'payload', 'sha256'}, 'record shape')
        require(raw['schema'] == 'mindthus.decision-record.v1' and isinstance(raw['payload'], dict),
                'record version/payload')
        require(digest(raw['payload']) == raw['sha256'], 'record digest mismatch')
        return raw['payload']
    except (OSError, ValueError, TypeError) as exc:
        raise ContractError(f'invalid persisted record: {path.name}') from None


@dataclass(frozen=True)
class Limits:
    max_calls: int = 8
    max_seconds: float = 30
    max_request_bytes: int = 98304

    def validate(self) -> None:
        require(type(self.max_calls) is int and 0 < self.max_calls <= 100, 'invalid call budget')
        require(type(self.max_seconds) in (float, int) and 0 < self.max_seconds <= 300,
                'invalid time budget')
        require(type(self.max_request_bytes) is int and 0 < self.max_request_bytes <= 262144,
                'invalid byte budget')


class Session:
    def __init__(self, root: Path, provider, *, scope: str, limits: Limits = Limits()):
        self.root, self.provider, self.scope, self.limits = Path(root), provider, scope, limits
        limits.validate()
        require(isinstance(scope, str) and bool(scope.strip()), 'explicit trial scope required')
        # Offline delivery is intentionally usable without authorizing a paid campaign.
        # The native adapters are implemented/testable; a future preregistered host
        # carrier must own live budgets, egress approval and qualified consumption.
        require(not provider.is_live, 'live_campaign_not_preregistered: use an authorized host carrier')
        self.impl = implementation_digest()
        self.calls_made = 0
        self.calls_reused = 0
        self.records = []
        self._lock = None

    def __enter__(self):
        try:
            import fcntl
        except ImportError:
            raise ContractError('journal requires a POSIX host; other hosts unqualified') from None
        self.root.mkdir(parents=True, exist_ok=True)
        self._lock = (self.root / '.lock').open('a+b')
        try:
            fcntl.flock(self._lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self._lock.close()
            self._lock = None
            raise RecoveryRequired('another process owns this trial') from None
        try:
            policy = {'scope': self.scope, 'limits': asdict(self.limits),
                      'provider': self.provider.identity, 'implementation': self.impl}
            path = self.root / 'policy.json'
            if path.exists():
                require(read_record(path) == policy, 'trial policy/implementation changed: use a new root')
            else:
                write_once(path, policy)
            self.started = time.monotonic()
            return self
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def __exit__(self, *_):
        if self._lock:
            self._lock.close()
            self._lock = None

    def evaluate(self, specs: list[DecisionSpec], context: dict) -> dict[str, DecisionResult]:
        require(self._lock is not None, 'session must be entered')
        try:
            view = project_context(specs, context)
        except ContractError as exc:
            if str(exc).startswith('missing_context:'):
                return {s.id: DecisionResult('missing_context', reason=str(exc)[:256]) for s in specs}
            raise
        if any(s.kind not in self.provider.capabilities for s in specs):
            return {s.id: DecisionResult('unsupported', reason='provider_capability') for s in specs}
        identity = {'questions': [s.to_dict() for s in specs], 'context_sha256': digest(view),
                    'provider': self.provider.identity, 'implementation': self.impl, 'scope': self.scope}
        key = digest(identity)
        directory = self.root / 'calls' / key
        intent = directory / 'intent.json'
        outcome = directory / 'outcome.json'
        if outcome.exists():
            require(intent.exists() and read_record(intent)['identity'] == identity, 'missing/mismatched intent')
            raw = self._read_outcome(outcome)
            require(set(raw['results']) == {s.id for s in specs}, 'persisted answer ids mismatch')
            require(raw.get('call_key') == key, 'outcome identity mismatch')
            batch = BatchResult({s.id: DecisionResult.from_dict(raw['results'][s.id], s) for s in specs},
                                raw['model'], raw['usage'])
            batch.validate(specs)
            self.calls_reused += 1
            self.records.append({'call_key': key, 'reused': True})
            return batch.results
        if intent.exists():
            raise RecoveryRequired('unresolved prior call:' + key)
        intents = sorted((self.root / 'calls').glob('*/intent.json'))
        spent = 0.0
        for prior in intents:
            data = read_record(prior)
            require(data.get('scope') == self.scope, 'foreign trial intent')
            prior_outcome = prior.parent / 'outcome.json'
            if not prior_outcome.exists():
                raise RecoveryRequired('trial has an unresolved call:' + prior.parent.name)
            spent += self._read_outcome(prior_outcome)['elapsed_seconds']
        require(len(intents) < self.limits.max_calls, 'call budget exhausted')
        remaining = self.limits.max_seconds - max(spent, time.monotonic() - self.started)
        require(remaining > 0, 'time budget exhausted')
        request_bytes = len(canonical({'state': view, 'questions': identity['questions']}))
        require(request_bytes <= self.limits.max_request_bytes, 'request byte budget exhausted')
        write_once(intent, {'identity': identity, 'call_key': key, 'scope': self.scope,
                            'projected_request_bytes': request_bytes,
                            'created_at': datetime.now(timezone.utc).isoformat()})
        begin = time.monotonic()
        self.calls_made += 1
        try:
            batch = self.provider.evaluate(specs, view, remaining)
            require(isinstance(batch, BatchResult), 'invalid provider batch type')
            batch.validate(specs)
            require(batch.model == self.provider.identity['model'], 'response model identity changed')
            if time.monotonic() - begin > remaining:
                raise ProviderError('deadline_exceeded')
        except (ProviderError, ContractError) as exc:
            # Persist a bounded error *type*, not arbitrary remote/provider text.
            batch = BatchResult({s.id: DecisionResult('provider_error', reason=type(exc).__name__)
                                 for s in specs}, self.provider.identity['model'])
        record = {'call_key': key, 'results': {k: asdict(v) for k, v in batch.results.items()},
                  'model': batch.model, 'usage': batch.usage,
                  'elapsed_seconds': time.monotonic() - begin, 'projected_request_bytes': request_bytes,
                  'evidence_kind': 'offline_fixture'}
        write_once(outcome, record)
        self.records.append({'call_key': key, 'reused': False})
        return batch.results

    def _read_outcome(self, path: Path) -> dict:
        raw = read_record(path)
        require(set(raw) == {'call_key', 'results', 'model', 'usage', 'elapsed_seconds',
                             'projected_request_bytes', 'evidence_kind'}, 'persisted outcome shape')
        require(raw['call_key'] == path.parent.name, 'persisted call directory mismatch')
        require(raw['model'] == self.provider.identity['model'], 'persisted model changed')
        require(raw['evidence_kind'] == 'offline_fixture', 'persisted evidence kind changed')
        require(number(raw['elapsed_seconds'], 0, 86400), 'invalid elapsed time')
        require(type(raw['projected_request_bytes']) is int and raw['projected_request_bytes'] >= 0, 'invalid byte count')
        require(isinstance(raw['results'], dict), 'invalid persisted results')
        require(isinstance(raw['usage'], dict) and set(raw['usage']) ==
                {'input_tokens', 'output_tokens', 'cost_usd'}, 'invalid persisted usage')
        for key, value in raw['usage'].items():
            require(value is None or (number(value, 0, 1e15) and
                    (key == 'cost_usd' or type(value) is int)), 'invalid persisted usage value')
        return raw

    def finish(self, graph: dict, context: dict, result: dict) -> dict:
        """Persist observable local result; neither a task completion nor quality gate."""
        require(self._lock is not None, 'session must be entered')
        identity = {'graph': graph, 'input_sha256': digest(context), 'scope': self.scope,
                    'implementation': self.impl, 'provider': self.provider.identity}
        run_id = digest(identity)
        path = self.root / 'runs' / (run_id + '.json')
        material = {'identity': identity, 'run_id': run_id, 'result': result,
                    'call_keys': [r['call_key'] for r in self.records]}
        if path.exists():
            old = read_record(path)
            require(old['identity'] == identity and old['result'] == result,
                    'same run identity produced a different result')
        else:
            write_once(path, material)
        outcomes = [self._read_outcome(p) for p in sorted((self.root / 'calls').glob('*/outcome.json'))]
        totals = {}
        for field in ('input_tokens', 'output_tokens', 'cost_usd'):
            values = [r['usage'][field] for r in outcomes]
            totals[field] = sum(values) if all(v is not None for v in values) else None
        return {**material, 'source_ref': str(path), 'invocation': {
            'new_calls': self.calls_made, 'reused_calls': self.calls_reused},
            'trial_usage': totals, 'trial_inference_seconds': sum(r['elapsed_seconds'] for r in outcomes),
            'cost_coverage': 'partial', 'semantic_outcome': 'not_evaluated',
            'end_to_end_value': 'unknown', 'evidence_kind': 'offline_fixture'}
