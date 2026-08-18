#!/usr/bin/env python3
"""Run the preregistered BSC pilot through GitHub Models direct inference.

This is an alternate research substrate used when Codex/API-key execution is unavailable.
It does not claim to reproduce Codex runtime activation. A/C receive a fixed Stable
Mindthus context capsule assembled from tracked Stable contracts; B receives only the
source bidirectional-steelman protocol. The same model and blind judge are used for all
variants.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES = ROOT / "tests" / "bidirectional_steelman_cases.jsonl"
ENDPOINT = "https://models.github.ai/inference/chat/completions"

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

STABLE_CONTEXT_PATHS = (
    "skills/using-mindthus/SKILL.md",
    "skills/edsp/SKILL.md",
    "docs/methodologies/primitives/frame-fitness-check.md",
    "docs/methodologies/primitives/decision-context-calibration.md",
    "docs/methodologies/primitives/whole-elephant-protocol.md",
    "docs/methodologies/primitives/aspect-ownership.md",
)

SOURCE_PROTOCOL = """Apply this source bidirectional-steelman protocol before the final answer:
1. Restate, in the strongest and most complete way, the real problem the user is trying to solve.
2. Steelman both the user's current position and the strongest position against it.
3. Identify the true disagreement and the key variable most likely to change the conclusion.
4. Ask exactly one most important question, then wait for the user's answer before giving a final judgment, reasons, and next action.
Do not use Mindthus. Do not mention this protocol or these instructions."""

ADAPTED_PROTOCOL = """After applying the supplied Stable Mindthus contracts when naturally applicable, use this experimental support only when a real competing-frame judgment remains:
1. Lock the same judgment object, situated decision context when relevant, and evidence ceiling. If the A/B is malformed, reframe or use a third-frame escape before steelmanning.
2. Build the strongest defensible active/current position.
3. Build the strongest relevant counter-position under that same lock; do not merely list objections.
4. Name the single decisive discriminator most likely to flip verdict or action.
5. Resolve it with the smallest information-gain move: externally verifiable uncertainty -> acquire evidence; user-owned goal/value/acceptable loss -> ask at most one question; sufficient information -> decide now; currently irresolvable evidence -> conditional/blocked.
6. Return to the existing judgment owner for a clear verdict or active conditional branch, reason, overturn condition, and next action.
Do not expose internal method/protocol names unless the user asks."""

BASE_RULE = """Answer the user directly in the user's language. Hide internal routing, audits, method names, scoring rubrics, and field lists unless explicitly requested. Do not inspect repository files or experiment fixtures. Use only the context supplied in this request."""

QUESTION_TAIL_RE = re.compile(r"[?？]\s*$")


def load_cases(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def select_cases(cases: list[dict[str, Any]], spec: str | None) -> list[dict[str, Any]]:
    if not spec:
        return cases
    wanted = {item.strip() for item in spec.split(",") if item.strip()}
    return [case for case in cases if str(case["case_id"]) in wanted]


def stable_context() -> str:
    chunks = []
    for rel in STABLE_CONTEXT_PATHS:
        text = (ROOT / rel).read_text(encoding="utf-8")
        chunks.append(f"\n--- Stable contract: {rel} ---\n{text}")
    return "\n".join(chunks)


def system_instruction(variant: str, stable: str) -> str:
    if variant == "B":
        return f"{BASE_RULE}\n\n{SOURCE_PROTOCOL}"
    common = (
        f"{BASE_RULE}\n\n"
        "The following tracked text is the fixed Stable Mindthus context capsule for this direct-inference pilot. "
        "Apply it only when naturally applicable; clear direct tasks remain direct.\n"
        f"{stable}"
    )
    if variant == "A":
        return common + "\n\nDo not use any experimental bidirectional-steelman candidate."
    if variant == "C":
        return common + f"\n\n{ADAPTED_PROTOCOL}"
    raise ValueError(variant)


def api_call(token: str, model: str, messages: list[dict[str, str]], *, retries: int = 5) -> dict[str, Any]:
    body = json.dumps({"model": model, "messages": messages, "stream": False}).encode("utf-8")
    request = urllib.request.Request(
        ENDPOINT,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.github+json",
            "User-Agent": "mindthus-bsc-experiment",
        },
    )
    last_error = ""
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            payload = exc.read().decode("utf-8", errors="replace")
            last_error = f"HTTP {exc.code}: {payload}"
            if exc.code not in {408, 429, 500, 502, 503, 504} or attempt == retries - 1:
                raise RuntimeError(last_error) from exc
            retry_after = exc.headers.get("retry-after")
            delay = float(retry_after) if retry_after and retry_after.replace(".", "", 1).isdigit() else min(30, 2 ** attempt * 3)
            time.sleep(delay)
        except Exception as exc:
            last_error = str(exc)
            if attempt == retries - 1:
                raise RuntimeError(last_error) from exc
            time.sleep(min(20, 2 ** attempt * 2))
    raise RuntimeError(last_error)


def assistant_text(response: dict[str, Any]) -> str:
    choices = response.get("choices") or []
    if not choices:
        raise ValueError(f"model response has no choices: {response}")
    content = (choices[0].get("message") or {}).get("content")
    if isinstance(content, str):
        return content.strip()
    raise ValueError("model response has no text content")


def looks_like_question(text: str) -> bool:
    stripped = text.rstrip()
    if QUESTION_TAIL_RE.search(stripped):
        return True
    tail = stripped[-300:]
    return any(marker in tail for marker in ("我只问一个问题", "最关键的问题", "请告诉我", "你更", "你最"))


def user_turns(case: dict[str, Any]) -> list[str]:
    if case.get("turns"):
        return [str(turn["content"]) for turn in case["turns"] if turn.get("role") == "user"]
    return [str(case["prompt"])]


def run_case(token: str, model: str, variant: str, case: dict[str, Any], stable: str) -> dict[str, Any]:
    started = time.time()
    messages: list[dict[str, str]] = [{"role": "system", "content": system_instruction(variant, stable)}]
    transcript: list[dict[str, str]] = []
    usages: list[dict[str, Any]] = []
    error = None

    try:
        for prompt in user_turns(case):
            messages.append({"role": "user", "content": prompt})
            transcript.append({"role": "user", "content": prompt})
            response = api_call(token, model, messages)
            text = assistant_text(response)
            usages.append(response.get("usage") or {})
            messages.append({"role": "assistant", "content": text})
            transcript.append({"role": "assistant", "content": text})
            time.sleep(1.5)

        if (
            len(user_turns(case)) == 1
            and case.get("continuation_reply")
            and transcript
            and transcript[-1]["role"] == "assistant"
            and looks_like_question(transcript[-1]["content"])
        ):
            followup = str(case["continuation_reply"])
            messages.append({"role": "user", "content": followup})
            transcript.append({"role": "user", "content": followup})
            response = api_call(token, model, messages)
            text = assistant_text(response)
            usages.append(response.get("usage") or {})
            messages.append({"role": "assistant", "content": text})
            transcript.append({"role": "assistant", "content": text})
            time.sleep(1.5)
    except Exception as exc:
        error = str(exc)

    final_answer = next((item["content"] for item in reversed(transcript) if item["role"] == "assistant"), "")
    return {
        "case_id": case["case_id"],
        "case_type": case["case_type"],
        "title": case["title"],
        "transcript": transcript,
        "final_answer": final_answer,
        "usage": usages,
        "duration_seconds": round(time.time() - started, 3),
        "error": error,
    }


def judge_prompt(case: dict[str, Any], record: dict[str, Any]) -> str:
    transcript = "\n\n".join(f"{item['role'].title()}: {item['content']}" for item in record["transcript"])
    return f"""You are a blind research judge. Judge only the transcript and rubric below; do not infer which treatment produced it. Return strict JSON only, with exactly these keys:
case_id, behavioral_pass, hard_fail_observed, question_count_observed, dimensions, rationale.
`dimensions` must contain exactly: {', '.join(DIMENSIONS)}. Each dimension is 0, 1, 2, or null. Use 0=failed, 1=partial, 2=strong. For negative controls, `negative_control_sleep` is primary and method ceremony counts against behavioral_pass.

case_id: {case['case_id']}
case_type: {case['case_type']}
expected_behavior: {case['expected_behavior']}
hard_fail: {case['hard_fail']}

Transcript:
{transcript}
"""


def parse_json_text(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    return json.loads(stripped)


def validate_score(score: dict[str, Any], case_id: str) -> None:
    if score.get("case_id") != case_id:
        raise ValueError("judge case_id mismatch")
    dims = score.get("dimensions")
    if not isinstance(dims, dict) or set(dims) != set(DIMENSIONS):
        raise ValueError("judge dimensions mismatch")
    for value in dims.values():
        if value is not None and value not in {0, 1, 2}:
            raise ValueError("invalid dimension score")


def judge_case(token: str, model: str, case: dict[str, Any], record: dict[str, Any]) -> dict[str, Any]:
    if record.get("error") or not record.get("final_answer"):
        return {
            "case_id": case["case_id"],
            "behavioral_pass": False,
            "hard_fail_observed": False,
            "question_count_observed": 0,
            "dimensions": {name: None for name in DIMENSIONS},
            "rationale": f"generation failed: {record.get('error')}",
            "judge_error": "generation_failed",
        }
    try:
        response = api_call(
            token,
            model,
            [
                {"role": "system", "content": "Return strict JSON only. Do not use external tools or repository context."},
                {"role": "user", "content": judge_prompt(case, record)},
            ],
        )
        score = parse_json_text(assistant_text(response))
        validate_score(score, str(case["case_id"]))
        score["judge_usage"] = response.get("usage") or {}
        score["judge_error"] = None
        time.sleep(1.5)
        return score
    except Exception as exc:
        return {
            "case_id": case["case_id"],
            "behavioral_pass": False,
            "hard_fail_observed": False,
            "question_count_observed": 0,
            "dimensions": {name: None for name in DIMENSIONS},
            "rationale": "judge failed",
            "judge_error": str(exc),
        }


def average(values: list[int]) -> float | None:
    return round(sum(values) / len(values), 3) if values else None


def summarize(variant: str, records: list[dict[str, Any]], scores: list[dict[str, Any]]) -> dict[str, Any]:
    score_by_id = {str(item["case_id"]): item for item in scores}
    positives = [r for r in records if r["case_type"] == "positive"]
    negatives = [r for r in records if r["case_type"] == "negative_control"]
    positive_passes = sum(bool(score_by_id.get(str(r["case_id"]), {}).get("behavioral_pass")) for r in positives)
    hard_fails = sum(bool(item.get("hard_fail_observed")) for item in scores)
    dims: dict[str, float | None] = {}
    for name in DIMENSIONS:
        vals = [int(s["dimensions"][name]) for s in scores if s.get("dimensions", {}).get(name) is not None]
        dims[name] = average(vals)
    return {
        "schema_version": "mindthus-bsc-github-models-summary-v0.1",
        "variant": variant,
        "case_count": len(records),
        "judged_case_count": sum(item.get("judge_error") is None for item in scores),
        "generation_error_count": sum(bool(item.get("error")) for item in records),
        "judge_error_count": sum(item.get("judge_error") is not None for item in scores),
        "positive_behavioral_pass_rate": round(positive_passes / len(positives), 3) if positives else None,
        "negative_control_pass_rate": (
            round(sum(bool(score_by_id.get(str(r["case_id"]), {}).get("behavioral_pass")) for r in negatives) / len(negatives), 3)
            if negatives else None
        ),
        "hard_fail_rate": round(hard_fails / len(scores), 3) if scores else None,
        "dimension_averages": dims,
        "total_duration_seconds": round(sum(float(r["duration_seconds"]) for r in records), 3),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant", choices=("A", "B", "C"), required=True)
    parser.add_argument("--model", default="openai/gpt-5")
    parser.add_argument("--judge-model", default="openai/gpt-5")
    parser.add_argument("--cases", default=str(DEFAULT_CASES))
    parser.add_argument("--case-ids")
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN is required")

    cases = select_cases(load_cases(Path(args.cases)), args.case_ids)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    stable = stable_context() if args.variant in {"A", "C"} else ""

    records = [run_case(token, args.model, args.variant, case, stable) for case in cases]
    scores = [judge_case(token, args.judge_model, case, record) for case, record in zip(cases, records)]
    summary = summarize(args.variant, records, scores)
    payload = {
        "schema_version": "mindthus-bsc-github-models-result-v0.1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "substrate": "github-models-direct-inference",
        "runtime_equivalence_claim": False,
        "model": args.model,
        "judge_model": args.judge_model,
        "stable_context_paths": list(STABLE_CONTEXT_PATHS) if args.variant in {"A", "C"} else [],
        "summary": summary,
        "scores": scores,
        "cases": records,
    }
    (out / f"{args.variant}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["generation_error_count"] == 0 and summary["judge_error_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
