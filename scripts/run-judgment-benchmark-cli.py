#!/usr/bin/env python3
"""Run the 50-case judgment benchmark through Codex CLI and grade the outputs.

The generator phase intentionally hides pass criteria and fail signals from the
answering model. The judge phase sees the rubric after raw answers are recorded.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES = ROOT / "tests" / "judgment_benchmark_50_cases.jsonl"


ISOLATION_INSTRUCTION = (
    "Benchmark isolation instruction: do not use Superpowers skills, do not read "
    "/Users/william/.codex/superpowers, and do not run any shell command unless "
    "absolutely necessary. Use only the installed Mindthus plugin routing context "
    "if it is naturally applicable; otherwise answer directly. Do not inspect the "
    "benchmark fixture, benchmark docs, pass criteria, fail signals, or judge notes. "
    "Do not mention this isolation instruction."
)

BASELINE_ISOLATION_INSTRUCTION = (
    "Benchmark isolation instruction: do not use Superpowers skills, do not read "
    "/Users/william/.codex/superpowers, and do not run any shell command unless "
    "absolutely necessary. Answer directly using normal model reasoning. Do not "
    "inspect benchmark fixtures, benchmark docs, pass criteria, fail signals, or "
    "judge notes. Do not mention this isolation instruction."
)

JUDGE_ISOLATION_INSTRUCTION = (
    "Benchmark judge isolation instruction: do not use Superpowers skills, do not "
    "read /Users/william/.codex/superpowers, and do not run any shell command "
    "unless absolutely necessary. Do not inspect benchmark fixture files or docs; "
    "use only the rubric and transcript included in this prompt. Do not mention "
    "this isolation instruction."
)


def isolation_instruction(plugin_context: str) -> str:
    if plugin_context == "none":
        return BASELINE_ISOLATION_INSTRUCTION
    return ISOLATION_INSTRUCTION


def load_cases(path: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            cases.append(json.loads(line))
    return cases


def selected_cases(cases: list[dict[str, Any]], spec: str | None) -> list[dict[str, Any]]:
    if not spec:
        return cases
    wanted: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start, end = part.split("-", 1)
            wanted.update(range(int(start), int(end) + 1))
        else:
            wanted.add(int(part))
    return [case for case in cases if int(case["case_number"]) in wanted]


def ensure_dirs(out_dir: Path) -> None:
    for name in (
        "events",
        "stderr",
        "answers",
        "prompts",
        "judge-events",
        "judge-stderr",
        "judge-answers",
        "judge-prompts",
    ):
        (out_dir / name).mkdir(parents=True, exist_ok=True)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def command_text(args: list[str]) -> str:
    proc = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)
    return proc.stdout.strip() if proc.returncode == 0 else ""


def run_codex(
    prompt: str,
    out_dir: Path,
    stem: str,
    codex_home: Path,
    repo_root: Path,
    execution_root: Path,
    model: str | None,
    timeout: int,
    *,
    resume_thread_id: str | None = None,
    persist_session: bool = False,
    output_schema: Path | None = None,
) -> dict[str, Any]:
    env = os.environ.copy()
    env["CODEX_HOME"] = str(codex_home)

    last_path = out_dir / "answers" / f"{stem}.txt"
    events_path = out_dir / "events" / f"{stem}.jsonl"
    stderr_path = out_dir / "stderr" / f"{stem}.stderr.txt"
    if output_schema is not None:
        last_path = out_dir / "judge-answers" / f"{stem}.json"
        events_path = out_dir / "judge-events" / f"{stem}.jsonl"
        stderr_path = out_dir / "judge-stderr" / f"{stem}.stderr.txt"
        prompt_path = out_dir / "judge-prompts" / f"{stem}.prompt.txt"
    else:
        prompt_path = out_dir / "prompts" / f"{stem}.prompt.txt"

    if resume_thread_id:
        cmd = ["codex", "exec", "resume", "--json", "-o", str(last_path)]
        if model:
            cmd.extend(["--model", model])
        if output_schema is not None:
            cmd.extend(["--output-schema", str(output_schema)])
        cmd.extend([resume_thread_id, "-"])
    else:
        cmd = [
            "codex",
            "exec",
            "--json",
            "--ignore-rules",
            "--skip-git-repo-check",
            "-C",
            str(execution_root),
            "-s",
            "read-only",
            "-o",
            str(last_path),
        ]
        if not persist_session:
            cmd.append("--ephemeral")
        if model:
            cmd.extend(["--model", model])
        if output_schema is not None:
            cmd.extend(["--output-schema", str(output_schema)])
        cmd.append("-")

    started = time.time()
    prompt_path.write_text(prompt, encoding="utf-8")
    timed_out = False
    timeout_message = ""
    try:
        proc = subprocess.run(
            cmd,
            input=prompt,
            text=True,
            capture_output=True,
            env=env,
            timeout=timeout,
            check=False,
        )
        stdout = proc.stdout
        stderr = proc.stderr
        returncode = proc.returncode
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        timeout_message = f"codex command timed out after {timeout} seconds"
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + "\n" + timeout_message
        returncode = 124
    duration = time.time() - started
    events_path.write_text(stdout, encoding="utf-8")
    stderr_path.write_text(stderr, encoding="utf-8")
    answer = last_path.read_text(encoding="utf-8") if last_path.is_file() else ""
    if timed_out and not answer:
        answer = timeout_message
        last_path.write_text(answer, encoding="utf-8")

    thread_id = None
    loaded_commands: list[str] = []
    agent_messages: list[str] = []
    usage: dict[str, Any] | None = None
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "thread.started":
            thread_id = event.get("thread_id")
        item = event.get("item") or {}
        if item.get("type") == "command_execution":
            loaded_commands.append(str(item.get("command", "")))
        if item.get("type") == "agent_message":
            agent_messages.append(str(item.get("text", "")))
        if event.get("type") == "turn.completed":
            usage = event.get("usage")
    contamination_flags = [
        command
        for command in loaded_commands
        if re.search(r"superpowers|judgment_benchmark_50_cases|docs/benchmarks|pass_criteria|fail_signal", command)
    ]

    return {
        "command": cmd,
        "returncode": returncode,
        "timed_out": timed_out,
        "duration_seconds": round(duration, 3),
        "thread_id": thread_id or resume_thread_id,
        "answer": answer,
        "events_path": str(events_path),
        "stderr_path": str(stderr_path),
        "last_message_path": str(last_path),
        "prompt_path": str(prompt_path),
        "loaded_commands": loaded_commands,
        "contamination_flags": contamination_flags,
        "agent_messages": agent_messages,
        "usage": usage,
    }


def user_turns(
    case: dict[str, Any],
    prior_case_answers: dict[str, str] | None = None,
) -> list[str]:
    prior_case_answers = prior_case_answers or {}
    turns = case.get("turns")
    if not turns:
        return [str(case["prompt"])]
    prompts: list[str] = []
    context_lines: list[str] = []
    prior_assistant_message: str | None = None
    for turn in turns:
        role = turn.get("role")
        content = str(turn.get("content", ""))
        if role == "context":
            context_lines.append(content)
        elif role == "assistant_setup":
            prior_assistant_message = content
        elif role == "assistant_generated":
            if "mtj-048" in content:
                prior_assistant_message = prior_case_answers.get("mtj-048", content)
            elif "prior turn" in content:
                prior_assistant_message = "{{prior_turn_answer}}"
            else:
                prior_assistant_message = content
        elif role == "user":
            parts: list[str] = []
            if context_lines:
                parts.append("Context for this turn:\n" + "\n".join(context_lines))
                context_lines = []
            if prior_assistant_message:
                parts.append("Prior assistant message:\n" + prior_assistant_message)
                prior_assistant_message = None
            parts.append("User prompt:\n" + content)
            prompts.append("\n\n".join(parts))
    return prompts or [str(case["prompt"])]


def generator_prompt(user_prompt: str, turn_index: int, instruction: str) -> str:
    return (
        f"{instruction}\n\n"
        "You are answering one user-facing benchmark turn. Answer the user directly "
        "in the user's language. Hide internal audit, method names, scoring rubrics, "
        "and field lists unless the user explicitly asks for them. Keep the answer "
        "concise but sufficient.\n\n"
        f"Turn {turn_index}\n\n"
        f"User prompt:\n{user_prompt}\n"
    )


def run_case(
    case: dict[str, Any],
    args: argparse.Namespace,
    prior_case_answers: dict[str, str] | None = None,
) -> dict[str, Any]:
    case_id = str(case["case_id"])
    out_dir = Path(args.out_dir)
    answer_record_path = out_dir / "answers" / f"{case_id}.record.json"
    if answer_record_path.exists() and not args.force:
        return json.loads(answer_record_path.read_text(encoding="utf-8"))

    prompts = user_turns(case, prior_case_answers=prior_case_answers)
    thread_id = None
    turn_records: list[dict[str, Any]] = []
    persist = len(prompts) > 1
    prior_turn_answer = ""
    for idx, prompt in enumerate(prompts, 1):
        prompt = prompt.replace("{{prior_turn_answer}}", prior_turn_answer)
        result = run_codex(
            generator_prompt(prompt, idx, isolation_instruction(args.plugin_context)),
            out_dir,
            f"{case_id}-turn-{idx}",
            Path(args.codex_home),
            Path(args.repo_root),
            Path(args.execution_root),
            args.model,
            args.timeout,
            resume_thread_id=thread_id if idx > 1 else None,
            persist_session=persist,
        )
        thread_id = result["thread_id"]
        result["user_prompt"] = prompt
        turn_records.append(result)
        prior_turn_answer = result["answer"]
        if result["returncode"] != 0:
            break

    record = {
        "schema_version": "mindthus-judgment-cli-response-v0.1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "variant": args.variant,
        "case_id": case_id,
        "case_number": case["case_number"],
        "group_id": case["group_id"],
        "group_name": case["group_name"],
        "case_type": case["case_type"],
        "multi_turn": case["multi_turn"],
        "thread_id": thread_id,
        "turns": turn_records,
        "final_answer": turn_records[-1]["answer"] if turn_records else "",
        "returncode": turn_records[-1]["returncode"] if turn_records else 1,
        "loaded_commands_all_turns": [
            command for turn in turn_records for command in turn.get("loaded_commands", [])
        ],
        "contamination_flags_all_turns": [
            command for turn in turn_records for command in turn.get("contamination_flags", [])
        ],
    }
    answer_record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return record


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def judge_schema(path: Path) -> None:
    schema = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "case_id",
            "score",
            "pass_criteria_met",
            "fail_signal_observed",
            "positive_wakeup_observed",
            "first_sentence_lock",
            "verdict_commitment_anti_mush",
            "over_forced_verdict",
            "rationale",
        ],
        "properties": {
            "case_id": {"type": "string"},
            "score": {"type": "integer", "minimum": 0, "maximum": 2},
            "pass_criteria_met": {"type": "boolean"},
            "fail_signal_observed": {"type": "boolean"},
            "positive_wakeup_observed": {"type": ["boolean", "null"]},
            "first_sentence_lock": {"type": ["boolean", "null"]},
            "verdict_commitment_anti_mush": {"type": ["boolean", "null"]},
            "over_forced_verdict": {"type": ["boolean", "null"]},
            "rationale": {"type": "string"},
        },
    }
    path.write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")


def validate_judge_output(parsed: dict[str, Any], expected_case_id: str) -> dict[str, Any]:
    required = {
        "case_id": str,
        "score": int,
        "pass_criteria_met": bool,
        "fail_signal_observed": bool,
        "rationale": str,
    }
    for key, expected_type in required.items():
        if key not in parsed:
            raise ValueError(f"judge output missing {key}")
        if not isinstance(parsed[key], expected_type):
            raise ValueError(f"judge output field {key} has wrong type")
    if parsed["case_id"] != expected_case_id:
        raise ValueError(f"judge output case_id {parsed['case_id']} != {expected_case_id}")
    if parsed["score"] not in {0, 1, 2}:
        raise ValueError("judge score must be 0, 1, or 2")
    for key in (
        "positive_wakeup_observed",
        "first_sentence_lock",
        "verdict_commitment_anti_mush",
        "over_forced_verdict",
    ):
        if key not in parsed:
            raise ValueError(f"judge output missing {key}")
        if parsed[key] is not None and not isinstance(parsed[key], bool):
            raise ValueError(f"judge output field {key} must be bool or null")
    allowed = set(required) | {
        "positive_wakeup_observed",
        "first_sentence_lock",
        "verdict_commitment_anti_mush",
        "over_forced_verdict",
    }
    extra = set(parsed) - allowed
    if extra:
        raise ValueError(f"judge output has unexpected fields: {sorted(extra)}")
    return parsed


def judge_prompt(case: dict[str, Any], response: dict[str, Any]) -> str:
    transcript_parts: list[str] = []
    for idx, turn in enumerate(response.get("turns", []), 1):
        transcript_parts.append(f"User turn {idx}:\n{turn.get('user_prompt', '')}")
        transcript_parts.append(f"Assistant turn {idx}:\n{turn.get('answer', '')}")
    transcript = "\n\n".join(transcript_parts)
    return (
        f"{JUDGE_ISOLATION_INSTRUCTION}\n\n"
        "You are a blind benchmark judge. The answer generator did not see the rubric; "
        "you may use it now. Return JSON only matching the supplied schema. Score 0/1/2. "
        "For negative_control cases, the score scale is reversed as described in score_scale: "
        "direct/stay-asleep behavior earns 2 and over-methodized behavior earns 0.\n\n"
        f"case_id: {case['case_id']}\n"
        f"case_type: {case['case_type']}\n"
        f"group_id: {case['group_id']}\n"
        f"expected_owner: {case['expected_owner']}\n"
        f"positive_wakeup_expected: {case['positive_wakeup_expected']}\n"
        f"stay_asleep_expected: {case['stay_asleep_expected']}\n"
        f"score_scale: {case['score_scale']}\n"
        f"pass_criteria: {case['pass_criteria']}\n"
        f"fail_signal: {case['fail_signal']}\n\n"
        f"Canonical single-line prompt:\n{case['prompt']}\n\n"
        f"Full executed transcript:\n{transcript}\n"
    )


def judge_case(
    case: dict[str, Any],
    response: dict[str, Any],
    args: argparse.Namespace,
    schema_path: Path,
) -> dict[str, Any]:
    case_id = str(case["case_id"])
    out_dir = Path(args.out_dir)
    score_path = out_dir / "judge-answers" / f"{case_id}.record.json"
    if score_path.exists() and not args.force:
        return json.loads(score_path.read_text(encoding="utf-8"))

    result = run_codex(
        judge_prompt(case, response),
        out_dir,
        f"{case_id}-judge",
        Path(args.codex_home),
        Path(args.repo_root),
        Path(args.execution_root),
        args.judge_model or args.model,
        args.timeout,
        output_schema=schema_path,
    )
    try:
        parsed = json.loads(result["answer"])
        parsed = validate_judge_output(parsed, case_id)
    except json.JSONDecodeError:
        parsed = {
            "case_id": case_id,
            "score": 0,
            "pass_criteria_met": False,
            "fail_signal_observed": True,
            "positive_wakeup_observed": None,
            "first_sentence_lock": None,
            "verdict_commitment_anti_mush": None,
            "over_forced_verdict": None,
            "rationale": "Judge did not return parseable JSON.",
        }
    except ValueError as exc:
        parsed = {
            "case_id": case_id,
            "score": 0,
            "pass_criteria_met": False,
            "fail_signal_observed": True,
            "positive_wakeup_observed": None,
            "first_sentence_lock": None,
            "verdict_commitment_anti_mush": None,
            "over_forced_verdict": None,
            "rationale": f"Judge output failed local validation: {exc}",
        }
    record = {
        **parsed,
        "schema_version": "mindthus-judgment-cli-score-v0.1",
        "judged_at_utc": datetime.now(timezone.utc).isoformat(),
        "variant": args.variant,
        "case_id": case_id,
        "case_number": case["case_number"],
        "group_id": case["group_id"],
        "group_name": case["group_name"],
        "case_type": case["case_type"],
        "judge_returncode": result["returncode"],
        "judge_usage": result.get("usage"),
    }
    score_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return record


def summarize(scores: list[dict[str, Any]]) -> dict[str, Any]:
    positive = [s for s in scores if s["case_type"] != "negative_control"]
    negative = [s for s in scores if s["case_type"] == "negative_control"]
    first_lock = [s for s in scores if s.get("first_sentence_lock") is not None]
    anti_mush = [s for s in scores if s.get("verdict_commitment_anti_mush") is not None]
    over_forced = [s for s in scores if s.get("over_forced_verdict") is not None]
    h_group = [s for s in scores if s["group_id"] == "H"]

    def avg(items: list[dict[str, Any]]) -> float | None:
        return round(sum(int(s["score"]) for s in items) / len(items), 3) if items else None

    def rate(items: list[dict[str, Any]], key: str, *, positive_value: bool = True) -> float | None:
        if not items:
            return None
        return round(sum(1 for s in items if s.get(key) is positive_value) / len(items), 3)

    false_wakes = [
        s for s in negative if bool(s.get("positive_wakeup_observed")) or int(s.get("score", 0)) == 0
    ]
    return {
        "schema_version": "mindthus-judgment-cli-summary-v0.1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "case_count": len(scores),
        "positive_count": len(positive),
        "negative_control_count": len(negative),
        "positive_mean": avg(positive),
        "overall_mean": avg(scores),
        "negative_false_wakeup_rate": round(len(false_wakes) / len(negative), 3) if negative else None,
        "first_sentence_lock_rate": rate(first_lock, "first_sentence_lock"),
        "verdict_commitment_anti_mush_rate": rate(anti_mush, "verdict_commitment_anti_mush"),
        "over_forced_verdict_rate": rate(over_forced, "over_forced_verdict"),
        "h_group_brake_rate": rate(h_group, "pass_criteria_met"),
        "score_histogram": {str(i): sum(1 for s in scores if int(s["score"]) == i) for i in (0, 1, 2)},
        "failed_cases": [
            {
                "case_id": s["case_id"],
                "case_number": s["case_number"],
                "score": s["score"],
                "rationale": s.get("rationale", ""),
            }
            for s in scores
            if int(s["score"]) < 2
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--codex-home", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--execution-root", type=Path, default=Path("/tmp/mindthus-benchmark-workspace"))
    parser.add_argument("--variant", default="baseline+Mindthus-hotfix")
    parser.add_argument("--plugin-context", choices=("mindthus", "none"), default="mindthus")
    parser.add_argument("--model", default=None)
    parser.add_argument("--judge-model", default=None)
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--jobs", type=int, default=3)
    parser.add_argument("--select", default=None, help="Case numbers, e.g. 1-10,12,50.")
    parser.add_argument("--phase", choices=("generate", "judge", "all"), default="all")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    ensure_dirs(args.out_dir)
    all_cases = load_cases(args.cases)
    cases = selected_cases(all_cases, args.select)
    case_by_id = {case["case_id"]: case for case in cases}
    all_case_by_id = {case["case_id"]: case for case in all_cases}

    manifest = {
        "schema_version": "mindthus-judgment-cli-run-manifest-v0.1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "variant": args.variant,
        "case_fixture": str(args.cases),
        "case_fixture_sha256": sha256_file(args.cases),
        "runner": str(Path(__file__).resolve()),
        "runner_sha256": sha256_file(Path(__file__).resolve()),
        "git_commit": command_text(["git", "rev-parse", "HEAD"]),
        "git_exact_tag": command_text(["git", "describe", "--tags", "--exact-match", "HEAD"]),
        "codex_cli_version": command_text(["codex", "--version"]),
        "case_count": len(cases),
        "codex_home": str(args.codex_home),
        "repo_root": str(args.repo_root),
        "execution_root": str(args.execution_root),
        "model": args.model,
        "judge_model": args.judge_model or args.model,
        "jobs": args.jobs,
        "timeout": args.timeout,
        "plugin_context": args.plugin_context,
        "generator_isolation_instruction": isolation_instruction(args.plugin_context),
        "judge_isolation_instruction": JUDGE_ISOLATION_INSTRUCTION,
    }
    (args.out_dir / "run-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    args.execution_root.mkdir(parents=True, exist_ok=True)

    responses: list[dict[str, Any]] = []
    if args.phase in {"generate", "all"}:
        prior_case_answers: dict[str, str] = {}
        remaining_cases = list(cases)
        if any(case["case_id"] == "mtj-050" for case in cases):
            dependency = all_case_by_id["mtj-048"]
            dependency_record = run_case(dependency, args, prior_case_answers)
            prior_case_answers["mtj-048"] = dependency_record["final_answer"]
            if dependency["case_id"] in case_by_id:
                responses.append(dependency_record)
                remaining_cases = [case for case in remaining_cases if case["case_id"] != "mtj-048"]
            else:
                dependency_path = args.out_dir / "answers" / "mtj-050-dependency-mtj-048.record.json"
                dependency_path.write_text(
                    json.dumps(dependency_record, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
            futures = [
                pool.submit(run_case, case, args, prior_case_answers)
                for case in remaining_cases
            ]
            for future in concurrent.futures.as_completed(futures):
                record = future.result()
                responses.append(record)
                print(f"generated {record['case_id']} rc={record['returncode']}", flush=True)
        responses.sort(key=lambda item: int(item["case_number"]))
        write_jsonl(args.out_dir / "raw-responses.jsonl", responses)
    else:
        for path in sorted((args.out_dir / "answers").glob("mtj-*.record.json")):
            record = json.loads(path.read_text(encoding="utf-8"))
            if record["case_id"] in case_by_id:
                responses.append(record)
        responses.sort(key=lambda item: int(item["case_number"]))

    if args.phase in {"judge", "all"}:
        schema_path = args.out_dir / "judge-output-schema.json"
        judge_schema(schema_path)
        response_by_case = {record["case_id"]: record for record in responses}
        judge_inputs = [case for case in cases if case["case_id"] in response_by_case]
        scores: list[dict[str, Any]] = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
            futures = [
                pool.submit(judge_case, case, response_by_case[case["case_id"]], args, schema_path)
                for case in judge_inputs
            ]
            for future in concurrent.futures.as_completed(futures):
                record = future.result()
                scores.append(record)
                print(f"judged {record['case_id']} score={record['score']}", flush=True)
        scores.sort(key=lambda item: int(item["case_number"]))
        write_jsonl(args.out_dir / "score-records.jsonl", scores)
        summary = summarize(scores)
        (args.out_dir / "summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(json.dumps(summary, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
