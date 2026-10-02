"""One offline TVG tabletop: injected judgments/text, never a model dispatcher.

Reuses C02 planning/recheck consumption; native and host calls are explicit imagined
workflows. This measures their structural call counts, not accuracy, tokens or price.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))
from experiments.typed_decision import c02
from experiments.typed_decision.contracts import DecisionResult, digest

CONTRACT_PATH = REPO / "docs/internal/research/typed-decision/review-remediation/c02-contract-v2.json"
PROFILE_PATH = REPO / "skills/tvg/resources/value-profiles/plain-sharp-skill-intro.md"
TVG_PATH = REPO / "skills/tvg/SKILL.md"
GAP = "TVG帮助全面、系统地优化任何问题，并自动判断最终结果是否正确。"
ADEQUATE = (
    "TVG把看似完整却不好用的产物，改到能支撑实际判断和行动。"
    "比如一份计划只有步骤，没有取舍理由，就补上理由和边界。"
    "它不替你验证事实，也不接管整项战略。"
)
UNNECESSARY_REWRITE = ADEQUATE + "它保证每次修改都提高质量。"
PLAN = "限定为一个既有产物；补上实际用途与例子，删除自动判真和适用任何问题的夸大。"


class TabletopSession:
    """Only injected DecisionResults; no Provider, credentials, journal or network."""
    root = Path("/offline-tabletop-not-a-live-root")

    def __init__(self):
        self.steps = []
        self.injected = {}

    def step(self, engine, role, response, **extra):
        self.steps.append({"sequence": len(self.steps) + 1, "engine": engine,
                           "role": role, "response": response,
                           "provenance": "hand_authored_simulation", **extra})

    def evaluate(self, questions, state):
        answers = {}
        for spec in questions:
            value = self.injected[spec.id]
            result = DecisionResult(status="ok", value=value, reason="offline_injected")
            result.validate(spec)
            answers[spec.id] = result
        self.step("jev", "recheck" if questions[0].id.startswith("recheck") else "local_check",
                  {key: answer.value for key, answer in answers.items()},
                  question_contracts=[spec.to_dict() for spec in questions],
                  state=state, native_probabilities=None)
        return answers

    def finish(self, graph, data, result):
        return {"run_id": digest({"graph": graph, "data": data}), "result": result}


def replay(name, mode, artifact, observed, contract, profile, tvg):
    session = TabletopSession()
    context = {
        "artifact": artifact, "source_ref": "synthetic-tabletop:" + digest(artifact),
        "target": {"source_ref": "owner-tabletop-task-v1",
                   "purpose": "首次读者能判断TVG做什么、何时有用及什么不由它负责。",
                   "standard": "按固定Plain Sharp Profile改这一段简介；用途和边界正确，足够好的稿子可保留。"},
        "evidence": [{"source_ref": "skills/tvg/SKILL.md", "text": tvg}],
        "veto_constraints": ["不得把TVG写成事实认证或全项目战略决定器；不得编造效果保证。"],
        "tvg_contract": tvg + "\n固定Profile：\n" + profile,
        "freshness": "current",
        "permission": {"mode": "advisory", "scope": "one_synthetic_text_module"},
    }
    route = None
    final = ADEQUATE
    if mode == "native":
        session.step("llm", "check_and_repair_or_keep_with_inline_self_review", final,
                     state=context)
    else:
        session.injected = observed
        route = c02.plan(session, context, contract)
        assert route["result"]["exit_state"] is None
        if mode == "split_interpretation":
            session.step("llm", "interpret_judgment_and_write_plan", PLAN,
                         consumes=route["result"])
        if mode == "split_unresolved":
            session.step("llm", "resolve_semantic_uncertainty_and_write_plan", PLAN,
                         consumes=route["result"])
        if route["result"]["route"] == "rewrite_candidate":
            generated = UNNECESSARY_REWRITE if mode == "false_positive" else ADEQUATE
            session.step("llm", "repair_and_inline_self_review", generated,
                         consumes=route["result"])
            if mode in {"separate_exit", "false_positive"}:
                parent = {"context_sha256": digest(context), "contract_sha256": digest(contract),
                          "artifact": generated, "artifact_sha256": digest(generated)}
                session.injected = {"recheck_utility": "adequate", "recheck_fidelity":
                                    "violation" if mode == "false_positive" else "faithful"}
                # Read interception only; no synthetic generation evidence in any live journal.
                with patch.object(c02, "read_record", return_value=parent):
                    route = c02.recheck(session, route, context, contract)
                assert route["result"]["route"] == "original_exit_owner"
                assert route["result"]["exit_state"] is None
                session.step("llm", "owner_review_return_original" if mode == "false_positive"
                             else "owner_review_in_separate_invocation", final,
                             consumes=route["result"])
            else:
                session.step("inline_owner_responsibility", "no_additional_invocation", None,
                             note="低风险下同一次宿主处理承担责任；不由Jev自动批准退出。")
        else:
            session.step("llm", "original_owner_check_and_repair_or_keep", final,
                         consumes=route["result"])
    llm = sum(step["engine"] == "llm" for step in session.steps)
    jev = sum(step["engine"] == "jev" for step in session.steps)
    return {"name": name, "mode": mode, "input": context,
            "injected_judgments": observed, "steps": session.steps,
            "last_c02_result": route, "simulated_final": final,
            "planned_llm_calls": llm, "planned_jev_calls": jev,
            "planned_serial_edges": max(llm + jev - 1, 0),
            "measured_model_seconds": None, "measured_model_tokens": None,
            "measured_model_cost": None, "semantic_quality_verified": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    contract = json.loads(CONTRACT_PATH.read_text())
    profile, tvg = PROFILE_PATH.read_text(), TVG_PATH.read_text()
    gap = {"utility": "deficit", "support": "sufficient", "action": "explain_tradeoff"}
    adequate = {"utility": "adequate", "support": "sufficient", "action": "leave_unchanged"}
    unclear = {"utility": "unclear", "support": "sufficient", "action": "abstain"}
    variants = [
        ("gap_native", "native", GAP, {}, (1, 0)),
        ("gap_jev_inline_owner", "compact", GAP, gap, (1, 1)),
        ("gap_jev_extra_interpreter", "split_interpretation", GAP, gap, (2, 1)),
        ("gap_jev_separate_owner", "separate_exit", GAP, gap, (2, 2)),
        ("adequate_native", "native", ADEQUATE, {}, (1, 0)),
        ("adequate_jev_owner_wakeup", "compact", ADEQUATE, adequate, (1, 1)),
        ("gap_jev_unclear_direct_fallback", "compact", GAP, unclear, (1, 1)),
        ("gap_jev_unclear_extra_resolver", "split_unresolved", GAP, unclear, (2, 1)),
        ("adequate_jev_false_positive", "false_positive", ADEQUATE, gap, (2, 2)),
    ]
    runs = []
    for name, mode, artifact, observations, expected in variants:
        run = replay(name, mode, artifact, observations, contract, profile, tvg)
        assert (run["planned_llm_calls"], run["planned_jev_calls"]) == expected, name
        assert run["simulated_final"] == ADEQUATE, name
        runs.append(run)
    report = {"schema": "mindthus.tvg.call-boundary-tabletop.v1", "simulation_only": True,
              "live_import_allowed": False, "actual_model_calls": 0,
              "claim_ceiling": "Injected workflow replay, not Jev or LLM ability/cost evidence",
              "source_sha256": {str(p.relative_to(REPO)): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in (CONTRACT_PATH, PROFILE_PATH, TVG_PATH, REPO / "experiments/typed_decision/c02.py")},
              "runs": runs}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("OFFLINE ONLY: actual_model_calls=0; injected variants=9")
    for run in runs:
        print(f"{run['name']}: planned LLM={run['planned_llm_calls']} Jev={run['planned_jev_calls']} "
              f"serial_edges={run['planned_serial_edges']}")
    print("9 variants passed call-count/output checks; injected text equality is not quality verification.")


if __name__ == "__main__":
    main()
