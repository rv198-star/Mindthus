# Brake V0.4 Action-Anchor Dev Freeze Receipt

Run commit: pinned by each generated `run-manifest.json` at campaign start.

This receipt records the static preconditions for the diagnostic-only dev campaign.
It is not a certification claim and does not request a new shadow batch.

## Prompt V0.3 To V0.4

Canonical prompt SHA-256 values, recomputed locally with `shasum -a 256`:

```text
d6086a6a6069ca6bdef5640187c205a75064df47f408794335c24bae23a1aebd  docs/benchmarks/brake-semantic-triage-prompt-v0.3.txt
cf50cd28995eadf1065da28b8bb4555c0b421524cf8eedae971b7939718a15c1  docs/benchmarks/brake-semantic-triage-prompt-v0.4.txt
```

The exact V0.3-to-V0.4 text delta is:

```diff
-- same means type: the repeated fixes use the same kind of intervention, even if the
-  surface verbs, labels, or affected items differ.
+- same means type: the repeated fixes use one local intervention mechanism, defined by a structural operation family and its downstream placement relative to the recurring failure pattern, even if surface verbs, labels, named targets, or named locations differ.
+- mechanism-granularity rule: count prior repairs as one class only when they repeat both the same structural operation family and the same downstream placement relative to a recurring failure pattern; named targets and named locations may differ, but a shared topic, symptom, goal, affected object, or generic change verb alone is not one mechanism.
```

## Approved Anchor Source Status

The following two sentences are quoted verbatim from the approved source packet before
mechanical fixture transcription:

> Status: external-audit text packet. These are not executable fixtures, are not
> generator prompt clauses, and must not be copied into calibration pairs until audit
> clears both the text and the two domains against the complete burned-domain list.

The source packet is now audit-cleared. Its text is preserved as the source of truth;
`tests/brake_loaded_action_v01_anchor_cases.jsonl` transcribes only the two user turns
for A1 and A2. The new fixture SHA-256 is
`bbfe78f370f3e42fb5c7389c4484dc062c262d35a37d3f58acba97167dc16c99`.

## Threshold Config Registration

The config changes only its prompt binding. The numeric threshold remains in place:

```diff
- "prompt_version":"v0.3"
+ "prompt_version":"v0.4"
  "threshold":0.85
```

```text
d50a95e0a75948adc7fd545d3e00918ba123cb8e6d6af9ffc58e4ee1707b9110  v0.3-bound config
a1761f9328adfd0d99a23d1f3aedc1947f1cc20117cee9bf222ab4f78acd1daa  v0.4-bound config
```

## Runner SHA Scope

```text
363c109f3fc3690b267662ce36d17e21cae93e698c195731d80450acac3d31e2  pre-V0.4 runner
989c28b4b11441585431e85311432b74bc98cc2b49c8b2c9e68acdd0a0bd1c7f  current runner
```

The forward delta adds the typed loaded-action contract, separate action artifacts,
action validation telemetry, and the blind whole-answer artifact-smuggling instruction.
It also moves the triage prompt from an embedded V0.3 design block to the canonical
V0.4 file and verifies its SHA. It does not change the triage schema, four-hard-gate
fire predicate, owner-skill exposure gate, or runtime-event false-wake predicate.
`owner_fidelity_for_case` only gains action telemetry fields; its pre-existing verdict
branches are unchanged.

## Evidence Split

The original V0.3 fixture and V0.4 P41-P43/N41-N43 expansion supply triage and
mechanism-granularity evidence. A1/A2 supply loaded-action evidence only: triage fire
is an activation prerequisite, reported separately and excluded from the
mechanism-granularity denominator.
