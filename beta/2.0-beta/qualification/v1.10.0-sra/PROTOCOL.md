# v1.10.0 ROI Beta deterministic SRA compatibility protocol

This qualification checks composition compatibility only. It does not turn Stable
regression evidence into Beta-specific model-quality or ROI evidence.

## Frozen inputs

- Stable shared core: `facc26ebac7004700881bd45f60e33960a197761`
- Stable tree: `c00780d3c43086378e10bd51521c5453212bc8b0`
- Runtime overlay implementation: `0bd58701fd36f33d5640ff2d00aa5e208026dbfa`
- Historical ROI.2 qualification: `4ee3e034db6bf8d1e34002d7f162e2b008516490`
- Prior v1.9.1 compatibility qualification: `69a4efdcfdc31b43faa26dea857e9894ba1d6c93`

## Gates

1. Build Stable Codex plugin bytes from the frozen shared core.
2. Build the ROI Beta twice from one clean final Beta source checkout.
3. Verify exact shared-core commit/tree, Beta identity and namespace isolation.
4. Verify all non-declared-delta files are byte-identical after namespace normalization.
5. Verify v1.9.x SRA resource, cumulative Demand, dependency, integrity and Repair surfaces remain inherited.
6. Verify v1.10.0 SRA Proportionate Allocation surfaces are inherited, including the v0.4 input contract, proportionate policy, checked-card/intake helpers, completion criteria and rerank helper.
7. Verify source tests retain explicit v0.3 compatibility and old-reader rejection of v0.4.
8. Verify the frozen ROI Thin Core remains within its qualified size/marker boundary and does not become a second allocation owner.
9. Verify both final Beta archives are byte-identical.

The result supports deterministic packaging, shared-core inheritance and namespace claims.
Natural activation, relative model quality, universal allocation correctness, real-task
benefit and Token ROI remain unmeasured by this protocol.
