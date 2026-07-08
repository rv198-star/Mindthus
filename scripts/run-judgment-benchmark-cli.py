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
V5_TARGET_TRIGGER_REGISTER = ROOT / "docs" / "benchmarks" / "v5-target-trigger-register.json"
CONTAMINATION_RE = re.compile(
    r"superpowers|judgment_benchmark_50_cases|docs/benchmarks|pass_criteria|fail_signal|judge notes",
    re.IGNORECASE,
)
SUPERPOWERS_RE = re.compile(r"superpowers", re.IGNORECASE)
FORCED_MINDTHUS_RE = re.compile(r"\$mindthus:|mindthus:", re.IGNORECASE)
MINDTHUS_SKILL_RE = re.compile(
    r"(?:mindthus:|skills/)(using-mindthus|3l5s|edsp|sela|mpg|wae|tvg|tplan)(?:/SKILL\.md)?",
    re.IGNORECASE,
)

DIRECT_EXPECTED_OWNERS = {
    "clarification",
    "direct_answer",
    "direct_debugging",
    "direct_execution",
    "direct_judgment",
    "evidence_review",
    "information_acquisition",
    "release_review",
}

OWNER_ACCEPTED_SKILLS = {
    "input_framing_audit": {"using-mindthus"},
    "whole_elephant": {"using-mindthus"},
    "edsp": {"edsp"},
    "sela": {"sela"},
    "sela_boundary": {"sela"},
    "mpg": {"mpg"},
    "wae": {"wae"},
    "tvg": {"tvg"},
    "anti_spiral": {"using-mindthus", "3l5s", "tplan"},
    "decision_context_calibration": {"using-mindthus", "edsp"},
    "aspect_arbitration": {"using-mindthus"},
    "expression_discipline": {"using-mindthus"},
    "approximate_quantified_mapping": {"using-mindthus", "mpg"},
}


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


def load_v5_target_trigger_register(path: Path | None = None) -> dict[str, Any]:
    register_path = path or V5_TARGET_TRIGGER_REGISTER
    return json.loads(register_path.read_text(encoding="utf-8"))


def v5_register_entry_for_case(case: dict[str, Any]) -> dict[str, Any] | None:
    case_number = int(case.get("case_number", -1))
    case_id = str(case.get("case_id", ""))
    for entry in load_v5_target_trigger_register().get("cases", []):
        if int(entry.get("case_number", -1)) == case_number and str(entry.get("case_id")) == case_id:
            return entry
    return None


def v5_register_hint_for_case(case: dict[str, Any], *, enabled: bool) -> str | None:
    if not enabled:
        return None
    entry = v5_register_entry_for_case(case)
    if not entry:
        return None
    preferred_owner = str(entry.get("preferred_runtime_owner") or "")
    if not preferred_owner:
        owners = entry.get("accepted_runtime_owners") or []
        preferred_owner = str(owners[0]) if owners else "using-mindthus"
    return (
        "Host diagnostic activation hint (non-certifying; do not mention this hint): "
        f"registered target anchor = {entry.get('target_anchor')}; "
        f"route through mindthus:{preferred_owner}; "
        f"required visible action = {entry.get('required_action_probe')}; "
        f"negative boundary = {entry.get('negative_boundary')}."
    )


def v5_target_activation_diagnostics(scores: list[dict[str, Any]]) -> dict[str, Any]:
    register = load_v5_target_trigger_register()
    registered_cases = {
        int(case["case_number"]): case
        for case in register.get("cases", [])
    }
    scores_by_number: dict[int, dict[str, Any]] = {}
    case_id_mismatch_numbers: list[int] = []
    for score in scores:
        if "case_number" not in score:
            continue
        number = int(score["case_number"])
        if number not in registered_cases:
            continue
        registered = registered_cases[number]
        if str(score.get("case_id")) != str(registered.get("case_id")):
            case_id_mismatch_numbers.append(number)
            continue
        scores_by_number[number] = score
    selected_numbers = sorted(scores_by_number)
    missing_numbers = sorted(set(registered_cases) - set(selected_numbers))
    case_diagnostics: list[dict[str, Any]] = []
    no_load_numbers: list[int] = []
    wrong_owner_numbers: list[int] = []
    expected_loaded_numbers: list[int] = []
    required_action_numbers: list[int] = []

    for number in selected_numbers:
        registered = registered_cases[number]
        score = scores_by_number[number]
        loaded_owner = score.get("loaded_owner") or []
        if isinstance(loaded_owner, str):
            loaded_owner = [loaded_owner]
        accepted_owners = set(str(owner) for owner in registered.get("accepted_runtime_owners", []))
        superpowers_loaded = bool(score.get("superpowers_loaded"))
        if any(owner in accepted_owners for owner in loaded_owner):
            register_expected_loaded = True
            register_verdict = "expected_owner_loaded"
        elif loaded_owner or superpowers_loaded:
            register_expected_loaded = False
            register_verdict = "wrong_owner_loaded"
        else:
            register_expected_loaded = False
            register_verdict = "no_load"

        if register_verdict == "no_load":
            no_load_numbers.append(number)
        if register_verdict == "wrong_owner_loaded":
            wrong_owner_numbers.append(number)
        if register_expected_loaded is True:
            expected_loaded_numbers.append(number)
        if score.get("required_visible_action_present") is True:
            required_action_numbers.append(number)

        case_diagnostics.append(
            {
                "case_number": number,
                "case_id": registered.get("case_id"),
                "target_anchor": registered.get("target_anchor"),
                "expected_owner": registered.get("expected_owner"),
                "accepted_runtime_owners": registered.get("accepted_runtime_owners", []),
                "required_action_probe": registered.get("required_action_probe"),
                "negative_boundary": registered.get("negative_boundary"),
                "loaded_owner": loaded_owner,
                "expected_owner_loaded": score.get("expected_owner_loaded"),
                "register_expected_owner_loaded": register_expected_loaded,
                "required_visible_action_present": score.get("required_visible_action_present"),
                "owner_fidelity_verdict": score.get("owner_fidelity_verdict"),
                "register_owner_fidelity_verdict": register_verdict,
            }
        )

    return {
        "schema_version": "mindthus-v5-target-activation-diagnostics-v0.1",
        "register_schema_version": register.get("schema_version"),
        "registered_case_count": len(registered_cases),
        "selected_registered_case_count": len(selected_numbers),
        "registered_case_numbers": sorted(registered_cases),
        "selected_registered_case_numbers": selected_numbers,
        "not_selected_registered_case_numbers": missing_numbers,
        "case_id_mismatch_case_numbers": sorted(set(case_id_mismatch_numbers)),
        "expected_owner_loaded_rate": (
            round(len(expected_loaded_numbers) / len(selected_numbers), 3)
            if selected_numbers
            else None
        ),
        "expected_owner_loaded_case_numbers": expected_loaded_numbers,
        "no_load_case_numbers": no_load_numbers,
        "wrong_owner_case_numbers": wrong_owner_numbers,
        "required_visible_action_case_numbers": required_action_numbers,
        "case_diagnostics": case_diagnostics,
    }


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


def contamination_flags_for(loaded_commands: list[str]) -> list[str]:
    return [command for command in loaded_commands if CONTAMINATION_RE.search(command)]


def loaded_owners_from_commands(loaded_commands: list[str]) -> list[str]:
    owners: list[str] = []
    for command in loaded_commands:
        for match in MINDTHUS_SKILL_RE.finditer(str(command)):
            owner = match.group(1).lower()
            if owner not in owners:
                owners.append(owner)
    return owners


def mindthus_loaded_from_commands(loaded_commands: list[str]) -> bool:
    return bool(loaded_owners_from_commands(loaded_commands))


def home_for_stem(args: argparse.Namespace, stem: str) -> Path | None:
    explicit_home = getattr(args, "home", None)
    empty_home_root = getattr(args, "empty_home_root", None)
    if explicit_home and empty_home_root:
        raise ValueError("--home and --empty-home-root cannot be used together")
    if explicit_home:
        home = Path(explicit_home)
        home.mkdir(parents=True, exist_ok=True)
        return home
    if empty_home_root:
        home = Path(empty_home_root) / stem
        if home.exists() and any(home.iterdir()):
            raise RuntimeError(f"empty HOME directory is not empty: {home}")
        home.mkdir(parents=True, exist_ok=True)
        return home
    return None


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
    home: Path | None = None,
    resume_thread_id: str | None = None,
    persist_session: bool = False,
    output_schema: Path | None = None,
) -> dict[str, Any]:
    env = os.environ.copy()
    env["CODEX_HOME"] = str(codex_home)
    if home is not None:
        home.mkdir(parents=True, exist_ok=True)
        env["HOME"] = str(home)

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
    contamination_flags = contamination_flags_for(loaded_commands)

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
        "home": str(home) if home is not None else None,
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


def generator_prompt(
    user_prompt: str,
    turn_index: int,
    instruction: str,
    activation_hint: str | None = None,
) -> str:
    hint_block = f"\n\n{activation_hint}" if activation_hint else ""
    return (
        f"{instruction}\n\n"
        "You are answering one user-facing benchmark turn. Answer the user directly "
        "in the user's language. Hide internal audit, method names, scoring rubrics, "
        "and field lists unless the user explicitly asks for them. Keep the answer "
        "concise but sufficient."
        f"{hint_block}\n\n"
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
        activation_hint = v5_register_hint_for_case(
            case,
            enabled=bool(getattr(args, "v5_register_hints", False)) and idx == 1,
        )
        result = run_codex(
            generator_prompt(
                prompt,
                idx,
                isolation_instruction(args.plugin_context),
                activation_hint=activation_hint,
            ),
            out_dir,
            f"{case_id}-turn-{idx}",
            Path(args.codex_home),
            Path(args.repo_root),
            Path(args.execution_root),
            args.model,
            args.timeout,
            home=home_for_stem(args, f"{case_id}-turn-{idx}"),
            resume_thread_id=thread_id if idx > 1 else None,
            persist_session=persist,
        )
        thread_id = result["thread_id"]
        result["user_prompt"] = prompt
        result["activation_hint"] = activation_hint
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
        "activation_hint_applied": any(turn.get("activation_hint") for turn in turn_records),
        "activation_hints_all_turns": [
            str(turn.get("activation_hint"))
            for turn in turn_records
            if turn.get("activation_hint")
        ],
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


def expected_owner_skills(case: dict[str, Any]) -> set[str]:
    if bool(case.get("stay_asleep_expected")):
        return set()
    owner = str(case.get("expected_owner", ""))
    if owner in DIRECT_EXPECTED_OWNERS:
        return set()
    if owner in OWNER_ACCEPTED_SKILLS:
        return set(OWNER_ACCEPTED_SKILLS[owner])
    if owner in {"using-mindthus", "3l5s", "edsp", "sela", "mpg", "wae", "tvg", "tplan"}:
        return {owner}
    return set()


def final_answer_false_wakeup(case: dict[str, Any], score: dict[str, Any]) -> bool:
    if not bool(case.get("stay_asleep_expected")):
        return False
    return bool(score.get("positive_wakeup_observed")) or int(score.get("score", 0)) == 0


def runtime_event_false_wakeup(
    case: dict[str, Any],
    *,
    mindthus_loaded: bool,
    superpowers_loaded: bool,
) -> bool:
    if not bool(case.get("stay_asleep_expected")):
        return False
    return mindthus_loaded or superpowers_loaded


def owner_fidelity_for_case(
    case: dict[str, Any],
    response: dict[str, Any],
    score: dict[str, Any],
) -> dict[str, Any]:
    commands = [str(command) for command in response.get("loaded_commands_all_turns", [])]
    loaded_owner = loaded_owners_from_commands(commands)
    mindthus_loaded = bool(loaded_owner)
    superpowers_loaded = any(SUPERPOWERS_RE.search(command) for command in commands)
    accepted_owners = sorted(expected_owner_skills(case))
    stay_asleep = bool(case.get("stay_asleep_expected"))
    expected_owner = str(case.get("expected_owner", ""))

    false_final = final_answer_false_wakeup(case, score)
    false_runtime = runtime_event_false_wakeup(
        case,
        mindthus_loaded=mindthus_loaded,
        superpowers_loaded=superpowers_loaded,
    )
    required_visible_action_present = (
        bool(score.get("pass_criteria_met")) if not stay_asleep else None
    )

    if stay_asleep or expected_owner in DIRECT_EXPECTED_OWNERS:
        expected_owner_loaded = not mindthus_loaded and not superpowers_loaded
        verdict = "runtime_over_wake" if false_runtime else "direct_stay_asleep"
    elif not accepted_owners:
        expected_owner_loaded = None
        verdict = "unknown_expected_owner"
    elif any(owner in accepted_owners for owner in loaded_owner):
        expected_owner_loaded = True
        verdict = "expected_owner_loaded"
    elif mindthus_loaded or superpowers_loaded:
        expected_owner_loaded = False
        verdict = "wrong_owner_loaded"
    else:
        expected_owner_loaded = False
        verdict = "no_load"

    return {
        "expected_owner": expected_owner,
        "accepted_loaded_owners": accepted_owners,
        "loaded_owner": loaded_owner,
        "mindthus_loaded": mindthus_loaded,
        "superpowers_loaded": superpowers_loaded,
        "false_wakeup_final_answer": false_final,
        "false_wakeup_runtime_event": false_runtime,
        "expected_owner_loaded": expected_owner_loaded,
        "required_visible_action_present": required_visible_action_present,
        "owner_fidelity_verdict": verdict,
    }


def augment_score_with_telemetry(
    case: dict[str, Any],
    response: dict[str, Any],
    score: dict[str, Any],
) -> dict[str, Any]:
    return {**score, **owner_fidelity_for_case(case, response, score)}


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
        cached = json.loads(score_path.read_text(encoding="utf-8"))
        cached["cached_judge_reused"] = True
        return augment_score_with_telemetry(case, response, cached)

    result = run_codex(
        judge_prompt(case, response),
        out_dir,
        f"{case_id}-judge",
        Path(args.codex_home),
        Path(args.repo_root),
        Path(args.execution_root),
        args.judge_model or args.model,
        args.timeout,
        home=home_for_stem(args, f"{case_id}-judge"),
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
        "schema_version": "mindthus-judgment-cli-score-v0.2",
        "judged_at_utc": datetime.now(timezone.utc).isoformat(),
        "variant": args.variant,
        "case_id": case_id,
        "case_number": case["case_number"],
        "group_id": case["group_id"],
        "group_name": case["group_name"],
        "case_type": case["case_type"],
        "judge_returncode": result["returncode"],
        "judge_usage": result.get("usage"),
        "judge_loaded_commands": result.get("loaded_commands", []),
        "judge_contamination_flags": result.get("contamination_flags", []),
        "cached_judge_reused": False,
    }
    record = augment_score_with_telemetry(case, response, record)
    score_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return record


def activation_summary(responses: list[dict[str, Any]]) -> dict[str, Any]:
    case_summaries: list[dict[str, Any]] = []
    for response in responses:
        commands = [str(command) for command in response.get("loaded_commands_all_turns", [])]
        prompt_text = "\n".join(str(turn.get("user_prompt", "")) for turn in response.get("turns", []))
        mindthus_loaded = mindthus_loaded_from_commands(commands)
        superpowers_loaded = any(SUPERPOWERS_RE.search(command) for command in commands)
        forced_mindthus_prompt = bool(FORCED_MINDTHUS_RE.search(prompt_text))
        activation_hint_applied = bool(response.get("activation_hint_applied")) or any(
            turn.get("activation_hint") for turn in response.get("turns", [])
        )
        loaded_owner = loaded_owners_from_commands(commands)
        case_summaries.append(
            {
                "case_id": response.get("case_id"),
                "case_number": response.get("case_number"),
                "mindthus_loaded": mindthus_loaded,
                "superpowers_loaded": superpowers_loaded,
                "loaded_owner": loaded_owner,
                "no_commands_loaded": not commands,
                "forced_mindthus_prompt": forced_mindthus_prompt,
                "activation_hint_applied": activation_hint_applied,
                "natural_mindthus_loaded": (
                    mindthus_loaded and not forced_mindthus_prompt and not activation_hint_applied
                ),
                "contaminated": bool(response.get("contamination_flags_all_turns")),
            }
        )

    def count(key: str) -> int:
        return sum(1 for item in case_summaries if item[key])

    case_count = len(case_summaries)
    return {
        "schema_version": "mindthus-judgment-cli-activation-summary-v0.2",
        "case_count": case_count,
        "mindthus_loaded_count": count("mindthus_loaded"),
        "superpowers_loaded_count": count("superpowers_loaded"),
        "no_commands_loaded_count": count("no_commands_loaded"),
        "natural_mindthus_loaded_count": count("natural_mindthus_loaded"),
        "forced_mindthus_prompt_count": count("forced_mindthus_prompt"),
        "activation_hint_applied_count": count("activation_hint_applied"),
        "contaminated_case_count": count("contaminated"),
        "mindthus_loaded_rate": round(count("mindthus_loaded") / case_count, 3) if case_count else None,
        "superpowers_loaded_rate": round(count("superpowers_loaded") / case_count, 3) if case_count else None,
        "no_commands_loaded_rate": round(count("no_commands_loaded") / case_count, 3) if case_count else None,
        "case_summaries": case_summaries,
    }


def contamination_report(
    responses: list[dict[str, Any]],
    scores: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    generator_cases = [
        {
            "case_id": response.get("case_id"),
            "case_number": response.get("case_number"),
            "contamination_flags_all_turns": response.get("contamination_flags_all_turns", []),
        }
        for response in responses
        if response.get("contamination_flags_all_turns")
    ]
    judge_cases = [
        {
            "case_id": score.get("case_id"),
            "case_number": score.get("case_number"),
            "judge_contamination_flags": score.get("judge_contamination_flags", []),
        }
        for score in scores or []
        if score.get("judge_contamination_flags")
    ]
    return {
        "schema_version": "mindthus-judgment-cli-contamination-report-v0.1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "generator_contaminated_case_count": len(generator_cases),
        "judge_contaminated_case_count": len(judge_cases),
        "generator_cases": generator_cases,
        "judge_cases": judge_cases,
    }


def write_activation_summary(out_dir: Path, responses: list[dict[str, Any]]) -> dict[str, Any]:
    summary = activation_summary(responses)
    (out_dir / "activation-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return summary


def write_contamination_report(
    out_dir: Path,
    responses: list[dict[str, Any]],
    scores: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    report = contamination_report(responses, scores)
    (out_dir / "contamination-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return report


def failure_diagnostics(
    responses: list[dict[str, Any]],
    scores: list[dict[str, Any]],
) -> dict[str, Any]:
    response_by_case = {response.get("case_id"): response for response in responses}
    failed_cases: list[dict[str, Any]] = []
    for score in scores:
        if int(score.get("score", 0)) >= 2:
            continue
        response = response_by_case.get(score.get("case_id"), {})
        commands = [str(command) for command in response.get("loaded_commands_all_turns", [])]
        mindthus_loaded = mindthus_loaded_from_commands(commands)
        superpowers_loaded = any(SUPERPOWERS_RE.search(command) for command in commands)
        loaded_owner = score.get("loaded_owner")
        if loaded_owner is None:
            loaded_owner = loaded_owners_from_commands(commands)
        failed_cases.append(
            {
                "case_id": score.get("case_id"),
                "case_number": score.get("case_number"),
                "score": score.get("score"),
                "group_id": score.get("group_id"),
                "multi_turn": bool(response.get("multi_turn")),
                "mindthus_loaded": mindthus_loaded,
                "superpowers_loaded": superpowers_loaded,
                "loaded_owner": loaded_owner,
                "no_commands_loaded": not commands,
                "first_sentence_lock": score.get("first_sentence_lock"),
                "verdict_commitment_anti_mush": score.get("verdict_commitment_anti_mush"),
                "over_forced_verdict": score.get("over_forced_verdict"),
                "false_wakeup_final_answer": score.get("false_wakeup_final_answer"),
                "false_wakeup_runtime_event": score.get("false_wakeup_runtime_event"),
                "expected_owner_loaded": score.get("expected_owner_loaded"),
                "required_visible_action_present": score.get("required_visible_action_present"),
                "owner_fidelity_verdict": score.get("owner_fidelity_verdict"),
            }
        )

    def count(key: str) -> int:
        return sum(1 for item in failed_cases if item[key])

    return {
        "schema_version": "mindthus-judgment-cli-failure-diagnostics-v0.2",
        "failed_case_count": len(failed_cases),
        "mindthus_loaded_failed_case_count": count("mindthus_loaded"),
        "superpowers_loaded_failed_case_count": count("superpowers_loaded"),
        "no_commands_failed_case_count": count("no_commands_loaded"),
        "multi_turn_failed_case_count": count("multi_turn"),
        "failed_cases": failed_cases,
    }


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

    def final_false_wakeup_from_score(score: dict[str, Any]) -> bool:
        if "false_wakeup_final_answer" in score:
            return bool(score.get("false_wakeup_final_answer"))
        return bool(score.get("positive_wakeup_observed")) or int(score.get("score", 0)) == 0

    final_false_wakes = [s for s in negative if final_false_wakeup_from_score(s)]
    runtime_missing = [
        s for s in negative if s.get("false_wakeup_runtime_event") is None
    ]
    runtime_false_wakes = [s for s in negative if s.get("false_wakeup_runtime_event") is True]
    owner_items = [s for s in scores if s.get("expected_owner_loaded") is not None]
    positive_owner_items = [s for s in positive if s.get("expected_owner_loaded") is not None]
    negative_owner_items = [s for s in negative if s.get("expected_owner_loaded") is not None]
    action_items = [s for s in scores if s.get("required_visible_action_present") is not None]
    loaded_action_items = [
        s
        for s in positive
        if s.get("required_visible_action_present") is not None
        and (s.get("mindthus_loaded") is True or s.get("superpowers_loaded") is True)
    ]
    owner_fidelity_counts = {
        verdict: sum(1 for s in scores if s.get("owner_fidelity_verdict") == verdict)
        for verdict in sorted({str(s.get("owner_fidelity_verdict")) for s in scores if s.get("owner_fidelity_verdict")})
    }
    return {
        "schema_version": "mindthus-judgment-cli-summary-v0.2",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "case_count": len(scores),
        "positive_count": len(positive),
        "negative_control_count": len(negative),
        "positive_mean": avg(positive),
        "overall_mean": avg(scores),
        "negative_false_wakeup_rate": round(len(final_false_wakes) / len(negative), 3) if negative else None,
        "negative_false_wakeup_final_answer_rate": (
            round(len(final_false_wakes) / len(negative), 3) if negative else None
        ),
        "negative_false_wakeup_runtime_event_rate": (
            round(len(runtime_false_wakes) / len(negative), 3)
            if negative and not runtime_missing
            else None
        ),
        "runtime_event_telemetry_complete": not runtime_missing,
        "runtime_event_telemetry_missing_count": len(runtime_missing),
        "first_sentence_lock_rate": rate(first_lock, "first_sentence_lock"),
        "verdict_commitment_anti_mush_rate": rate(anti_mush, "verdict_commitment_anti_mush"),
        "over_forced_verdict_rate": rate(over_forced, "over_forced_verdict"),
        "h_group_brake_rate": rate(h_group, "pass_criteria_met"),
        "expected_owner_loaded_rate": rate(owner_items, "expected_owner_loaded"),
        "positive_expected_owner_loaded_rate": rate(positive_owner_items, "expected_owner_loaded"),
        "negative_runtime_stay_asleep_rate": rate(negative_owner_items, "expected_owner_loaded"),
        "required_visible_action_rate": rate(action_items, "required_visible_action_present"),
        "loaded_required_visible_action_rate": rate(
            loaded_action_items, "required_visible_action_present"
        ),
        "owner_fidelity_counts": owner_fidelity_counts,
        "v5_target_activation": v5_target_activation_diagnostics(scores),
        "score_histogram": {str(i): sum(1 for s in scores if int(s["score"]) == i) for i in (0, 1, 2)},
        "failed_cases": [
            {
                "case_id": s["case_id"],
                "case_number": s["case_number"],
                "score": s["score"],
                "owner_fidelity_verdict": s.get("owner_fidelity_verdict"),
                "rationale": s.get("rationale", ""),
            }
            for s in scores
            if int(s["score"]) < 2
        ],
    }


def validate_run_args(args: argparse.Namespace) -> list[str]:
    errors: list[str] = []
    if args.home and args.empty_home_root:
        errors.append("--home and --empty-home-root cannot be used together")
    if args.certification_candidate:
        if not args.model:
            errors.append("--certification-candidate requires explicit --model")
        if not args.judge_model:
            errors.append("--certification-candidate requires explicit --judge-model")
        if args.select:
            errors.append("--certification-candidate requires the full case set; omit --select")
        if args.reanalysis_of:
            errors.append("--certification-candidate cannot be combined with --reanalysis-of")
        if getattr(args, "v5_register_hints", False):
            errors.append("--certification-candidate cannot use --v5-register-hints")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--codex-home", type=Path, required=True)
    parser.add_argument("--home", type=Path, default=None, help="Set HOME for every Codex subprocess.")
    parser.add_argument(
        "--empty-home-root",
        type=Path,
        default=None,
        help="Create a separate empty HOME directory under this root for each Codex subprocess.",
    )
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
    parser.add_argument(
        "--certification-candidate",
        action="store_true",
        help="Mark this as a V5 certification candidate. Requires explicit models and the full case set.",
    )
    parser.add_argument(
        "--reanalysis-of",
        default=None,
        help="Identifier or path of the source run when reinterpreting archived artifacts.",
    )
    parser.add_argument(
        "--source-run-commit",
        default=None,
        help="Original source-run commit for diagnostic reanalysis artifacts.",
    )
    parser.add_argument(
        "--fail-on-contamination",
        action="store_true",
        help="Exit nonzero if a generator or judge subprocess loads forbidden benchmark or host-skill context.",
    )
    parser.add_argument(
        "--v5-register-hints",
        action="store_true",
        help="Diagnostic only: inject host-style V5 target register hints into registered target cases. Disallowed for certification candidates.",
    )
    args = parser.parse_args()
    errors = validate_run_args(args)
    if errors:
        parser.error("; ".join(errors))

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
        "home": str(args.home) if args.home else None,
        "empty_home_root": str(args.empty_home_root) if args.empty_home_root else None,
        "repo_root": str(args.repo_root),
        "execution_root": str(args.execution_root),
        "model": args.model,
        "judge_model": args.judge_model or args.model,
        "model_explicit": args.model is not None,
        "judge_model_explicit": args.judge_model is not None,
        "jobs": args.jobs,
        "timeout": args.timeout,
        "phase": args.phase,
        "force": args.force,
        "plugin_context": args.plugin_context,
        "fail_on_contamination": args.fail_on_contamination,
        "v5_register_hints": args.v5_register_hints,
        "v5_target_trigger_register": str(V5_TARGET_TRIGGER_REGISTER),
        "v5_target_trigger_register_sha256": sha256_file(V5_TARGET_TRIGGER_REGISTER),
        "certification_status": (
            "certification_candidate" if args.certification_candidate else "diagnostic"
        ),
        "certification_candidate_requested": args.certification_candidate,
        "reanalysis_of": args.reanalysis_of,
        "source_run_commit": args.source_run_commit,
        "cached_judge_reuse_allowed": not args.force,
        "contamination_patterns": CONTAMINATION_RE.pattern,
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
        write_activation_summary(args.out_dir, responses)
        if args.fail_on_contamination:
            report = write_contamination_report(args.out_dir, responses)
            if report["generator_contaminated_case_count"]:
                print(json.dumps(report, ensure_ascii=False, indent=2))
                return 2
    else:
        for path in sorted((args.out_dir / "answers").glob("mtj-*.record.json")):
            record = json.loads(path.read_text(encoding="utf-8"))
            if record["case_id"] in case_by_id:
                responses.append(record)
        responses.sort(key=lambda item: int(item["case_number"]))
        write_activation_summary(args.out_dir, responses)
        if args.fail_on_contamination:
            report = write_contamination_report(args.out_dir, responses)
            if report["generator_contaminated_case_count"]:
                print(json.dumps(report, ensure_ascii=False, indent=2))
                return 2

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
        cached_judge_reused_count = sum(1 for score in scores if score.get("cached_judge_reused"))
        summary["certification_status"] = manifest["certification_status"]
        summary["certification_candidate_requested"] = args.certification_candidate
        summary["model_explicit"] = manifest["model_explicit"]
        summary["judge_model_explicit"] = manifest["judge_model_explicit"]
        summary["run_phase"] = args.phase
        summary["reanalysis_of"] = args.reanalysis_of
        summary["source_run_commit"] = args.source_run_commit
        summary["cached_judge_reused_count"] = cached_judge_reused_count
        summary["certification_candidate_valid"] = (
            args.certification_candidate
            and cached_judge_reused_count == 0
            and summary.get("runtime_event_telemetry_complete") is True
        )
        summary["activation"] = activation_summary(responses)
        summary["failure_diagnostics"] = failure_diagnostics(responses, scores)
        (args.out_dir / "summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        if args.certification_candidate and cached_judge_reused_count:
            print(
                "certification candidate cannot reuse cached judge records; rerun with --force",
                flush=True,
            )
            return 2
        if args.fail_on_contamination:
            report = write_contamination_report(args.out_dir, responses, scores)
            if report["generator_contaminated_case_count"] or report["judge_contaminated_case_count"]:
                print(json.dumps(report, ensure_ascii=False, indent=2))
                return 2
        print(json.dumps(summary, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
