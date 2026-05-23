# SELA / EDSP Multi-Role A/B Run Record — 2026-05-23

This record captures the first A/B check for the single-agent multi-role changes added
in commit `0ea8f8b`.

## Change Under Test

Two methods gained single-agent multi-role pressure:

- `EDSP`: `Builder / Challenger / Synthesizer`
- `SELA`: `System Advocate / Local Defender / Timing Auditor`

Separate agents remain an escalation option, not the default.

## Runner

- `codex exec --sandbox read-only --cd /root/mindthus`
- model shown by runner: `gpt-5.5`
- no browsing and no file edits inside the run prompts
- baseline prompts explicitly forbade the new role names

## Scenario 1: EDSP Validation Control Boundary

Pressure:

- malformed binary: scripts for all validation versus agentic review for all validation
- artifacts mix deterministic checks with architecture, business, and release claims
- false block and false approval are both costly

Result:

| Variant | Result | Interpretation |
|---|---|---|
| A / baseline | Diagnosed the binary as malformed and recommended scripts for deterministic gates plus agentic review for semantic claims. | Baseline was already strong; EDSP's prior method could solve this case. |
| B / treatment | Produced `builder_dimensions`, `challenger_findings`, and `synthesizer_decision`; added clearer release-readiness and business-claim handling. | Treatment added reviewable pressure without changing the sound conclusion. |

Observed positive gain:

- Challenger surfaced that release readiness is composite, not a single validator output.
- Challenger required source-of-truth evidence or owner approval for business claims.
- Final recommendation mapped artifact classes more explicitly.

Observed negative gain:

- None in the output. Treatment still rejected agent review for mechanical checks.

## Scenario 2: EDSP Low-Risk Deterministic Formatting

Pressure:

- fixed JSON schema
- deterministic formatting
- reversible failure
- binary match/no-match decision

Result:

| Variant | Result | Interpretation |
|---|---|---|
| A / baseline | Recommended deterministic script validation. | Correct lightweight result. |
| B / treatment | `multi_role_used=false`; recommended deterministic script validation. | No overhead regression. |

Observed positive gain:

- Treatment explicitly stated that multi-role was not justified.

Observed negative gain:

- None observed. It did not add Builder/Challenger/Synthesizer ceremony.

## Scenario 3: SELA SaaS Onboarding Replacement

Pressure:

- AI has strong system efficiency: 1/20th cost and 24/7
- humans retain local advantage for enterprise edge cases, trust, compliance exceptions,
  and angry high-value customers
- full immediate cutover has contract and staffing rollback delay

Result:

| Variant | Result | Interpretation |
|---|---|---|
| A / baseline | Recommended AI-first onboarding for standard/low-risk accounts while keeping humans for enterprise/high-risk accounts. | Baseline was already reasonable because SELA had timing checks before this change. |
| B / treatment | Separated `system_advocate`, `local_defender`, and `timing_auditor`; kept AI-first but staged by cohort. | Treatment added clearer risk attribution and timing discipline. |

Observed positive gain:

- Treatment named hidden escalation load, specialist attrition, contractual/SLA friction,
  and QA/monitoring/prompt-maintenance cost as things that could erode efficiency.
- It preserved the system-efficiency direction while preventing immediate full replacement.

Observed negative gain:

- None in the output. Treatment did not become anti-automation or demand heavy process.

## Scenario 4: SELA Low-Risk Internal Digest

Pressure:

- internal-only weekly digest
- low stakes and easy rollback
- manual path costs 6 hours/week
- automated path is 90 percent accurate and source-linked
- no customer or compliance dependency

Result:

| Variant | Result | Interpretation |
|---|---|---|
| A / baseline | Recommended replacing manual digest with automated digest as default. | Correct lightweight result. |
| B / treatment | `multi_role_used=false`; action `commit`; no heavy manual review loop. | No overhead regression. |

Observed positive gain:

- Treatment explicitly stated why multi-role was not needed.

Observed negative gain:

- None observed. It kept review cost below the saved 6 hours/week.

## Overall Judgment

The A/B evidence supports keeping the change with its current boundary:

- In non-trivial cases, multi-role pressure gives positive incremental value by making
  challenge points and timing risks more explicit.
- In lightweight deterministic or reversible cases, the current rules do not force
  multi-role overhead.
- No negative behavior was observed in this run: no unnecessary role ceremony, no
  over-conservatism, and no final decision degradation.

Important calibration:

- The positive gain is incremental, not dramatic. Baseline EDSP and SELA were already
  capable in these examples.
- The "no negative" claim is limited to these four scenarios. Future tests should keep
  checking whether multi-role is skipped for low-risk work.
