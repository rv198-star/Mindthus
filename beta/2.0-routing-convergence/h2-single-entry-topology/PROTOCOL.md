# H2 — Single Entry / On-demand Owner Topology

Status: `FROZEN_FOR_IMPLEMENTATION`

## Decision claim

H2 tests the Mission's final architecture hypothesis: Codex discovers exactly one thin
Mindthus Skill; that entry retains the four passive obligations and reads a small owner
index plus one formal owner contract only when a hard judgment remains. All work stays
inside the same user turn except one genuinely blocking Decision Context question.

This is not a repair of H1. H1 proved that owner metadata can remove false owner loads
but cannot make an already injected entry ask before giving a direction. H2 therefore
changes discovery topology and makes Decision Context the first control branch.

## Frozen topology

```text
skills/
└── using-mindthus/
    ├── SKILL.md                         # the only discoverable Skill
    └── references/
        ├── owner-index.md               # read only after a hard judgment remains
        └── owners/
            ├── 3l5s/OWNER.md
            ├── edsp/OWNER.md
            ├── sela/OWNER.md
            ├── mpg/OWNER.md
            ├── wae/OWNER.md
            ├── tvg/OWNER.md
            ├── tplan/OWNER.md
            └── _runtime/...
```

Each owner directory retains its original resources, templates, scripts, and fixtures.
The source `SKILL.md` is renamed to `OWNER.md` at package time so nested contracts cannot
re-enter Codex discovery. Mechanical namespace and relative-path adaptation is allowed;
reverse-normalized owner content and support trees must match the frozen 1.4.6 sources.

The package has no other `SKILL.md`, Hook, AGENTS injection, defaultPrompt, passive
kernel, second guard, router script, model-name branch, symlink to a Skill directory, or
dynamic prompt carrier. Stable is not co-enabled.

## Thin entry mainline

The entry is capped at 3,000 bytes and 320 words. It contains only:

1. **Decision Context first.** When a request asks for a continue/commit/hold/stop/exit/
   switch decision and missing actor, target, timing, authority, exposure, rollback, or
   acceptable loss could flip the answer: read no index or owner, give no direction or
   interim posture, ask exactly one blocking question, and end the turn.
2. **Direct.** Clear, low-risk, fact-sufficient work proceeds without an owner.
3. **Evidence first.** Missing facts, files, runtime proof, rules, or authority are
   acquired before methodology.
4. **Passive obligations.** Frame, Whole, Decision Context, and Anti-Spiral retain their
   decision-changing behavior.
5. **Hard judgment.** Only after context is locked, read `references/owner-index.md`.
   If exactly one gate independently matches and changes definition, evidence, action,
   or stop, read exactly that `OWNER.md` fully before acting. A genuine owner ambiguity
   may ask one blocking question; otherwise no match means direct work.

The entry never prints an owner menu, explains routing, or requests method confirmation.

## Owner index boundary

The index is a legal on-demand resource, not a discoverable or constant carrier. It may
contain exactly seven rows. Each row has a positive domain gate, hard exclusion, and
relative `OWNER.md` path. It contains no method steps, examples, output templates,
companion graph, fallback flow, keyword score, scripts, or owner-body synopsis.

Reading the index on ordinary, evidence-first, near-negative, or missing Decision
Context work is a qualification failure. Adding a second index or routing stage is
forbidden.

## Static qualification

Before any live call, prove:

1. `find skills -name SKILL.md` returns exactly `using-mindthus/SKILL.md`.
2. Seven `OWNER.md` trees exist; no owner `SKILL.md` or top-level owner metadata exists.
3. Reverse-normalized owner bodies/support trees match frozen 1.4.6 hashes.
4. Every owner-relative resource/script/template path resolves in the package; the
   SELA/MPG companion read resolves to a sibling `OWNER.md`.
5. The entry references one index and the index references exactly seven owners.
6. No forbidden carrier exists and plugin.json has no `defaultPrompt` field.
7. The entry and index stay within frozen byte/word budgets.
8. A fresh isolated `CODEX_HOME` enables only this candidate.
9. Raw JSONL can show exact entry, index, and owner-resource reads.

One zero-call equal replacement/subtraction may fix a static implementation defect
before the candidate is frozen. After the first live call, there is no correction budget:
all seven remaining qualification calls are required for one digest.

## Seven-call live qualification

All calls use `gpt-5.6-sol / xhigh`, run serially, and stay below 200,000 counted tokens.
Every case has an independent workspace; Q1/Q2 share one persistent conversation.

1. **Decision Context.** Use the frozen underspecified migration prompt. Pass: entry
   only; no index/owner; no continue/hold/stop posture; exactly one answer-changing
   blocking question.
2. **Clear MPG after context.** Supply the frozen CTO/Q4/dual-write/exposure/rollback/
   lag/cutover context. Pass: entry, index, and MPG resource read in the same turn;
   path-carrying action; no unrelated owner or visible routing round.
3. **Clear WAE.** Pass: entry, index, and WAE resource read in the same turn; useful
   control split; no unrelated owner or routing round.
4. **Evidence First + Frame + Whole near-negative.** Read the frozen release evidence;
   preserve the passing unit test as local truth, deny it whole-result control, and
   `NOT APPROVED/HOLD` for named missing product evidence. Only the entry may load.
5. **Ordinary.** Create exactly `17`. Pass: only entry; no index/owner or ceremony.
6. **Genuine owner ambiguity.** A real next action is ambiguous between changing an
   agentic production controller (WAE) and strengthening an existing bounded control
   artifact (TVG). Pass: entry and index, no owner body or direction, exactly one
   blocking target question, then end the turn.
7. **Anti-Spiral.** A fixture contains an incident, a plan already changed twice, two
   real edit records, and an evidence index proving no new evidence. The neutral prompt
   asks to improve the plan again. Pass: entry and evidence read; plan unchanged; no
   index/owner; refuses another layer and returns to the missing upstream evidence.

Q7 does not tell the model that this is a third pass or prescribe the stop answer. The
fixture, hashes, and diffs must carry that fact.

Any semantic failure yields `H2_REJECTED`; missing credible lifecycle or isolation
evidence yields `STOP_UNPROVEN`. Neither permits a live correction because a different
digest cannot be fully requalified inside the remaining seven-call ceiling.

## Compatibility and claim ceiling

Moving owners out of discovery removes direct `$mindthus:<owner>` coordinates. Natural
language work can still enter through the sole entry, but explicit owner invocation—most
notably `$mindthus:tplan`—is a potential product-level regression. Qualification may
prove the topology mechanism but cannot waive this loss. If H2 qualifies, the Stable
comparison and responsibility-separated usability review must decide whether this is a
decision-changing regression; one critical failure blocks `CONTINUE`.

Qualification samples WAE and MPG live; static locks cover the other contracts. It does
not claim that all seven owners have been individually live-certified.

If every technical criterion passes and the only remaining blocker is loss of explicit
`$mindthus:<owner>` coordinates, the Mission enters `REQUIRES_WILLIAM`; a Judge cannot
waive or condemn that 2.x product compatibility choice.

## Terminal rules

- Seven live passes: `H2_ELIGIBLE_FOR_STABLE_COMPARISON`.
- Any trusted critical failure: `H2_REJECTED`, then `STOP_2X_EXPLORATION`.
- Missing trustworthy activation/isolation evidence: `STOP_UNPROVEN`, then
  `STOP_2X_EXPLORATION`.
- No H3, no extra calls, no hidden carrier, no test relaxation, no release work.
