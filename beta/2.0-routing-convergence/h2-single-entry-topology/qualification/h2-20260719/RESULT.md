# H2 Single-entry Qualification Result

Terminal H2 outcome: `H2_REJECTED`

Mission consequence: `STOP_2X_EXPLORATION`

Candidate commit `9c271c1f3fb86f1e81f4860d32d9e5ac4f08b59c` passed all static
gates and three responsibility-separated reviews. Q1 then passed the frozen Decision
Context criterion. Q2 triggered two independent hard failures, so Q3-Q7, Stable
comparison, and Judge were not run.

## Q1 — pass

The host injected and the model read only the packaged thin entry. It read no index or
owner, gave no continue/hold/stop posture, and ended with one answer-changing blocking
question. Usage was 28,091 input + 404 output = 28,495 counted tokens.

The model also exposed one same-turn sentence saying it was using the Mindthus workflow.
This was recorded as a usability defect, but it did not add a user interaction round and
was not the stopping failure.

## Q2 — hard failure

Q2 resumed the exact Q1 thread UUID, but the resumed process reported the repository
worktree as its current directory. It inspected project `AGENTS.md`, Stable source
Skills, methodology documents, H2 source files, and finally the packaged MPG resource.
The observed answer therefore cannot prove isolated candidate routing or a clean
entry -> index -> resource lifecycle.

The completed call reported 204,951 input + 5,062 output = 210,013 counted tokens. This
exceeds the frozen per-call authorization ceiling of 200,000. The pre-registered runbook
maps that event directly to `H2_REJECTED` then `STOP_2X_EXPLORATION`, with no rerun.

## Usage

| Phase | Calls | Input | Output | Counted |
| --- | ---: | ---: | ---: | ---: |
| Q1 | 1 | 28,091 | 404 | 28,495 |
| Q2 | 1 | 204,951 | 5,062 | 210,013 |
| **H2 total** | **2** | **233,042** | **5,466** | **238,508** |

No Judge ran. Five H2 qualification calls were not consumed.

## Claim ceiling

Static evidence proves that one discoverable entry plus seven locked resource-owner
trees can be packaged without Hook, AGENTS injection, defaultPrompt, second Skill, or
reference atlas. Q1 proves first-turn entry activation and Decision Context behavior in
the tested host lifecycle.

The evidence does not prove same-session H2 routing, owner fidelity, passive coverage,
Stable-relative quality, loaded-byte savings, uncached-token savings, or usability.
It also does not prove that the abstract topology is impossible on every future host.
It proves that this final authorized H2 candidate did not qualify under the frozen Codex
conditions and cannot support a continue conclusion.

Raw host JSONL, stderr, final answers, plugin inventory, static diagnostic, hashes, and
preflight are under `evidence/`.
