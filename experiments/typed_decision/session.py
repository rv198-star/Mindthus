"""Small immutable inference journal, not a Mission/task engine.

A batch is the cache unit. Completed batches are reused only with the same projected
input, questions, implementation, logical Decision Engine and serving configuration.
The resolved runtime model/provider is an observation, not configuration; the first
successful observation is locked for a trial so a serving alias cannot drift silently.
Unknown in-flight calls are never silently repeated.
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

from .contracts import (
    BatchResult,
    ContractError,
    DecisionResult,
    DecisionSpec,
    ResolvedRuntime,
    canonical,
    digest,
    number,
    project_context,
    provider_configuration,
    require,
)
from .providers import ProviderError


class RecoveryRequired(RuntimeError):
    """Original external call may have occurred; reconcile before any resubmission."""


def implementation_digest() -> str:
    root = Path(__file__).resolve().parent
    return digest({
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(root.glob('*.py'))
    })


def _sync_directory(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def write_once(path: Path, payload: dict) -> None:
    """Atomically publish an immutable, checked JSON record on a POSIX filesystem."""

    path.parent.mkdir(parents=True, exist_ok=True)
    wrapper = {
        'schema': 'mindthus.decision-record.v1',
        'payload': payload,
        'sha256': digest(payload),
    }
    fd, temp = tempfile.mkstemp(prefix='.record-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(canonical(wrapper) + b'\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temp, path)
        _sync_directory(path.parent)
    finally:
        os.unlink(temp)


def read_record(path: Path) -> dict:
    try:
        raw = json.loads(path.read_bytes())
        require(isinstance(raw, dict) and set(raw) == {'schema', 'payload', 'sha256'},
                'record shape')
        require(raw['schema'] == 'mindthus.decision-record.v1'
                and isinstance(raw['payload'], dict),
                'record version/payload')
        require(digest(raw['payload']) == raw['sha256'], 'record digest mismatch')
        return raw['payload']
    except (OSError, ValueError, TypeError):
        raise ContractError(f'invalid persisted record: {path.name}') from None


@dataclass(frozen=True)
class Limits:
    max_calls: int = 8
    max_seconds: float = 30
    max_request_bytes: int = 98304

    def validate(self) -> None:
        require(type(self.max_calls) is int and 0 < self.max_calls <= 100,
                'invalid call budget')
        require(type(self.max_seconds) in (float, int) and 0 < self.max_seconds <= 300,
                'invalid time budget')
        require(type(self.max_request_bytes) is int
                and 0 < self.max_request_bytes <= 262144,
                'invalid byte budget')


class Session:
    def __init__(self, root: Path, provider, *, scope: str, limits: Limits = Limits(),
                 live_admission: dict | None = None):
        self.root = Path(root)
        self.provider = provider
        self.scope = scope
        self.limits = limits
        limits.validate()
        require(isinstance(scope, str) and bool(scope.strip()),
                'explicit trial scope required')
        self.provider_config = provider_configuration(provider)
        self.impl = implementation_digest()
        self.live_admission = json.loads(canonical(live_admission)) if live_admission is not None else None
        live_admission = self.live_admission
        self.evidence_kind = 'live_model' if provider.is_live else 'offline_fixture'
        if provider.is_live:
            require(isinstance(live_admission, dict), 'live_campaign_not_preregistered')
            require(set(live_admission) == {'scope', 'implementation', 'provider_configuration',
                    'limits', 'request_allowlist', 'max_cost_usd', 'reserve_per_call_usd',
                    'authorization_ref', 'freeze_sha256'}, 'invalid live admission')
            require(live_admission['scope'] == scope and live_admission['implementation'] == self.impl
                    and live_admission['provider_configuration'] == self.provider_config
                    and live_admission['limits'] == asdict(limits), 'live identity/limits mismatch')
            allowlist = live_admission['request_allowlist']
            require(isinstance(allowlist, list) and 0 < len(allowlist) <= 1000
                    and all(isinstance(x, str) and len(x) == 64
                            and set(x) <= set('0123456789abcdef') for x in allowlist),
                    'invalid live request allowlist')
            require(number(live_admission['max_cost_usd'], .000001, 1)
                    and number(live_admission['reserve_per_call_usd'], .000001, 1),
                    'invalid live cost ceiling')
            require(isinstance(live_admission['authorization_ref'], str)
                    and bool(live_admission['authorization_ref'].strip())
                    and isinstance(live_admission['freeze_sha256'], str)
                    and len(live_admission['freeze_sha256']) == 64
                    and set(live_admission['freeze_sha256']) <= set('0123456789abcdef'),
                    'missing live authority/freeze')
        else:
            require(live_admission is None, 'live admission requires a live provider')
        self.calls_made = 0
        self.calls_reused = 0
        self.records = []
        self._lock = None

    def __enter__(self):
        try:
            import fcntl
        except ImportError:
            raise ContractError(
                'journal requires a POSIX host; other hosts unqualified'
            ) from None
        self.root.mkdir(parents=True, exist_ok=True)
        self._lock = (self.root / '.lock').open('a+b')
        try:
            fcntl.flock(self._lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self._lock.close()
            self._lock = None
            raise RecoveryRequired('another process owns this trial') from None
        try:
            policy = {
                'scope': self.scope,
                'limits': asdict(self.limits),
                'provider_configuration': self.provider_config,
                'implementation': self.impl,
            }
            if self.live_admission is not None:
                policy['live_admission'] = self.live_admission
            path = self.root / 'policy.json'
            if path.exists():
                require(read_record(path) == policy,
                        'trial policy/implementation changed: use a new root')
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

    def _bind_runtime(self, runtime: ResolvedRuntime) -> None:
        """Freeze the actual runtime snapshot used by successful calls in this trial."""

        self.provider.validate_runtime(runtime)
        payload = runtime.to_dict()
        path = self.root / 'resolved-runtime.json'
        if path.exists():
            require(read_record(path) == payload,
                    'resolved runtime changed: use a new trial root')
        else:
            write_once(path, payload)

    def evaluate(self, specs: list[DecisionSpec], context: dict) -> dict[str, DecisionResult]:
        require(self._lock is not None, 'session must be entered')
        try:
            view = project_context(specs, context)
        except ContractError as exc:
            if str(exc).startswith('missing_context:'):
                return {
                    spec.id: DecisionResult(
                        'missing_context',
                        reason=str(exc)[:256],
                    ) for spec in specs
                }
            raise
        if any(spec.kind not in self.provider.capabilities for spec in specs):
            return {
                spec.id: DecisionResult(
                    'unsupported',
                    reason='provider_capability',
                ) for spec in specs
            }
        identity = {
            'questions': [spec.to_dict() for spec in specs],
            'context_sha256': digest(view),
            'provider_configuration': self.provider_config,
            'implementation': self.impl,
            'scope': self.scope,
        }
        if self.live_admission is not None:
            request_key = digest({'questions': identity['questions'],
                                  'context_sha256': identity['context_sha256']})
            require(request_key in self.live_admission['request_allowlist'],
                    'request outside frozen live egress')
        key = digest(identity)
        directory = self.root / 'calls' / key
        intent = directory / 'intent.json'
        outcome = directory / 'outcome.json'

        if outcome.exists():
            require(
                intent.exists() and read_record(intent)['identity'] == identity,
                'missing/mismatched intent',
            )
            raw = self._read_outcome(outcome)
            require(set(raw['results']) == {spec.id for spec in specs},
                    'persisted answer ids mismatch')
            require(raw.get('call_key') == key, 'outcome identity mismatch')
            runtime = (
                ResolvedRuntime.from_dict(raw['resolved_runtime'])
                if raw['resolved_runtime'] is not None
                else None
            )
            if runtime is not None:
                self._bind_runtime(runtime)
            batch = BatchResult(
                {
                    spec.id: DecisionResult.from_dict(
                        raw['results'][spec.id],
                        spec,
                    ) for spec in specs
                },
                runtime,
                raw['usage'],
            )
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
                raise RecoveryRequired(
                    'trial has an unresolved call:' + prior.parent.name
                )
            spent += self._read_outcome(prior_outcome)['elapsed_seconds']

        require(len(intents) < self.limits.max_calls, 'call budget exhausted')
        if self.live_admission is not None:
            # Reserve every attempted call, including unknown or failed billing.
            require((len(intents) + 1) * self.live_admission['reserve_per_call_usd']
                    <= self.live_admission['max_cost_usd'], 'cost reservation exhausted')
            for prior in intents:
                usage = self._read_outcome(prior.parent / 'outcome.json')['usage']
                require(usage['cost_usd'] is None or usage['cost_usd']
                        <= self.live_admission['reserve_per_call_usd'], 'observed cost exceeds reserve')
        remaining = self.limits.max_seconds - max(
            spent,
            time.monotonic() - self.started,
        )
        require(remaining > 0, 'time budget exhausted')
        request_bytes = len(canonical({
            'state': view,
            'questions': identity['questions'],
        }))
        require(request_bytes <= self.limits.max_request_bytes,
                'request byte budget exhausted')

        write_once(intent, {
            'identity': identity,
            'call_key': key,
            'scope': self.scope,
            'projected_request_bytes': request_bytes,
            'created_at': datetime.now(timezone.utc).isoformat(),
        })
        begin = time.monotonic()
        self.calls_made += 1
        try:
            batch = self.provider.evaluate(specs, view, remaining)
            require(isinstance(batch, BatchResult), 'invalid provider batch type')
            batch.validate(specs)
            if batch.resolved_runtime is not None:
                self._bind_runtime(batch.resolved_runtime)
            if time.monotonic() - begin > remaining:
                raise ProviderError('deadline_exceeded')
        except (ProviderError, ContractError) as exc:
            # Persist a bounded error type, never arbitrary remote/provider text.
            batch = BatchResult({
                spec.id: DecisionResult(
                    'provider_error',
                    reason=type(exc).__name__,
                ) for spec in specs
            })

        record = {
            'call_key': key,
            'results': {
                name: asdict(value) for name, value in batch.results.items()
            },
            'resolved_runtime': (
                batch.resolved_runtime.to_dict()
                if batch.resolved_runtime is not None
                else None
            ),
            'usage': batch.usage,
            'elapsed_seconds': time.monotonic() - begin,
            'projected_request_bytes': request_bytes,
            'evidence_kind': self.evidence_kind,
        }
        write_once(outcome, record)
        self.records.append({'call_key': key, 'reused': False})
        return batch.results

    def _read_outcome(self, path: Path) -> dict:
        raw = read_record(path)
        require(
            set(raw) == {
                'call_key',
                'results',
                'resolved_runtime',
                'usage',
                'elapsed_seconds',
                'projected_request_bytes',
                'evidence_kind',
            },
            'persisted outcome shape',
        )
        require(raw['call_key'] == path.parent.name,
                'persisted call directory mismatch')
        if raw['resolved_runtime'] is not None:
            runtime = ResolvedRuntime.from_dict(raw['resolved_runtime'])
            self.provider.validate_runtime(runtime)
        require(raw['evidence_kind'] == self.evidence_kind,
                'persisted evidence kind changed')
        require(number(raw['elapsed_seconds'], 0, 86400),
                'invalid elapsed time')
        require(type(raw['projected_request_bytes']) is int
                and raw['projected_request_bytes'] >= 0,
                'invalid byte count')
        require(isinstance(raw['results'], dict),
                'invalid persisted results')
        require(
            isinstance(raw['usage'], dict)
            and set(raw['usage']) == {
                'input_tokens',
                'output_tokens',
                'cost_usd',
            },
            'invalid persisted usage',
        )
        for key, value in raw['usage'].items():
            require(
                value is None or (
                    number(value, 0, 1e15)
                    and (key == 'cost_usd' or type(value) is int)
                ),
                'invalid persisted usage value',
            )
        return raw

    def finish(self, graph: dict, context: dict, result: dict) -> dict:
        """Persist observable local result; neither task completion nor quality gate."""

        require(self._lock is not None, 'session must be entered')
        identity = {
            'graph': graph,
            'input_sha256': digest(context),
            'scope': self.scope,
            'implementation': self.impl,
            'provider_configuration': self.provider_config,
        }
        run_id = digest(identity)
        path = self.root / 'runs' / (run_id + '.json')
        material = {
            'identity': identity,
            'run_id': run_id,
            'result': result,
            'call_keys': [record['call_key'] for record in self.records],
        }
        if path.exists():
            old = read_record(path)
            require(old['identity'] == identity and old['result'] == result,
                    'same run identity produced a different result')
        else:
            write_once(path, material)

        outcomes = [
            self._read_outcome(p)
            for p in sorted((self.root / 'calls').glob('*/outcome.json'))
        ]
        totals = {}
        for field in ('input_tokens', 'output_tokens', 'cost_usd'):
            values = [record['usage'][field] for record in outcomes]
            totals[field] = (
                sum(values)
                if all(value is not None for value in values)
                else None
            )
        runtimes = []
        seen = set()
        for record in outcomes:
            runtime = record['resolved_runtime']
            if runtime is not None:
                key = digest(runtime)
                if key not in seen:
                    runtimes.append(runtime)
                    seen.add(key)

        return {
            **material,
            'source_ref': str(path),
            'invocation': {
                'new_calls': self.calls_made,
                'reused_calls': self.calls_reused,
            },
            'trial_usage': totals,
            'trial_inference_seconds': sum(
                record['elapsed_seconds'] for record in outcomes
            ),
            'resolved_runtimes': runtimes,
            'cost_coverage': 'partial',
            'semantic_outcome': 'not_evaluated',
            'end_to_end_value': 'unknown',
            'evidence_kind': self.evidence_kind,
        }
