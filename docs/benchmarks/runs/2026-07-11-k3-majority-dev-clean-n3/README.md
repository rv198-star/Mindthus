# Clean k=3 dev run status

This campaign uses the frozen k=3 fire policy and owner-skill exposure gate.
Only complete repeats count toward the pre-registered six gates.

## Status

- `repeat-1/` is complete: anchors, original fixture, and v0.4 expansion all
  completed without provider-limit events or contamination.
- `invalid-attempt-quota-exhaustion-repeat-2-20260711T2102+0800/` is fully
  excluded. The provider reported a usage limit during the original fixture;
  its successful anchor pack and partial original artifacts cannot be combined
  with repeat 1.
- Repeat 3 has not started. The n=3 gate is therefore not decided.

## Frozen identity

- Runner SHA-256:
  `183a34888d68042abf2427fe0f14e83a780fccbe85909c3ea32acc433fbbb6de`
- Prompt SHA-256:
  `cf50cd28995eadf1065da28b8bb4555c0b421524cf8eedae971b7939718a15c1`
- Fire-policy SHA-256:
  `7c4594ee35b14f7d60fa59fdc79cc5a7a745583ebf498aeb15e5944128a5c018`

The prestart directory under `repeat-1/` is also excluded; it contains no
model responses and exists solely to document the host-reaped background
launch. `repeat-1/v04-expansion/` is the valid scored expansion run.
