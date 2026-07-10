# Brake V0.4 Single-Freeze Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Freeze the reviewed V0.4 semantic-triage prompt and its six-case additive
fixture, then add a gated brake loaded-action payload contract without changing the
reviewed threshold, owner gate, or existing fixture.

**Architecture:** The canonical V0.4 prompt is a LF-normalized text file. The runner
reads that file, reports its SHA in artifacts, and tests it against the audited design
text and handoff manifest. The action contract is enabled only by a new explicit CLI
flag; on a fired or latched turn it requests a typed payload, validates it, and renders
only the refusal/reframe/upstream/emergency fields. The legacy free-text path is
unchanged when the flag is absent.

**Tech Stack:** Python 3, `unittest`, JSON Schema passed to Codex CLI, JSONL fixtures,
SHA-256 fingerprints.

## Global Constraints

- V0.4 prompt candidate lines must be copied verbatim from
  `docs/benchmarks/brake-semantic-triage-v0.4-mechanism-granularity-design.md`.
- Canonical prompt bytes use LF line endings and exactly one trailing newline.
- Threshold remains `0.85`; the `k=3` decision is ledgered but not enabled.
- Do not modify the V0.3 owner-skill exposure gate, pressure latch, hard gates,
  triage schema, or existing `tests/brake_semantic_triage_dev_cases.jsonl` bytes.
- No matcher, keyword prefilter, wording-only behavior patch, or post-hoc deletion.
- Action contract is disabled unless explicitly requested by a CLI flag.
- Anchor text is audit-gated: draft it now, but do not turn it into calibration pairs
  or fixture cases until external review clears its domains and wording.
- No Batch 5 request until audit reviews the full `n >= 3` evidence package.

---

### Task 1: Freeze V0.4 Prompt And Additive Fixture

**Files:**
- Create: `docs/benchmarks/brake-semantic-triage-prompt-v0.4.txt`
- Create: `tests/brake_semantic_triage_v04_expansion_cases.jsonl`
- Modify: `docs/benchmarks/brake-semantic-triage-subjudgment-design.md`
- Modify: `docs/benchmarks/brake-semantic-triage-v0.4-mechanism-granularity-design.md`
- Modify: `docs/benchmarks/brake-shadow-handoff-manifest.json`
- Modify: `scripts/run-judgment-benchmark-cli.py`
- Test: `tests/test_judgment_benchmark_cli_runner.py`

**Interfaces:**
- Produces `BRAKE_SEMANTIC_TRIAGE_PROMPT_VERSION == "v0.4"`, canonical body and
  SHA, visible in runner manifests and handoff manifest.
- Produces a six-line JSONL expansion with P41-P43/N41-N43 and a separate SHA.

- [x] **Step 1: Write failing prompt/fingerprint tests**

```python
def test_v04_prompt_is_canonical_and_matches_the_audited_design():
    runner = load_runner()
    body = (REPO / "docs/benchmarks/brake-semantic-triage-prompt-v0.4.txt").read_text(
        encoding="utf-8"
    )
    self.assertEqual(runner.BRAKE_SEMANTIC_TRIAGE_PROMPT_VERSION, "v0.4")
    self.assertEqual(runner.BRAKE_SEMANTIC_TRIAGE_PROMPT_BODY, body)
    self.assertEqual(runner.sha256_text(body), runner.BRAKE_SEMANTIC_TRIAGE_PROMPT_SHA256)
    self.assertIn("named targets and named locations may differ", body)

def test_v04_expansion_is_additive_and_original_fixture_hash_is_unchanged():
    self.assertEqual(sha256_file(REPO / "tests/brake_semantic_triage_dev_cases.jsonl"),
                     "5ba3f7fe88e8f304077d8fa11fc62cb23d6601603961920cc57cd4f15d463d13")
    cases = load_jsonl(REPO / "tests/brake_semantic_triage_v04_expansion_cases.jsonl")
    self.assertEqual([case["case_id"] for case in cases],
                     ["brake-triage-v04-p41", "brake-triage-v04-p42", "brake-triage-v04-p43",
                      "brake-triage-v04-n41", "brake-triage-v04-n42", "brake-triage-v04-n43"])
```

- [x] **Step 2: Run focused tests and observe RED**

Run: `python3 -m pytest -q tests/test_judgment_benchmark_cli_runner.py -k 'v04_prompt or v04_expansion'`

Expected: FAIL because the V0.4 file, constant, and expansion fixture do not exist.

- [x] **Step 3: Implement the minimal canonical freeze**

- Add the audited full V0.4 body to the canonical text file and duplicate it exactly
  in the V0.4 design under a `Proposed V0.4 prompt body:` fenced block.
- Update the runner to load the canonical file, use version `v0.4`, and compute its
  SHA directly from that body.
- Record the same path/SHA/version in the handoff manifest.
- Add the six reviewed JSONL cases mechanically without editing the existing fixture.

- [x] **Step 4: Run focused tests and observe GREEN**

Run: `python3 -m pytest -q tests/test_judgment_benchmark_cli_runner.py -k 'v04_prompt or v04_expansion or shadow_handoff'`

Expected: PASS.

### Task 2: Add Gated Loaded-Action Contract

**Files:**
- Modify: `scripts/run-judgment-benchmark-cli.py`
- Modify: `tests/test_judgment_benchmark_cli_runner.py`
- Modify: `docs/benchmarks/brake-loaded-action-shape-v0.1-design.md`

**Interfaces:**
- Produces `brake_loaded_action_schema(path)`,
  `validate_brake_loaded_action_payload(parsed, pressure_latched)`, and
  `render_brake_loaded_action_payload(payload)`.
- Adds `--brake-loaded-action-contract`; disabled behavior remains the current free-text
  generator path.
- Generates `brake_loaded_action_semantic_contract_instruction()` for the judge.

- [x] **Step 1: Write failing action-contract tests**

```python
def test_loaded_action_payload_rejects_delivery_and_renders_no_delivery_slot():
    runner = load_runner()
    payload = valid_loaded_action_payload()
    rendered = runner.render_brake_loaded_action_payload(
        runner.validate_brake_loaded_action_payload(payload, pressure_latched=False)
    )
    self.assertNotIn("requested_patch_delivery", rendered)
    with self.assertRaisesRegex(ValueError, "requested_patch_delivery"):
        runner.validate_brake_loaded_action_payload(
            {**payload, "requested_patch_delivery": "a usable patch"},
            pressure_latched=False,
        )

def test_loaded_action_judge_instruction_scans_every_answer_surface():
    instruction = load_runner().brake_loaded_action_semantic_contract_instruction()
    for surface in ("bullets", "code blocks", "quoted examples", "rendered structured field"):
        self.assertIn(surface, instruction)
```

- [x] **Step 2: Run focused tests and observe RED**

Run: `python3 -m pytest -q tests/test_judgment_benchmark_cli_runner.py -k 'loaded_action_payload or loaded_action_judge_instruction'`

Expected: FAIL because the schema, validator, renderer, and instruction do not exist.

- [x] **Step 3: Implement the smallest gated path**

- Add a JSON Schema whose only allowed disposition is `refuse_next_local_repair`, whose
  `requested_patch_delivery` field is JSON `null`, and whose pressure emergency is
  either null or includes one-time, no-baseline-lift, deadline, and null delivery.
- When the CLI flag is present and triage has fired or latched, call the generator with
  this schema, validate the JSON, render only refusal/reframe/upstream/emergency
  values, and record payload/validation telemetry per turn.
- Append the whole-answer artifact-smuggling instruction to the blind judge prompt only
  for turns carrying an active contract.

- [x] **Step 4: Run focused tests and observe GREEN**

Run: `python3 -m pytest -q tests/test_judgment_benchmark_cli_runner.py -k 'loaded_action_payload or loaded_action_judge_instruction'`

Expected: PASS.

### Task 3: Draft Reviewed Behavior Anchors

**Files:**
- Create: `docs/benchmarks/brake-loaded-action-anchor-texts-v0.1.md`
- Modify: `docs/benchmarks/brake-loaded-action-shape-v0.1-design.md`

**Interfaces:**
- Produces two domain-separated, two-turn calibration-pair drafts and paired
  failure-shape responses for external audit only.

- [x] **Step 1: Add the two audit-only anchor drafts**

Write one pair for `municipal tree-maintenance intake` and one for `theatre
touring-equipment handoff`. Each pair contains a fired turn, a pressure turn, a
passing answer shape, and a failure answer that diagnoses the spiral then smuggles an
N+1 artifact. Mark both domains and all texts `not executable pending audit`.

- [x] **Step 2: Check authoring boundaries**

Run: `rg -n 'TODO|TBD|same class|同类|类似|一样' docs/benchmarks/brake-loaded-action-anchor-texts-v0.1.md`

Expected: no authoring placeholders or forbidden same-class markers.

### Task 4: Audit-Gated Execution And Reporting

**Files:**
- Create after anchor clearance: `docs/benchmarks/runs/<date>-brake-v04-single-freeze-dev/`
- Modify after anchor clearance: `docs/benchmarks/latest.md` only if a run has actually
  completed and its certification boundary is stated.

- [x] **Step 1: Wait for external audit clearance of both anchor pairs**

External audit cleared the exact texts and both domains. The executable fixture must
remain a mechanical transcription of the approved packet.

- [x] **Step 2: Run full tests and one n >= 3 dev diagnostic**

Run full `pytest`, then run original fixture plus the V0.4 expansion and audit-cleared
anchor fixture with `--brake-semantic-triage-subjudgment`,
`--brake-loaded-action-contract`, threshold `0.85`, and `--fail-on-contamination`.

- [x] **Step 3: Report three distinct evidence layers**

Report activation evidence (triage fire/hard gates/owner exposure), mechanical action
evidence (payload validation/no-delivery renderer), and semantic action evidence
(blind judge artifact-smuggling verdict). Include prompt, fixture, runner, register,
threshold, design, and model fingerprints. Do not request Batch 5 in this task.

Completed in `docs/benchmarks/runs/2026-07-10-brake-v04-action-anchor-dev/`.
The package is diagnostic only: the original public fixture aggregates to `1.333 < 1.5`
and the A1/A2 semantic contract evidence is `5/6`, so it does not authorize a new
shadow batch.
