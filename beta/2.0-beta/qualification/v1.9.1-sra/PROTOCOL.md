# v1.9.1 ROI Beta deterministic SRA compatibility protocol

This qualification checks composition compatibility only. It does not re-label Stable
behavioral evidence as Beta model-quality evidence.

## Frozen inputs

- Stable shared core: `d735d11c14d92325607fe6b844eb29f7c426df62`
- Stable tree: `9c301753689d5ceb5f9fa2019ca41b4425f583bd`
- Runtime overlay implementation: `0bd58701fd36f33d5640ff2d00aa5e208026dbfa`
- Historical ROI.2 qualification: `4ee3e034db6bf8d1e34002d7f162e2b008516490`

## Gates

1. Build Stable plugins from the frozen shared core.
2. Build the ROI Beta twice from a clean source checkout.
3. Verify exact shared-core identity, Beta identity and namespace isolation.
4. Verify all non-declared-delta files are byte-identical after namespace normalization.
5. Verify the SRA v0.3 domain, integrity, Repair and Full-view surfaces are inherited.
6. Verify the cumulative Demand and prepared-input anchor regression tests are present in
   the frozen shared core.
7. Verify both Beta archives are byte-identical.

The result supports packaging and inheritance claims only. Natural activation, relative
model quality, universal allocation correctness and Token ROI remain unmeasured here.
