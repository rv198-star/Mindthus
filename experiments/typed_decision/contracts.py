"""Provider-neutral, shape-only contracts for the opt-in pilots (#209)."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
import math
import re
from typing import Any, Protocol

STATUSES = frozenset({'ok', 'abstain', 'missing_context', 'unsupported', 'provider_error'})
KINDS = frozenset({'select', 'assess_proposition', 'rate'})
ID = re.compile(r'^[a-zA-Z][a-zA-Z0-9_.-]{0,95}$')
OPTION = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,95}$')


class ContractError(ValueError):
    """Malformed or unsupported contract, not a semantic judgment."""


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def number(value: Any, low: float, high: float) -> bool:
    return type(value) in (float, int) and math.isfinite(value) and low <= value <= high


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


@dataclass(frozen=True)
class DecisionSpec:
    id: str
    question: str
    criteria: Any
    required_context: tuple[str, ...]
    kind: str = 'select'
    version: str = '1'
    policy_ref: str = 'experimental-advisory-v1'
    fallback_ref: str = 'original-owner'

    def validate(self) -> None:
        require(isinstance(self.id, str) and bool(ID.fullmatch(self.id)), 'invalid decision id')
        require(isinstance(self.kind, str) and self.kind in KINDS, 'unsupported result type')
        for value in (self.question, self.version, self.policy_ref, self.fallback_ref):
            require(isinstance(value, str) and bool(value.strip()), 'empty decision contract')
        require(isinstance(self.required_context, (tuple, list)) and bool(self.required_context),
                'required context must be an explicit sequence')
        require(all(isinstance(k, str) and ID.fullmatch(k) for k in self.required_context),
                'invalid context keys')
        require(len(set(self.required_context)) == len(self.required_context), 'duplicate context key')
        if self.kind == 'select':
            require(isinstance(self.criteria, dict) and 2 <= len(self.criteria) <= 255,
                    'select requires 2..255 described options')
            require(all(isinstance(k, str) and OPTION.fullmatch(k) and isinstance(v, str) and v.strip()
                        for k, v in self.criteria.items()), 'invalid option/rubric')
        elif self.kind == 'assess_proposition':
            require(isinstance(self.criteria, dict) and set(self.criteria) == {'true', 'false'},
                    'proposition requires positive and negative semantics')
            require(all(isinstance(v, str) and v.strip() for v in self.criteria.values()),
                    'empty proposition rubric')
        else:
            require(isinstance(self.criteria, list) and 2 <= len(self.criteria) <= 10,
                    'rate requires 2..10 ordered levels')
            require(all(isinstance(v, str) and v.strip() for v in self.criteria), 'empty level')
        require(len(canonical(asdict(self))) <= 32768, 'decision contract too large')

    def to_dict(self) -> dict:
        self.validate()
        return json.loads(canonical(asdict(self)))


@dataclass(frozen=True)
class DecisionResult:
    status: str
    value: Any = None
    uncertainty: dict | None = None
    reason: str = ''

    def validate(self, spec: DecisionSpec) -> None:
        require(isinstance(self.status, str) and self.status in STATUSES, 'invalid result status')
        require(isinstance(self.reason, str) and len(self.reason) <= 256, 'invalid reason')
        if self.status != 'ok':
            require(self.value is None, 'non-ok result carries a decision')
        elif spec.kind == 'select':
            require(isinstance(self.value, str) and self.value in spec.criteria, 'out-of-contract choice')
        elif spec.kind == 'assess_proposition':
            require(number(self.value, 0, 1), 'invalid proposition probability')
        else:
            require(number(self.value, 0, len(spec.criteria) - 1), 'invalid weighted rating')
        if self.uncertainty is not None:
            require(isinstance(self.uncertainty, dict), 'invalid uncertainty')
            require(self.uncertainty.get('source') == 'provider_distribution', 'unknown uncertainty source')
            require(set(self.uncertainty) <= {'source', 'confidence', 'probabilities'},
                    'unknown uncertainty field')
            if 'confidence' in self.uncertainty:
                require(number(self.uncertainty['confidence'], 0, 1), 'invalid confidence')
            if 'probabilities' in self.uncertainty:
                probs = self.uncertainty['probabilities']
                expected = set(spec.criteria) if spec.kind == 'select' else {
                    str(i) for i in range(len(spec.criteria))}
                require(spec.kind != 'assess_proposition' and isinstance(probs, dict)
                        and set(probs) == expected, 'invalid distribution support')
                require(all(number(v, 0, 1) for v in probs.values()), 'invalid probability')
                require(abs(sum(probs.values()) - 1) <= 1e-6, 'distribution not normalized')
                if self.status == 'ok' and spec.kind == 'select':
                    require(probs[self.value] >= max(probs.values()) - 1e-9, 'choice is not an argmax')
                if self.status == 'ok' and spec.kind == 'rate':
                    require(abs(sum(int(k) * v for k, v in probs.items()) - self.value) <= 1e-6,
                            'weighted rating/distribution mismatch')

    @classmethod
    def from_dict(cls, raw: dict, spec: DecisionSpec) -> 'DecisionResult':
        require(isinstance(raw, dict) and set(raw) == {'status', 'value', 'uncertainty', 'reason'},
                'result shape mismatch')
        result = cls(**raw)
        result.validate(spec)
        return result


@dataclass
class BatchResult:
    results: dict[str, DecisionResult]
    model: str
    usage: dict = field(default_factory=lambda: {
        'input_tokens': None, 'output_tokens': None, 'cost_usd': None})

    def validate(self, specs: list[DecisionSpec]) -> None:
        require(isinstance(self.results, dict) and set(self.results) == {s.id for s in specs},
                'answer ids differ from question ids')
        require(isinstance(self.model, str) and bool(self.model), 'missing actual model')
        require(isinstance(self.usage, dict) and set(self.usage) ==
                {'input_tokens', 'output_tokens', 'cost_usd'}, 'invalid usage keys')
        for k, v in self.usage.items():
            require(v is None or (number(v, 0, 1e15) and (k == 'cost_usd' or type(v) is int)),
                    'invalid usage value')
        for spec in specs:
            self.results[spec.id].validate(spec)


class DecisionProvider(Protocol):
    """Only local semantic evaluation; providers do not execute actions."""
    identity: dict
    capabilities: frozenset[str]
    is_live: bool

    def evaluate(self, specs: list[DecisionSpec], context: dict, timeout: float) -> BatchResult: ...


def project_context(specs: list[DecisionSpec], context: dict) -> dict:
    """Project one same-input batch; different read sets require separate batches."""
    require(bool(specs) and len({s.id for s in specs}) == len(specs), 'empty/duplicate decisions')
    for spec in specs:
        spec.validate()
    keys = set(specs[0].required_context)
    require(all(set(s.required_context) == keys for s in specs), 'batch read sets differ')
    require(isinstance(context, dict), 'context must be an object')
    # None is unknown/missing; a declared empty evidence list is still an observable fact.
    missing = sorted(k for k in keys if k not in context or context[k] is None)
    if missing:
        raise ContractError('missing_context:' + ','.join(missing))
    projected = {k: context[k] for k in sorted(keys)}
    require(len(canonical(projected)) <= 65536, 'bounded context exceeds 64 KiB')
    return json.loads(canonical(projected))
