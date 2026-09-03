#!/usr/bin/env python3
"""Run the preregistered Bidirectional Steelman Convergence experiment.

This is a research harness, not Stable Mindthus runtime. It reuses the existing Codex
CLI execution helper but owns a separate fixture, treatment compiler, blind judge
schema, and summary. Generation never receives case rubrics or expected behavior.

Recommended isolation:
- A/C/D: a CODEX_HOME containing the current Stable Mindthus plugin.
- B: a clean baseline CODEX_HOME without Mindthus installed.
- judge: a separate clean CODEX_HOME.

Use --dry-run first to inspect compiled prompts without calling a model.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES = ROOT / "tests" / "bidirectional_steelman_cases.jsonl"
BENCHMARK_RUNNER = ROOT / "scripts" / "run-judgment-benchmark-cli.py"

DIMENSIONS = (
    "frame_lock",
    "steelman_symmetry",
    "counter_position_quality",
    "third_frame_escape",
    "decisive_discriminator",
    "information_gain_move",
    "question_discipline",
    "verdict_commitment",
    "overturn_condition",
    "negative_control_sleep",
)

DIMENSION_GUIDANCE = {
    "frame_lock": "Competing claims are compared on the same judgment object, situated decision context when relevant, and evidence ceiling.",
    "steelman_symmetry": "Both materially relevant positions are strengthened; the losing side is not reduced to a strawman or a list of objections.",
    "counter_position_quality": "The strongest relevant competing explanation is present and could genuinely win if better supported.",
    "third_frame_escape": "A malformed or non-exhaustive A/B can be rejected or reframed rather than polished as an exhaustive binary.",
    "decisive_discriminator": "The answer identifies a fact, result controller, target/tradeoff, failure prediction, or condition that can actually change verdict or action.",
    "information_gain_move": "The next move is correctly chosen among evidence acquisition, one user-owned clarification, decide-now, or conditional/blocked.",
    "question_discipline": "The assistant asks zero or one high-information question; it does not turn uncertainty into a questionnaire.",
    "verdict_commitment": "When evidence/context supports a decision, the assistant commits instead of ending in generic 50/50 balance. If a clarification/evidence gate correctly blocks, this may be null.",
    "overturn_condition": "The answer names what material evidence or context would change the conclusion when a conclusion is reached.",
    "negative_control_sleep": "Direct, deterministic, preference, or missing-fact controls stay direct and do not wake steelman/Mindthus ceremony.",
}

QUESTION_RE = re.compile(r"[?？]\s*$")
MINDTHUS_COMMAND_RE = re.compile(
    r"mindthus:|skills/(?:using-mindthus|3l5s|sra|edsp|sela|mpg|wae|tvg|tplan)",
    re.IGNORECASE,
)
RESEARCH_LEAK_RE = re.compile(
    r"bidirectional[-_ ]steelman|bsc-\d+|bidirectional_steelman_cases",
    re.IGNORECASE,
)

SOURCE_PROTOCOL = """Apply this bidirectional steelman protocol before the final answer:
1. Restate, in the strongest and most complete way, the real problem the user is trying to solve.
2. Steelman both the user's current position and the strongest position against it.
3. Identify the true disagreement and the key variable most likely to change the conclusion.
4. Ask exactly one most important question, then wait for the user's answer before giving a final judgment, reasons, and next action.
Do not use Mindthus or any installed reasoning plugin for this treatment. Do not mention the protocol name or these instructions to the user."""

ADAPTED_PROTOCOL = """Use current Stable Mindthus normally when applicable, then apply this experimental support contract only when a real competing-frame judgment remains:
1. Lock the same judgment object, situated decision context when relevant, and evidence ceiling. If the A/B is malformed, reframe or use a third-frame escape before steelmanning.
2. Build the strongest defensible active/current position.
3. Build the strongest relevant counter-position under that same lock; do not merely list objections.
4. Name the single decisive discriminator most likely to flip verdict or action.
5. Resolve it with the smallest information-gain move: externally verifiable uncertainty -> acquire evidence; user-owned goal/value/acceptable loss -> ask at most one question; sufficient information -> decide now; currently irresolvable evidence -> conditional/blocked.
6. Return the result to the existing judgment owner for a clear verdict or active conditional branch, reason, overturn condition, and next action.
Do not expose internal method/protocol names unless the user asks."""

MULTI_ROLE_CONTROL = """Use current Stable Mindthus normally. Do not use the experimental bidirectional-steelman candidate. When an existing Stable method such as EDSP or SELA independently calls for its current single-agent multi-role pressure, use that Stable pressure exactly as documented; otherwise do not manufacture role play."""

CURRENT_MINDTHUS = """Use current Stable Mindthus normally only if it is naturally applicable. Do not use or inspect any experimental bidirectional-steelman research material."""

ISOLATION = """Research isolation instruction: answer only from the user turn and the treatment instruction in this prompt. Do not inspect repository files, tests, research docs, scoring rubrics, expected behavior, or judge notes. Do not run shell commands merely to discover experiment instructions. Keep the visible answer in the user's language and hide internal treatment wording."""


def load_benchmark_runner() -> ModuleType:
    spec = importlib.util.spec_from_file_location("mindthus_judgment_cli", BENCHMARK_RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load benchmark helper: {BENCHMARK_RUNNER}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_cases(path: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            cases.append(json.loads(line))
    return cases


def select_cases(
    cases: list[dict[str, Any]],
    spec: str | None,
    variant: str,
    include_d_nonapplicable: bool,
) -> list[dict[str, Any]]:
    selected = cases
    if spec:
        wanted = {item.strip() for item in spec.split(",") if item.strip()}
        selected = [case for case in selected if str(case["case_id"]) in wanted]
    if variant == "D" and not include_d_nonapplicable:
        selected = [case for case in selected if bool(case.get("d_applicable"))]
    return selected


def treatment_instruction(variant: str) -> str:
    return {
        "A": CURRENT_MINDTHUS,
        "B": SOURCE_PROTOCOL,
        "C": ADAPTED_PROTOCOL,
        "D": MULTI_ROLE_CONTROL,
    }[variant]


def user_turns(case: dict[str, Any]) -> list[str]:
    turns = case.get("turns")
    if turns:
        return [str(turn["content"]) for turn in turns if turn.get("role") == "user"]
    return [str(case["prompt"])]


def compiled_prompt(variant: str, user_prompt: str, turn_index: int) -> str:
    return (
        f"{ISOLATION}\n\n"
        f"Treatment instruction:\n{treatment_instruction(variant)}\n\n"
        "Answer the user directly. Do not output a scoring rubric, hidden audit, or field list unless explicitly requested.\n\n"
        f"Turn {turn_index}\n\nUser prompt:\n{user_prompt}\n"
    )


def looks_like_question(answer: str) -> bool:
    stripped = answer.rstrip()
    if QUESTION_RE.search(stripped):
        return True
    tail = stripped[-240:]
    return any(
        marker in tail
        for marker in ("我只问一个问题", "最关键的问题", "请告诉我", "你更", "你最")
    )


def prepare_out_dir(out_dir: Path) -> None:
    for name in (
        "answers",
        "events",
        "stderr",
        "prompts",
        "judge-answers",
        "judge-events",
        "judge-stderr",
        "judge-prompts",
        "records",
    ):
        (out_dir / name).mkdir(parents=True, exist_ok=True)


def case_home(
    empty_home_root: Path | None,
    variant: str,
    case_id: str,
    *,
    judge: bool = False,
) -> Path | None:
    if empty_home_root is None:
        return None
    role = f"judge-{variant.lower()}" if judge else f"variant-{variant.lower()}"
    return empty_home_root / role / case_id


def reset_case_home(home: Path | None, force: bool) -> None:
    if home is None:
        return
    if home.exists() and any(home.iterdir()):
        if not force:
            raise RuntimeError(f"experiment HOME is not empty: {home}; use a fresh root or --force")
        shutil.rmtree(home)
    home.mkdir(parents=True, exist_ok=True)


def command_contamination(variant: str, commands: list[str]) -> list[str]:
    findings: list[str] = []
    for command in commands:
        if RESEARCH_LEAK_RE.search(command):
            findings.append(f"research-leak:{command}")
        if variant == "B" and MINDTHUS_COMMAND_RE.search(command):
            findings.append(f"source-protocol-mindthus-contamination:{command}")
    return findings


def run_generation_case(
    case: dict[str, Any],
    args: argparse.Namespace,
    helper: ModuleType,
    out_dir: Path,
) -> dict[str, Any]:
    case_id = str(case["case_id"])
    record_path = out_dir / "records" / f"{case_id}.json"
    if record_path.exists() and not args.force:
        return json.loads(record_path.read_text(encoding="utf-8"))

    turns = user_turns(case)
    compiled: list[str] = []
    results: list[dict[str, Any]] = []
    thread_id: str | None = None
    persist = len(turns) > 1 or bool(case.get("continuation_reply"))
    home = case_home(
        Path(args.empty_home_root) if args.empty_home_root else None,
        args.variant,
        case_id,
    )
    if not args.dry_run:
        reset_case_home(home, args.force)

    for idx, user_prompt in enumerate(turns, 1):
        prompt = compiled_prompt(args.variant, user_prompt, idx)
        compiled.append(prompt)
        if args.dry_run:
            (out_dir / "prompts" / f"{case_id}-turn-{idx}.prompt.txt").write_text(
                prompt,
                encoding="utf-8",
            )
            continue
        result = helper.run_codex(
            prompt,
            out_dir,
            f"{case_id}-turn-{idx}",
            Path(args.codex_home),
            ROOT,
            Path(args.execution_root),
            args.model,
            args.timeout,
            home=home,
            resume_thread_id=thread_id if idx > 1 else None,
            persist_session=persist,
        )
        result["user_prompt"] = user_prompt
        results.append(result)
        thread_id = result.get("thread_id")
        if result.get("returncode") != 0:
            break

    if (
        not args.dry_run
        and args.auto_followup
        and len(turns) == 1
        and results
        and case.get("continuation_reply")
        and looks_like_question(str(results[-1].get("answer", "")))
    ):
        user_prompt = str(case["continuation_reply"])
        idx = 2
        prompt = compiled_prompt(args.variant, user_prompt, idx)
        compiled.append(prompt)
        result = helper.run_codex(
            prompt,
            out_dir,
            f"{case_id}-turn-{idx}",
            Path(args.codex_home),
            ROOT,
            Path(args.execution_root),
            args.model,
            args.timeout,
            home=home,
            resume_thread_id=thread_id,
            persist_session=True,
        )
        result["user_prompt"] = user_prompt
        result["fixture_auto_followup"] = True
        results.append(result)
        thread_id = result.get("thread_id")

    commands = [
        str(command)
        for result in results
        for command in result.get("loaded_commands", [])
    ]
    usage = [result.get("usage") for result in results if result.get("usage")]
    duration = sum(float(result.get("duration_seconds", 0.0)) for result in results)
    record = {
        "schema_version": "mindthus-bidirectional-steelman-response-v0.1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "variant": args.variant,
        "case_id": case_id,
        "case_type": case["case_type"],
        "title": case["title"],
        "dry_run": bool(args.dry_run),
        "compiled_prompts": compiled if args.dry_run else [],
        "fixture_continuation_reply": case.get("continuation_reply") if args.dry_run else None,
        "turns": results,
        "final_answer": results[-1].get("answer", "") if results else "",
        "returncode": results[-1].get("returncode", 0) if results else 0,
        "loaded_commands": commands,
        "contamination_flags": command_contamination(args.variant, commands),
        "usage": usage,
        "duration_seconds": round(duration, 3),
    }
    record_path.write_text(
        json.dumps(record, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return record


def write_judge_schema(path: Path) -> None:
    score_or_null = {"type": ["integer", "null"], "minimum": 0, "maximum": 2}
    schema = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "case_id",
            "behavioral_pass",
            "hard_fail_observed",
            "question_count_observed",
            "dimensions",
            "rationale",
        ],
        "properties": {
            "case_id": {"type": "string"},
            "behavioral_pass": {"type": "boolean"},
            "hard_fail_observed": {"type": "boolean"},
            "question_count_observed": {"type": "integer", "minimum": 0},
            "dimensions": {
                "type": "object",
                "additionalProperties": False,
                "required": list(DIMENSIONS),
                "properties": {name: score_or_null for name in DIMENSIONS},
            },
            "rationale": {"type": "string"},
        },
    }
    path.write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")


def blind_judge_prompt(case: dict[str, Any], record: dict[str, Any]) -> str:
    transcript: list[str] = []
    for idx, turn in enumerate(record.get("turns", []), 1):
        transcript.append(f"User turn {idx}:\n{turn.get('user_prompt', '')}")
        transcript.append(f"Assistant turn {idx}:\n{turn.get('answer', '')}")
    transcript_text = "\n\n".join(transcript)
    guidance = "\n".join(
        f"- {name}: {DIMENSION_GUIDANCE[name]}" for name in DIMENSIONS
    )
    return (
        "Blind research judge instruction: judge only the transcript and rubric below. Do not infer or guess which treatment produced it. "
        "Do not inspect repository files, experiment outputs, or variant names. Return JSON only matching the supplied schema. "
        "Use 0=failed, 1=partial, 2=strong for applicable dimensions and null when genuinely not applicable. "
        "For negative controls, negative_control_sleep is the primary dimension and method ceremony should count against behavioral_pass.\n\n"
        f"case_id: {case['case_id']}\n"
        f"case_type: {case['case_type']}\n"
        f"title: {case['title']}\n"
        f"expected_behavior: {case['expected_behavior']}\n"
        f"hard_fail: {case['hard_fail']}\n\n"
        f"Dimension guidance:\n{guidance}\n\n"
        f"Transcript:\n{transcript_text}\n"
    )


def validate_judge_output(data: dict[str, Any], case_id: str) -> None:
    if data.get("case_id") != case_id:
        raise ValueError(f"judge case_id mismatch: {data.get('case_id')} != {case_id}")
    if not isinstance(data.get("behavioral_pass"), bool):
        raise ValueError("judge behavioral_pass must be bool")
    if not isinstance(data.get("hard_fail_observed"), bool):
        raise ValueError("judge hard_fail_observed must be bool")
    if not isinstance(data.get("question_count_observed"), int):
        raise ValueError("judge question_count_observed must be int")
    dims = data.get("dimensions")
    if not isinstance(dims, dict) or set(dims) != set(DIMENSIONS):
        raise ValueError("judge dimensions mismatch")
    for name, value in dims.items():
        if value is not None and value not in {0, 1, 2}:
            raise ValueError(f"invalid score for {name}: {value}")
    if not isinstance(data.get("rationale"), str):
        raise ValueError("judge rationale must be string")


def run_judge_case(
    case: dict[str, Any],
    record: dict[str, Any],
    args: argparse.Namespace,
    helper: ModuleType,
    out_dir: Path,
    schema_path: Path,
) -> dict[str, Any]:
    case_id = str(case["case_id"])
    if record.get("dry_run"):
        raise ValueError("cannot judge a dry-run record")
    judge_home_root = (
        Path(args.judge_empty_home_root)
        if args.judge_empty_home_root
        else None
    )
    home = case_home(judge_home_root, args.variant, case_id, judge=True)
    reset_case_home(home, args.force)
    result = helper.run_codex(
        blind_judge_prompt(case, record),
        out_dir,
        case_id,
        Path(args.judge_codex_home),
        ROOT,
        Path(args.execution_root),
        args.judge_model,
        args.timeout,
        home=home,
        output_schema=schema_path,
    )
    if result.get("returncode") != 0:
        raise RuntimeError(f"judge failed for {case_id}: {result.get('answer')}")
    parsed = json.loads(
        Path(result["last_message_path"]).read_text(encoding="utf-8")
    )
    validate_judge_output(parsed, case_id)
    parsed["judge_duration_seconds"] = result.get("duration_seconds")
    parsed["judge_usage"] = result.get("usage")
    return parsed


def usage_total(records: list[dict[str, Any]], key: str) -> int:
    total = 0
    for record in records:
        for usage in record.get("usage", []):
            value = usage.get(key) if isinstance(usage, dict) else None
            if isinstance(value, int):
                total += value
    return total


def summarize(
    records: list[dict[str, Any]],
    scores: list[dict[str, Any]],
) -> dict[str, Any]:
    score_by_case = {score["case_id"]: score for score in scores}
    applicable_values: list[int] = []
    positive_passes = 0
    positive_total = 0
    negative_sleep_values: list[int] = []
    hard_fail_cases: list[str] = []
    for record in records:
        score = score_by_case.get(record["case_id"])
        if not score:
            continue
        if record["case_type"] == "positive":
            positive_total += 1
            positive_passes += int(bool(score.get("behavioral_pass")))
        if score.get("hard_fail_observed"):
            hard_fail_cases.append(record["case_id"])
        for name, value in score.get("dimensions", {}).items():
            if value is not None:
                applicable_values.append(int(value))
            if (
                name == "negative_control_sleep"
                and value is not None
                and record["case_type"] == "negative_control"
            ):
                negative_sleep_values.append(int(value))
    return {
        "schema_version": "mindthus-bidirectional-steelman-summary-v0.1",
        "variant": records[0]["variant"] if records else None,
        "case_count": len(records),
        "judged_case_count": len(scores),
        "positive_behavioral_pass_rate": (
            round(positive_passes / positive_total, 3) if positive_total else None
        ),
        "mean_applicable_dimension_score_0_to_2": (
            round(sum(applicable_values) / len(applicable_values), 3)
            if applicable_values
            else None
        ),
        "negative_control_sleep_mean_0_to_2": (
            round(sum(negative_sleep_values) / len(negative_sleep_values), 3)
            if negative_sleep_values
            else None
        ),
        "hard_fail_cases": hard_fail_cases,
        "contaminated_cases": [
            record["case_id"]
            for record in records
            if record.get("contamination_flags")
        ],
        "generation_duration_seconds": round(
            sum(float(record.get("duration_seconds", 0.0)) for record in records),
            3,
        ),
        "generation_input_tokens": usage_total(records, "input_tokens"),
        "generation_output_tokens": usage_total(records, "output_tokens"),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant", choices=("A", "B", "C", "D"), required=True)
    parser.add_argument("--cases", default=str(DEFAULT_CASES))
    parser.add_argument(
        "--case-ids",
        help="Comma-separated case ids, e.g. bsc-001,bsc-002",
    )
    parser.add_argument("--out-dir", required=True)
    parser.add_argument(
        "--phase",
        choices=("generate", "judge", "all"),
        default="generate",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compile prompts and records without calling Codex",
    )
    parser.add_argument(
        "--auto-followup",
        action="store_true",
        help="If a single-turn case has continuation_reply and the answer asks a question, send the preregistered fixture reply",
    )
    parser.add_argument(
        "--include-d-nonapplicable",
        action="store_true",
        help="Run D on cases not preregistered as existing multi-role controls",
    )
    parser.add_argument("--codex-home")
    parser.add_argument("--judge-codex-home")
    parser.add_argument("--empty-home-root")
    parser.add_argument("--judge-empty-home-root")
    parser.add_argument("--execution-root", default=str(ROOT))
    parser.add_argument("--model")
    parser.add_argument("--judge-model")
    parser.add_argument("--timeout", type=int, default=420)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = Path(args.out_dir)
    prepare_out_dir(out_dir)
    cases = select_cases(
        load_cases(Path(args.cases)),
        args.case_ids,
        args.variant,
        args.include_d_nonapplicable,
    )
    if not cases:
        raise SystemExit("no cases selected")
    case_by_id = {str(case["case_id"]): case for case in cases}
    helper = load_benchmark_runner()

    if (
        args.phase in {"generate", "all"}
        and not args.dry_run
        and not args.codex_home
    ):
        raise SystemExit(
            "--codex-home is required for generation unless --dry-run is used"
        )
    if (
        args.phase in {"judge", "all"}
        and not args.dry_run
        and not args.judge_codex_home
    ):
        raise SystemExit("--judge-codex-home is required for judge/all phase")

    records: list[dict[str, Any]] = []
    if args.phase in {"generate", "all"}:
        for case in cases:
            records.append(run_generation_case(case, args, helper, out_dir))
        (out_dir / "responses.jsonl").write_text(
            "".join(
                json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
                for record in records
            ),
            encoding="utf-8",
        )
    else:
        for case_id in case_by_id:
            path = out_dir / "records" / f"{case_id}.json"
            if not path.exists():
                raise SystemExit(
                    f"missing generation record for judge phase: {path}"
                )
            records.append(json.loads(path.read_text(encoding="utf-8")))

    scores: list[dict[str, Any]] = []
    if args.phase in {"judge", "all"} and not args.dry_run:
        schema_path = out_dir / "judge-schema.json"
        write_judge_schema(schema_path)
        for record in records:
            case = case_by_id[record["case_id"]]
            scores.append(
                run_judge_case(case, record, args, helper, out_dir, schema_path)
            )
        (out_dir / "scores.jsonl").write_text(
            "".join(
                json.dumps(score, ensure_ascii=False, sort_keys=True) + "\n"
                for score in scores
            ),
            encoding="utf-8",
        )

    summary = summarize(records, scores)
    summary["dry_run"] = bool(args.dry_run)
    summary["phase"] = args.phase
    summary["cases_file"] = str(Path(args.cases))
    summary["auto_followup"] = bool(args.auto_followup)
    (out_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
