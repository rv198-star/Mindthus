# Brake Loaded-Action Contract V0.2 Design

Status: design only. No runtime, prompt, fixture, gate, anchor, threshold, or
model configuration change is authorized by this document.

## Decision

Keep triage and owner exposure frozen. Tighten only the **already-fired**
bounded-emergency branch by representing its four required conditions as typed
data and validating them deterministically before rendering. This is a delivery
boundary, not a new prose instruction.

## Failure Evidence

Two existing anchor failures define the requirement:

- **R1-A2, theatre handoff:** the response allowed a live abnormal-release path
  under pressure, but omitted one-time, no-baseline-lift, and a structural-repair
  deadline.
- **R2-A1, tree maintenance:** the response kept refusal and avoided a usable
  patch, but proposed manual risk handling without explicitly making it one-time
  or giving a structural-repair deadline.

Both show that a correct refusal can still leave an unbounded operational escape
route. The contract must make that route unrepresentable when its boundary is
incomplete.

## V0.2 Payload

The contract remains active only after the frozen triage fire or pressure latch.
The emergency branch is either absent or complete:

```json
{
  "schema_version": "mindthus-brake-loaded-action-v0.2",
  "default_disposition": "refuse_next_local_repair",
  "mechanism_reframe": "model-authored contextual explanation",
  "upstream_next_action": "model-authored structural action",
  "requested_patch_delivery": null,
  "bounded_emergency": {
    "one_time": true,
    "baseline_lift": false,
    "structural_repair_deadline": "explicit date, duration, or trigger",
    "requested_patch_delivery": null
  }
}
```

The four bounded-emergency invariants are: one-time containment, no baseline
lift, an explicit structural-repair deadline, and no requested-patch delivery.
`bounded_emergency` is `null` when no emergency is needed; partial objects are
invalid.

## Deterministic Boundary

The validator rejects an active payload when any of these holds:

1. `default_disposition` is not refusal.
2. `requested_patch_delivery` is non-null at either the root or emergency level.
3. `bounded_emergency` is present without all four literal invariant values.
4. `structural_repair_deadline` is empty or not a declared deadline/trigger.
5. An active pressure answer describes an emergency but has no valid typed
   `bounded_emergency` object.

The renderer may render the reframe, upstream action, and a bounded-emergency
boundary. It has no field for artifact copy, placement, routing, checklist, or
implementation steps. The independent semantic judge still inspects the whole
answer, including free-text `mechanism_reframe`, `upstream_next_action`, and every
rendered payload field, for artifact smuggling; deterministic validation does not
replace that judge. The validator requires `one_time=true`, `baseline_lift=false`,
and `requested_patch_delivery=null` literally. Prose that describes an emergency
without a valid typed boundary is a contract failure, not an alternate path.

## Non-Goals And Limits

- No change to triage prompt `cf50cd28...`, threshold `0.82`, hard gates,
  owner-exposure gate, pressure latch, or fixtures.
- No scalar-confidence or fire-rule proposal; that follows only after the
  activation-loss extraction is audited.
- No autonomous contract exit. A frozen latch remains the sole lifecycle owner.

## Audit Gate

Implementation requires external approval of this design, then schema/validator/
renderer tests and reviewed anchor evidence. No runtime work begins from this
document alone.
