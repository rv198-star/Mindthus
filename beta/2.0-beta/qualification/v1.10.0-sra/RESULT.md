# v1.10.0 ROI Beta deterministic SRA compatibility result

Date: 2026-09-05

Status: **PASS with explicit claim ceiling**

## Frozen identities

- Stable shared core commit: `facc26ebac7004700881bd45f60e33960a197761`
- Stable shared core tree: `c00780d3c43086378e10bd51521c5453212bc8b0`
- Candidate Beta source used for this qualification: `d6b547d08e054fb59b4cb4772f92ffab80487b31`
- Runtime overlay implementation: `0bd58701fd36f33d5640ff2d00aa5e208026dbfa`
- Historical ROI.2 qualification: `4ee3e034db6bf8d1e34002d7f162e2b008516490`

## Deterministic qualification

`qualification/v1.10.0-sra/verify.py` passed against a Stable Codex plugin generated
from the exact frozen Stable source and an assembled Beta candidate.

Verified boundaries include:

- exact Stable commit/tree inheritance;
- separate `mindthus-beta` plugin identity and namespace isolation;
- the frozen 2274-byte ROI Thin Core and its SRA routing marker;
- byte equality for every non-declared-delta shared-core file after namespace normalization;
- inherited v1.9.x cumulative Demand, dependency-authorization and prepared-input Repair blockers;
- inherited v1.10.0 `sra.decision-context-input.v0.4` and `sra.proportionate.v1` identities;
- inherited proportionate runtime, intake draft, checked-card, completion-criterion and rerank surfaces;
- source regressions for legacy Full dual-view behavior, explicit v0.4 versioning and rerank lineage protection.

Two independent Beta archive builds were byte-identical:

`e40e14b30f59eba2f6ffb4e8e1708c236e05433c8aba6797ef1cabcbb7b95396`

The packaged runtime diagnostic also passed `--strict` when repo, marketplace and cache
roots were explicitly bound to the same inspectable built artifact. That check proves
file/hash/marker integrity only; it is not a real installed-host activation test.

## Repository regression

On the Beta composition source before publication-finalization:

- complete unittest discovery ran 1054 tests and passed, with 5 documented optional-dependency skips;
- Test Lifecycle reported 78/78 executable test files registered and `status=valid`;
- packaged Python surfaces compiled successfully;
- `git diff --check` passed.

## Claim ceiling

This PASS supports deterministic Beta composition, shared-core inheritance, packaging,
namespace isolation and the named SRA compatibility boundaries only.

It does **not** prove Beta-specific natural activation, relative model quality, real-task
benefit, universal allocation correctness, host-level activation parity or Token ROI.
