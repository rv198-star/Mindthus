# Explain HTML V2 — D1 implementation and recovery

## Status

2026-10-07: #227 code and local engineering verification are implemented on
`feat/explain-html-v2`. The four initial component families are callout, table, flow
and progress/range. The remaining sequence/tree/timeline work in #229 still depends
on the #228 benefit decision; neither V2.1 nor V3 has been started.

This is not an entire-V2 completion, merged-main, published-release, paired-model
benefit or in-conversation HTML visibility claim.

## Implementation

- `skills/explain/scripts/render_explanation.py`: one source parser, CLI and delivery boundary.
- `scripts/explain_compiler/`: source spans/IR, advisory lint, optional Node geometry,
  deterministic Python layout, shared safe HTML and source recovery.
- `skills/explain/resources/html-v2.md`: runnable draft examples, complete initial
  grammar, engine selection, export/recovery/patch and fidelity rules.
- `skills/explain/resources/compiler-notices.md`: exact dependency provenance.
- `tests/test_explain_compiler.py`: 42 behavior and packaging tests.
- `tests/check_explain_browser.mjs`: optional actual-browser matrix.
- `tests/fixtures/explain-v2/showcase.md`: clearly illustrative component gallery.

Node receives graph dimensions/relations only. Markdown parsing, writing rules and
HTML serialization have one implementation. Node availability changes geometry, not
content. No runtime npm/pip install, network request, browser launch or business-state
mutation is added. TPlan continues using its existing renderer and authority.

The dependency bundle was checked by archive digests. Mistune has two documented
packaging-only adjustments for Python3.10 and private namespace imports. Node uses
Dagre's self-contained bundle. All licenses and file digests ship in the Skill.

## Verification

Evidence: [check summary](evidence/d1/checks.json),
[browser matrix](evidence/d1/browser-results.json),
[complete Explain source hashes](evidence/d1/source-manifest.json).

- Focused compiler + Explain + packaging: 101 tests, 100 pass, 1 existing dependency skip.
- Compiler behavior under the already-installed Python3.12: 42/42 pass.
- Five real pack layouts, each run through Python and Node with Python site packages
  disabled: 10/10 successful render/recovery checks.
- Real isolated PATH without Node: auto selects Python, still generates SVG and HTML.
- Real Node22.23.1 and Python3.10.12/3.12.14. Node18/20/22 selection and failure
  branches are tested with fixtures; no real Node20 execution is claimed.
- Chromium: Node/Python × 1440/390 × JS on/off, 8/8 pass. No whole-page overflow,
  clipped SVG labels, implicit HTTP requests or script errors; keyboard details and
  dark/doc controls work. These are browser checks, not a ChatGPT rendering receipt.
- Portability lint: portable=true, 0 errors, 0 warnings. The host rejected its declared
  skill-binding parameter, so the verified local managed helper was run by its actual
  path instead; no tool settings or shared Skill installation were changed.
- Lifecycle registry: 87/87 executable test files registered. Explain SKILL entry
  stays within its existing 10 KiB limit, at 10,223 bytes.

### Existing test environment repair

Full discovery first ran on the system Python3.10. The old partial/shallow clone lacked
an existing pinned historical fixture, and those tests also use Python3.11+ unittest
APIs. No test condition was weakened. The exact fixture commit
`ed5171bf7b34746027acd730864d9c98ef1dd8d2` was fetched; its promised blobs were hydrated
through a temporary detached checkout, then that temporary checkout was removed.
The already-installed Python3.12 ran the affected modules successfully, 23/23.

The Python3.12 full scan had 1,204 tests, 26 initial error reports (including subtests)
and 7 existing skips, all errors in the three fixture-dependent modules. Their full
23-test rerun passed after hydration. This is full discovery plus a targeted successful
rerun, not a claim that the first or second full run was green. Original raw logs and
hashes are retained in the evidence manifest; fixture output saying DELIVERED is from
an offline fake transport, not new model calls.

## Review scope

Current-Agent phase-separated code and boundary review plus mechanical/browser tests.
No independent second-model review has occurred. Source fidelity checks retain labels,
relations, quantities, uncertainty, quotations and citations. Write errors preserve
original files; source recovery verifies integrity but does not authenticate an author.
No production TPlan state, original Jev checkout, main branch or release was changed.

## Next step

#228 can run fixed-source engineering checks on the frozen D1 commit. Its model arm
still needs a specifically authorized channel/model/settings and budget for nine pairs
(18 generations), and actual hosted HTML interaction must be observed separately.
Previous Jev-specific budgets/authorizations do not transfer. Keep #229 waiting rather
than treating synthetic fixtures or screenshots as a completed benefit decision.

## Local recovery

Worktree: `/srv/agentdock/worktrees/Mindthus-explain-v2-design-20261007` (OCI).
Branch: `feat/explain-html-v2`. AgentDock task: `tsk_a315ee4ca6dac6ab`.
Developer evidence cache: `/srv/agentdock/.cache/mindthus-explain-v2-d1`.
Original Jev checkout stays at `8e47cdacc63d3ad53c7fd0f64aa77d9a25e4ebd2`.
Read the live issue comments and commit evidence before continuing; do not recreate
D0 or rerun already-recorded tests without a new code/validation reason.
