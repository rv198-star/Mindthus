# SRA Independent Wake-Up Audit

Date: 2026-09-03
Branch: `audit/sra-wakeup-and-method-boundaries`
Parent issue: #156
Verdict: **INDEPENDENT INVOCATION PASS / BEHAVIORAL WAKE-UP RATE NOT YET CERTIFIED**

## Audit Questions

1. Can SRA be invoked as a standalone Skill without requiring 3L5S, TPlan, or the routing Skill to own the judgment first?
2. When prompts do not name SRA, is there enough routing and benchmark infrastructure to measure natural wake-up and false activation?
3. What wake-up rate is actually supported by current evidence?

This audit keeps availability, routing readiness, and observed behavior separate.

## Evidence Layers

### Layer 1: Direct Standalone Availability

Result: **PASS**.

The SRA frontmatter now begins with an explicit direct-use contract:

```text
Use directly when multiple already-judgeable actions or bundles compete for the same scarce resource.
```

It does not require:

- prior 3L5S execution when candidates are already judgeable;
- an active TPlan Mission;
- routing through `using-mindthus` when SRA is explicitly loaded;
- a particular host runtime.

A release-pack build confirms a standalone `skills/sra/SKILL.md` in all five supported layouts:

1. Claude Code plugin;
2. Claude Code standalone skills;
3. Codex plugin;
4. Codex standalone skills;
5. OpenCode skills.

Direct package availability: **5 / 5 = 100%**.

This proves installable and independently loadable surface coverage. It does not prove that a host will choose SRA naturally.

### Layer 2: Passive Router Readiness

Initial result: **PARTIAL**.

Already present before this audit:

- SRA owner row in `skills/using-mindthus/SKILL.md`;
- SRA recognition in `scripts/run-judgment-benchmark-cli.py`;
- SRA packaging and public method map;
- direct SRA pressure tests.

Missing before this audit:

1. Entry Triage did not register cross-candidate scarce-resource competition as a low-frequency wake-up family.
2. No dedicated weak-cue SRA holdout existed.
3. EDSP and WAE did not both expose a reciprocal handoff back to SRA, increasing adjacent-owner ambiguity.

Remediation:

- added the SRA semantic shape to Entry Triage Disease Families, Trigger Register, ownership tie-breaks, and loaded-action probes;
- clarified the router row as multiple valid, judgeable candidates sharing a common scarce resource;
- added `tests/sra_wakeup_holdout_cases.jsonl`;
- added `tests/sra_wakeup_experiment_design.md`;
- added `tests/test_sra_wakeup_and_boundaries.py`;
- added reciprocal EDSP and WAE boundaries;
- registered the executable test in Test Lifecycle.

Post-remediation routing surfaces:

- direct Skill entry;
- normal router owner table;
- Entry Triage low-frequency register;
- benchmark owner telemetry;
- five release package layouts.

Contract surface coverage: **5 / 5 required wake-up surfaces present**.

### Layer 3: Weak-Cue Case Readiness

Result: **PASS FOR CASE DESIGN**.

The holdout contains 24 prompts with no Mindthus method names:

- 12 SRA-positive cases;
- 8 adjacent-owner controls covering 3L5S, EDSP, SELA, MPG, WAE, TVG, TPlan, and Anti-Spiral;
- 4 stay-asleep controls covering direct debugging, independent parallel work, information acquisition, and a deterministic checklist.

Case contract coverage:

```text
SRA positives             12 / 12
Adjacent-owner controls    8 / 8
Stay-asleep controls       4 / 4
Total                      24 / 24
```

Every SRA-positive case requires action-changing allocation rather than a priority label:

- next meaningful tranche;
- investment ceiling or authorization horizon;
- maintenance line;
- defer or stop set;
- reserve posture;
- reranking trigger.

The experiment distinguishes:

- explicit standalone invocation;
- natural router wake-up;
- adjacent-owner accuracy;
- direct stay-asleep behavior;
- execution impact after wake-up.

## Behavioral Wake-Up Attempt

A fresh Codex CLI probe was attempted from an empty read-only workspace with no method name in the user prompt.

The process reached the model transport and failed before model execution:

```text
HTTP 401 Unauthorized
Missing bearer or basic authentication
```

Valid model outputs: **0**.

Therefore:

```text
Observed natural SRA wake-up rate: N/A
Completed fresh model judgments: 0
Certified positive recall: no
Certified false activation rate: no
```

The infrastructure failure is not scored as a wake-up miss. Reporting `0%` would falsely convert authentication failure into model behavior; reporting a positive percentage would invent evidence.

## Certification Protocol

The committed experiment defines these thresholds for a valid host/model run:

- standalone method execution >= 90%;
- SRA natural positive wake-up recall >= 80%;
- SRA false activation rate <= 10%;
- adjacent-owner accuracy >= 80%;
- direct stay-asleep rate >= 90%;
- execution impact among SRA wake-ups >= 90%.

Optional A/B attribution uses:

- baseline: `b497ee380fb275727f1ba715f8035f17327a7efe`;
- treatment: the final commit from this audit branch.

## Findings

### W1 — Direct Use Was Implicit Rather Than Explicit

The original SRA description allowed standalone use but did not say `Use directly` or explicitly state candidate readiness.

Status: **FIXED**.

### W2 — Entry Triage Could Miss SRA As A Low-Frequency Owner

The normal owner table contained SRA, but the lower-frequency semantic trigger register omitted it. A host that consults Entry Triage for ambiguous low-frequency routes could remain in generic prioritization, 3L5S, or direct advice.

Status: **FIXED**.

### W3 — No Dedicated Natural Wake-Up Holdout

Pressure tests exercised SRA behavior after entry, but no case set measured whether the router selected SRA without naming it or over-called SRA on neighboring methods.

Status: **FIXED AT TEST-DESIGN LEVEL**. Behavioral execution remains pending.

### W4 — Static Green Cannot Be Reported As Wake-Up Rate

All deterministic tests may pass while a host never loads the Skill. This distinction is now explicit in the experiment and audit contract.

Status: **FIXED IN CLAIM BOUNDARY**.

## Mechanical Evidence

```text
git diff --check                         PASS
python3 -m compileall -q skills scripts tests
                                           PASS
SRA/router/method focused suite          109 PASS
Test Lifecycle executable coverage       73 / 73
full unittest suite                       927 PASS, 5 skipped
all-platform release pack                PASS
SRA direct package layouts                5 / 5
TPlan hook/schema/runtime diff            EMPTY
```

The model-level wake-up probe remains excluded from these pass counts because it failed
at authentication before model execution.

## Final Verdict

- Standalone SRA invocation surface: **PASS**.
- Installed direct availability: **100% across 5 / 5 supported layouts**.
- Natural wake-up routing contract: **PASS**.
- Weak-cue benchmark readiness: **PASS, 24 / 24 cases structurally valid**.
- Actual natural wake-up recall: **NOT MEASURED**.
- Actual false SRA activation rate: **NOT MEASURED**.
- Mainline or release claim that SRA has a proven wake-up rate: **HOLD** until valid fresh model and judge outputs exist.
