# #207 WAE Loop: fixed-evidence pilot v1

Date: 2026-09-07. Authorization: user approved MVP construction and live tests in F/K/S.
Status before first request: implementation freeze required; no result inferred here.
Design: ../wae-loop-v0.2/design.md and ../wae-loop-v0.2/mvp-protocol.md.

## Scope and experiment

Three synthetic, self-contained handoffs, no private customer data and no production calls:
F = P2 to P3 executable revision/approval projection (not a browser or full web app).
K = fixed-source knowledge representation and scoped downstream analysis (not repository exploration).
S = three page representations for a decision proposal (not rendered slides, audience tests or aesthetics certification).

A uses the published WAE SKILL plus Ownership Closure resource. B/C share candidate.md,
a generic task-facing projection of v0.2 with no case answers. A/B each have one Owner
opportunity; C has up to three. All are allowed to do substantive work within an
opportunity and to hand off immediately. No minimum cycle count or compulsory reviewer.
Every successful non-boundary handoff goes to one fresh recipient. Need-input, stop,
invalid output or an unfinished final refine is not silently converted into success.

Source, startup, tools and recipient task are fixed per case. Candidate/published guide
length differs and is part of the treatment; B-A is not a pure isolated phrase effect.
B/C have the same 12,000 total reported output-token ceiling, including reasoning when
reported; C per-call ceiling is 6,000 or remaining total, whichever is smaller. Recipient
ceiling is 6,000. Boundary Owner ceiling is 4,000. No claim of matched realized compute.

Direct HTTPS Responses requests use the already-user-authorized sub2api endpoint,
existing local Codex API-key storage, configured model gpt-5.6-sol and high effort.
Returned model/effort and usage fields are recorded. Backend routing is not independently
attested. No CLI shell or tools, no hidden agent loop, no automatic network retry or
redirect, no response conversation reuse, no private reasoning retention. This transport
isolates this experiment; it does not reproduce Codex App or WFF's environment.

## Frozen order and budget

F-A, K-B, S-C, F-B, K-C, S-A, F-C, K-A, S-B;
then F-ready-C, K-guarantee-C, S-missing-C.
One transport-only model probe is counted before slots. All attempts including probe,
timeout, invalid outputs and retries share the 27-request cap. No automatic retry.
If all C trials require three Owner requests, the probe consumes capacity and the
last slot can remain unrun; never conceal this by spending 28 requests.

Hard per-call timeout 120 seconds; cumulative client request time 1,800 seconds;
batch elapsed wall ceiling 5,400 seconds; batch reported output-token ceiling 200,000;
per-prompt 70,000 UTF-8 bytes. Model cap values are resource ceilings, not estimates.
Unknown output usage reserves the requested ceiling conservatively, while reported
usage remains unknown in measurement. No monetary estimate without verified pricing.
The run manifest freezes code, guidance, source, oracles, tests and these settings
before probing. Mid-run changes abort freeze validation. Existing attempt labels
cannot be resent. Interrupted attempts remain visible, not automatically replaced.

## Evaluation and reference checks

F has 48 held-out combinations of role, view, surface and revision states derived
only from the public policy/API. Two different reference implementations must pass;
record-wide approval, reader draft leakage and input mutation mutants must fail.
Generated code executes in a restricted Python worker with AST restrictions, restricted
builtins, CPU/memory limits, no credential environment, and subprocess timeout. This
is not offered as a general adversarial-code sandbox.

K/S have two prewritten adequate examples and frozen per-obligation semantic rubrics in
evaluation.py. These examples and questions/oracles are excluded from Owner requests.
K's receiver sees only the final knowledge and task. F/S receivers also see their
public authoritative sources: if they repair an upstream defect from that source,
report the end-to-end outcome separately from the defective handoff.

K/S evaluation combines mechanically observable properties (references/pages/arithmetic)
with a rubric-based review by this ChatGPT session after outputs are frozen. It is
NOT an independent model or human reviewer and NOT a real audience evaluation.
Same-session knowledge of arm/author creates evaluator-bias risk; do not claim blinded
independent quality certification. Persist per-obligation excerpts and counterexamples,
not only a global score. Allow alternative correct arguments and representations.

No hidden result is supplied to a new Owner cycle. C receives only its previous
artifact/concise decision record and a statement that JSON shape validated. No semantic
oracle feedback, receiver rescue or retry-to-pass. A/B's final refine is unconverged.
The final handoff's obligations are graded independently of recipient implementation.
Existing fact/authority regressions, unjustified deepening and purpose shrinkage fail
promotion even if a recipient guesses an appropriate answer.

## Offline before live

Run selftest.py with zero network calls. Validate routing, budget, isolation, version
binding, attempt uniqueness, invalid-output retention, no forced handoff, and reference
oracle fairness. These tests prove only harness behavior. K/S reference acceptability
is author-audited against the frozen sources, not automatically certified by unit tests.

## Interpretation

One trial per arm per main family plus three boundaries can show runnable paths,
false handoffs and early-exit behavior. It cannot establish repeatability or causal
superiority. If C chooses handoff on its first request, that is legitimate early
exit, but its refine/revisit path has NOT been demonstrated by real models.
If B and C have the same observed quality, no Loop incremental value is established;
one sample cannot establish equivalence. Report all costs, including failed attempts.
No additional repeated batch, production integration or Skill promotion is authorized
by an encouraging first wave; follow-on experiments need a new frozen budget.

## Reproduction

Use Python 3.10+ with requests and jsonschema. No credentials go into files/arguments.

```sh
python3 -B docs/internal/research/wae-loop-mvp/selftest.py -q
python3 -B docs/internal/research/wae-loop-mvp/runner.py init --out /tmp/mindthus-207-wave1-UNIQUE
python3 -B docs/internal/research/wae-loop-mvp/runner.py advance --out /tmp/mindthus-207-wave1-UNIQUE --steps 1
python3 -B docs/internal/research/wae-loop-mvp/runner.py summary --out /tmp/mindthus-207-wave1-UNIQUE
python3 -B docs/internal/research/wae-loop-mvp/evaluation.py --out /tmp/mindthus-207-wave1-UNIQUE
```

Repeat advance to consume the next frozen slot, not to retry a failed slot. Output
files are external runtime evidence, not production Mission state. Copy admitted
results into this research directory only through explicit repository file operations.

Reference for transport semantics only: https://platform.openai.com/docs/api-reference/responses
