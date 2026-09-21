"""Bridge to existing Judgment Trace v1.1 without claiming unobserved host actions."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys


def from_c01(report: dict, file_receipt: dict | None = None) -> dict:
    result = report['result']
    route = result['route']
    owner = result['owner']
    decision = {'intervene': 'intervene', 'direct_execute': 'direct_execute',
                'acquire_information': 'acquire_information'}.get(route, 'block')
    object_name = {'3l5s': 'problem_definition', 'sra': 'scarce_resource_allocation',
                   'edsp': 'structural_ambiguity', 'sela': 'strategy_direction',
                   'mpg': 'path_carrying', 'wae': 'controller_boundary',
                   'tvg': 'artifact_value', 'tplan': 'mission_runtime'}.get(owner, 'unknown')
    if route == 'direct_execute':
        owner, object_name = 'direct_execution', 'direct_task'
    elif route == 'acquire_information':
        owner, object_name = 'information_acquisition', 'information_gap'
    else:
        owner = owner or 'unknown'
    fields = {'input_shape.judgment_object': 'inferred',
              'input_shape.hard_judgment_point': 'inferred' if result['hard_judgment'] is not None else 'unknown',
              'routing.judgment_owner': 'inferred', 'routing.loaded_methods': 'runtime_observation',
              'routing.routing_decision': 'inferred', 'decision_delta.basis': 'runtime_observation',
              'decision_delta.comparison_ref': 'unknown', 'outcome.status': 'runtime_observation'}
    delta = {'basis': 'not_assessed', 'comparison_ref': None}
    for key in ('strategy_changed', 'risk_handling_changed', 'evidence_requirement_changed',
                'next_action_changed', 'stopping_condition_changed', 'handoff_changed'):
        fields['decision_delta.' + key] = 'unknown'
        delta[key] = 'unknown'
    trace = {'schema_version': 'mindthus.judgment-trace.v1.1',
             'trace_id': 'c01-' + report['run_id'][:24],
             'timestamp_utc': datetime.now(timezone.utc).isoformat(),
             'provenance': {'producer': 'typed-decision-offline-probe', 'source_type': 'mixed',
                            'source_ref': report['source_ref'], 'field_sources': fields},
             'input_shape': {'judgment_object': object_name,
                             'hard_judgment_point': result['hard_judgment'] is True,
                             'frame_status': 'not_assessed', 'active_constraints': result['obligations']},
             'routing': {'judgment_owner': owner, 'routing_decision': decision, 'loaded_methods': []},
             'evidence': {'available_evidence_classes': ['offline-control-flow-fixture'] +
                          (['local-skill-file-read'] if file_receipt else []),
                          'missing_evidence_classes': ['native-host-skill-load', 'live-model-result',
                                                       'downstream-task-acceptance'],
                          'claim_ceiling': 'Offline mechanical probe only; a file read is not a native '
                          'skill load, model quality, or counterfactual value.'},
             'decision_delta': delta, 'outcome': {'status': 'not_evaluated'}}
    return trace


def validate_with_existing(trace: dict, repo: Path) -> None:
    sys.path.insert(0, str(repo / 'skills'))
    from _runtime.judgment.trace import validate_judgment_trace_or_raise
    validate_judgment_trace_or_raise(trace)
