#!/usr/bin/env python3
"""Append and validate lightweight Method Fidelity usage logs.

This script records whether method-fidelity constraints helped in real or evaluation
use. It validates the record shape only; it does not judge method value.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "mindthus-fidelity-usage-log-v0.1"
DEFAULT_LOG = Path("data/fidelity-usage-log.jsonl")
METHODS = ("3L5S", "SELA", "MPG", "EDSP", "WAE", "TVG", "tplan", "using-mindthus")
RECORD_TYPES = ("real_use", "evaluation", "fixture")
HELPED_VALUES = ("yes", "no", "mixed", "unknown")
INVOCATION_MODES = ("explicit_router", "explicit_skill", "automatic_best_effort", "unknown")
OVERHEAD_LEVELS = ("none", "low", "moderate", "high", "unknown")

# Backfill is useful for analysis and dangerous for the freeze: if historical tasks count
# toward the tenth record, the observation window can be closed in an afternoon. Records
# therefore declare when the task actually happened (`observed_at`, distinct from
# `logged_at`) and how it was collected. Prospective is necessary but not sufficient for
# freeze exit; the observation date has to clear FREEZE_OPENED as well. See freeze_eligible.
COLLECTION_MODES = ("prospective", "retrospective", "unknown")

# The exact GitHub creation timestamp of #144. The issue requires tasks occurring after
# it opened, not after the next UTC calendar boundary. Rounding this to 2026-07-27 omitted
# 5h56m37s of otherwise eligible observation time.
#
# Parsed once at import rather than per record: a tz-naive value here raises TypeError on
# comparison, and a boundary that only fails when someone moves the window is a boundary
# nobody can move.
FREEZE_OPENED = datetime(2026, 7, 26, 18, 3, 23, tzinfo=timezone.utc)


@dataclass(frozen=True)
class Finding:
    line: int
    code: str
    message: str


def non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_tags(raw: str) -> list[str]:
    if not raw.strip():
        return []
    tags = [item.strip() for item in raw.split(",")]
    return [item for item in tags if item]


def optional_text(value: str | None) -> str:
    return value.strip() if value else ""


def parse_timestamp(value: Any) -> datetime | None:
    """Parse an ISO-8601 timestamp, or None if it is not one.

    Returns tz-aware UTC. A naive timestamp is read as UTC rather than rejected: every
    timestamp this script writes carries `Z`, and rejecting naive values would invalidate
    a hand-edited record for a reason unrelated to whether the task happened.
    """
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def validate_timestamp(
    record: dict[str, Any], field: str, findings: list[Finding], line: int, *, required: bool
) -> datetime | None:
    """Validate one timestamp field by type, then by format, as separate findings.

    Two codes rather than one, because they are two different mistakes: a non-string is a
    writer bug, an unparseable string is a human typo. Collapsing them into "must be a
    non-empty string" let `not-a-date`, `2027-13-45`, and `yesterday` all validate --
    which is how a record could claim to be a prospective observation of a task in 2024.
    """
    value = record.get(field)
    if value is None:
        if required:
            findings.append(Finding(line, "missing-field", f"{field} must be a non-empty string"))
        return None
    if not isinstance(value, str):
        findings.append(Finding(line, "invalid-field-type", f"{field} must be a string"))
        return None
    if not value.strip():
        findings.append(Finding(line, "missing-field", f"{field} must be a non-empty string"))
        return None
    parsed = parse_timestamp(value)
    if parsed is None:
        findings.append(
            Finding(line, "invalid-timestamp", f"{field} must be an ISO-8601 timestamp")
        )
    return parsed


def validate_score(
    record: dict[str, Any], field: str, max_score: int, findings: list[Finding], line: int
) -> None:
    value = record.get(field)
    if value is None and field == "baseline_score":
        return
    if not is_int(value) or not 0 <= value <= max_score:
        findings.append(
            Finding(line, "invalid-score", f"{field} must be an integer from 0 to max_score")
        )


def validate_record(record: Any, line: int) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(record, dict):
        return [Finding(line, "invalid-record", "record must be a JSON object")]

    if record.get("schema_version") != SCHEMA_VERSION:
        findings.append(
            Finding(line, "invalid-schema-version", f"schema_version must be {SCHEMA_VERSION}")
        )

    for field in ("scenario", "model"):
        if not non_empty_string(record.get(field)):
            findings.append(Finding(line, "missing-field", f"{field} must be a non-empty string"))

    if record.get("method") not in METHODS:
        findings.append(Finding(line, "invalid-method", f"method must be one of: {', '.join(METHODS)}"))
    if record.get("record_type") not in RECORD_TYPES:
        findings.append(
            Finding(line, "invalid-record-type", f"record_type must be one of: {', '.join(RECORD_TYPES)}")
        )
    if record.get("constraint_helped") not in HELPED_VALUES:
        findings.append(
            Finding(
                line,
                "invalid-helped-value",
                f"constraint_helped must be one of: {', '.join(HELPED_VALUES)}",
            )
        )

    invocation_mode = record.get("invocation_mode")
    if invocation_mode is not None and invocation_mode not in INVOCATION_MODES:
        findings.append(
            Finding(
                line,
                "invalid-invocation-mode",
                f"invocation_mode must be one of: {', '.join(INVOCATION_MODES)}",
            )
        )
    for field in ("decision_changed", "rework_reduced", "harm_observed"):
        value = record.get(field)
        if value is not None and value not in HELPED_VALUES:
            findings.append(
                Finding(
                    line,
                    "invalid-outcome-value",
                    f"{field} must be one of: {', '.join(HELPED_VALUES)}",
                )
            )
    collection_mode = record.get("collection_mode")
    if collection_mode is not None and collection_mode not in COLLECTION_MODES:
        findings.append(
            Finding(
                line,
                "invalid-collection-mode",
                f"collection_mode must be one of: {', '.join(COLLECTION_MODES)}",
            )
        )
    # Both timestamps go through the same function. Validating `logged_at` for presence
    # only while `observed_at` was checked for emptiness only meant the field the freeze
    # actually counts on was the less validated of the two.
    logged_at = validate_timestamp(record, "logged_at", findings, line, required=True)
    observed_at = validate_timestamp(record, "observed_at", findings, line, required=False)
    if logged_at and observed_at and observed_at > logged_at:
        findings.append(
            Finding(
                line,
                "impossible-observation-order",
                "observed_at is after logged_at; a task cannot be recorded before it happened",
            )
        )

    record_id = record.get("record_id")
    if record_id is not None and not non_empty_string(record_id):
        findings.append(
            Finding(line, "invalid-optional-field", "record_id must be a non-empty string")
        )

    overhead_level = record.get("overhead_level")
    if overhead_level is not None and overhead_level not in OVERHEAD_LEVELS:
        findings.append(
            Finding(
                line,
                "invalid-overhead-level",
                f"overhead_level must be one of: {', '.join(OVERHEAD_LEVELS)}",
            )
        )
    if "mechanism" in record and not isinstance(record.get("mechanism"), str):
        findings.append(Finding(line, "invalid-optional-field", "mechanism must be a string"))

    max_score = record.get("max_score")
    baseline = record.get("baseline_score")
    constrained = record.get("constrained_score")
    if max_score is None and record.get("record_type") == "real_use":
        if baseline is not None or constrained is not None:
            findings.append(
                Finding(
                    line,
                    "incomplete-score-set",
                    "real_use scores require constrained_score and a positive max_score",
                )
            )
    elif not is_int(max_score) or max_score <= 0:
        findings.append(Finding(line, "invalid-max-score", "max_score must be a positive integer"))
        max_score = 0
    else:
        validate_score(record, "baseline_score", max_score, findings, line)
        validate_score(record, "constrained_score", max_score, findings, line)

    expected_delta = constrained - baseline if is_int(baseline) and is_int(constrained) else None
    if record.get("score_delta") != expected_delta:
        findings.append(
            Finding(line, "invalid-score-delta", "score_delta must equal constrained_score - baseline_score")
        )

    tags = record.get("tags")
    if not isinstance(tags, list) or any(not non_empty_string(item) for item in tags):
        findings.append(Finding(line, "invalid-tags", "tags must be a list of non-empty strings"))

    # Absent and empty both mean "not provided" and must be treated the same way. They
    # were not: `--source ""` passed silently while omitting the key reported a finding,
    # so the more careless entry was the one that validated. Only a wrong *type* is a
    # finding. These fields stay optional -- see data/README.md, which describes `source`
    # as a pointer to use when a redacted record needs one, not as a required field.
    for field in ("judge_model", "source", "notes"):
        value = record.get(field)
        if value is not None and not isinstance(value, str):
            findings.append(Finding(line, "invalid-optional-field", f"{field} must be a string"))

    return findings


def derive_record_id(record: dict[str, Any]) -> str:
    """Derive an ID from the fields that identify the task.

    Stable under reordering and reformatting of the log, which is what the record-10
    review needs in order to cite inclusion and exclusion by ID.

    `logged_at` is deliberately not in the seed. It contributed nothing in one case and
    damage in the other: without `--observed-at` the two fields are equal, so including
    it was redundant; with `--observed-at` it was the only thing making the same task
    yield a different ID depending on when someone got around to logging it.

    The stability this buys is conditional, and the condition is the caller's:

    - With an explicit `--observed-at`, the same task logged twice yields the same ID, so
      an accidental duplicate is visible as a repeated ID.
    - Without it, `observed_at` defaults to the logging time, so the same task logged
      twice still yields two IDs. Nothing here can detect that duplicate.

    Two genuinely distinct tasks sharing `observed_at`, type, method, scenario, and model
    collide into one ID. `scenario` is the discriminator that makes this unlikely, not
    impossible -- and a collision is not detectable from the ID either. Deduplication
    remains a human step at review time.
    """
    seed = "|".join(
        str(record.get(field, ""))
        for field in ("observed_at", "record_type", "method", "scenario", "model")
    )
    return "mtu-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]


def build_record(args: argparse.Namespace) -> dict[str, Any]:
    baseline = args.baseline_score
    constrained = args.constrained_score
    logged_at = args.logged_at or now_utc()
    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "logged_at": logged_at,
        "observed_at": optional_text(args.observed_at) or logged_at,
        "collection_mode": args.collection_mode,
        "record_type": args.record_type,
        "scenario": args.scenario.strip(),
        "method": args.method,
        "model": args.model.strip(),
        "judge_model": optional_text(args.judge_model),
        "baseline_score": baseline,
        "constrained_score": constrained,
        "max_score": args.max_score,
        "score_delta": constrained - baseline if baseline is not None else None,
        "constraint_helped": args.constraint_helped,
        "invocation_mode": args.invocation_mode,
        "decision_changed": args.decision_changed,
        "rework_reduced": args.rework_reduced,
        "overhead_level": args.overhead_level,
        "harm_observed": args.harm_observed,
        "mechanism": optional_text(args.mechanism),
        "source": optional_text(args.source),
        "notes": optional_text(args.notes),
        "tags": parse_tags(args.tags),
    }
    record["record_id"] = optional_text(args.record_id) or derive_record_id(record)
    return record


def is_default_log_path(path: Path) -> bool:
    return path.resolve(strict=False) == (Path.cwd() / DEFAULT_LOG).resolve(strict=False)


def read_jsonl(path: Path, *, allow_missing_empty: bool = False) -> tuple[list[dict[str, Any]], list[Finding]]:
    records: list[dict[str, Any]] = []
    findings: list[Finding] = []
    if not path.exists():
        if allow_missing_empty:
            return records, findings
        findings.append(Finding(0, "missing-log", f"usage log not found: {path}"))
        return records, findings

    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            findings.append(Finding(index, "invalid-json", f"invalid JSON: {exc}"))
            continue
        records.append(record)
        findings.extend(validate_record(record, index))
    return records, findings


def print_findings(findings: list[Finding]) -> None:
    for finding in findings:
        line = f"line {finding.line}" if finding.line else "file"
        print(f"- BLOCK [{finding.code}] {line}: {finding.message}")


def count_by_type(records: list[dict[str, Any]]) -> dict[str, int]:
    """Break the record count down by type, and by collection mode within `real_use`.

    An untyped total is not a usable signal: a log holding only `evaluation` and `fixture`
    records can satisfy a total threshold while `real_use` stays at zero.

    `real_use_prospective` and `freeze_eligible` are reported separately and deliberately.
    Collapsing them into one number would hide exactly the records worth looking at: a
    backfilled record declaring itself prospective shows up as the gap between the two.
    """
    counts = {record_type: 0 for record_type in RECORD_TYPES}
    prospective = 0
    eligible_ids: set[str] = set()
    for record in records:
        record_type = record.get("record_type")
        if record_type in counts:
            counts[record_type] += 1
        if record_type == "real_use" and record.get("collection_mode") == "prospective":
            prospective += 1
            if freeze_eligible(record):
                # The observation window is ten independently citable tasks, not ten
                # lines. A repeated stable ID stays visible in the raw/prospective count
                # but contributes once to freeze exit.
                eligible_ids.add(record["record_id"].strip())
    counts["real_use_prospective"] = prospective
    counts["freeze_eligible"] = len(eligible_ids)
    return counts


def freeze_eligible(record: dict[str, Any]) -> bool:
    """Whether one record counts toward freeze exit.

    `collection_mode=prospective` alone is not enough. It is a self-declared field, and a
    record can declare itself prospective while pointing `observed_at` at a task from
    years before the freeze opened -- which validated, and counted. Requiring the
    observation to fall after FREEZE_OPENED closes that particular hole.

    Eligibility also requires a stable ID and a reviewable source. Their presence does
    not prove either is truthful; it only ensures that the record-10 human review has an
    identity and evidence pointer to examine. Semantic inclusion remains human judgment.

    A record with no `observed_at` is not eligible. It could be dated from `logged_at`
    instead -- but then omitting the field would be enough to make a backfilled record
    count, which is the hole this closes. The CLI always writes the field, so this only
    reaches hand-written records, and the failure is visible: the count does not move.
    """
    if record.get("record_type") != "real_use":
        return False
    if record.get("collection_mode") != "prospective":
        return False
    if not non_empty_string(record.get("record_id")):
        return False
    if not non_empty_string(record.get("source")):
        return False
    observed = parse_timestamp(record.get("observed_at"))
    if observed is None:
        return False
    return observed > FREEZE_OPENED


def freeze_opened_text() -> str:
    return FREEZE_OPENED.isoformat().replace("+00:00", "Z")


def validate_log(path: Path, min_real_use: int = 0) -> int:
    missing_default_log = not path.exists() and is_default_log_path(path)
    records, findings = read_jsonl(path, allow_missing_empty=missing_default_log)
    if findings:
        print("Fidelity Usage Log Report")
        print(f"Log file: {path}")
        print_findings(findings)
        return 1
    counts = count_by_type(records)
    print("Fidelity Usage Log Report")
    print(f"Log file: {path}")
    print(f"Records: {len(records)}")
    print(
        f"By type: real_use={counts['real_use']} "
        f"evaluation={counts['evaluation']} fixture={counts['fixture']}"
    )
    print(f"Real-use prospective: {counts['real_use_prospective']}")
    print(
        f"Freeze-eligible: {counts['freeze_eligible']} "
        f"(unique, traceable, prospective, observed after {freeze_opened_text()})"
    )
    if missing_default_log:
        print("No usage-log data yet; the default log is optional until the first record is appended.")
    print("No usage-log shape risks detected.")
    if min_real_use and counts["freeze_eligible"] < min_real_use:
        # Deliberately not a shape finding: the log is well-formed, there is simply not
        # enough of it yet. Callers that want this to be fatal opt in with --min-real-use;
        # required CI must not, or a strategic gap becomes a merge blocker.
        print(
            f"- BELOW-THRESHOLD freeze-eligible real_use {counts['freeze_eligible']} "
            f"< required {min_real_use}"
        )
        return 1
    return 0


STATUS_BEGIN = "<!-- BEGIN real-use-status (generated by scripts/log-fidelity-usage.py) -->"
STATUS_END = "<!-- END real-use-status -->"
FREEZE_EXIT_TARGET = 10


def render_status_block(records: list[dict[str, Any]]) -> str:
    """Render the real-use status block embedded in README.md.

    The point of this surface is that a reader encounters the number, so it states the
    freeze-eligible count against the freeze-exit target rather than a total that
    evaluation and fixture records could inflate.

    "No records at all" and "records exist, none eligible" are rendered as separate
    sentences. They are different situations and only one of them is "the register is
    empty"; a status surface that says the empty thing while records exist is stating a
    falsehood on the project's front page.
    """
    counts = count_by_type(records)
    prospective = counts["real_use_prospective"]
    eligible = counts["freeze_eligible"]
    lines = [
        STATUS_BEGIN,
        f"**真实使用记录：{eligible}/{FREEZE_EXIT_TARGET}**"
        f"（冻结开出后观察到的前瞻记录；另有 retrospective {counts['real_use'] - prospective} 条、"
        f"evaluation {counts['evaluation']} 条、fixture {counts['fixture']} 条）",
        "",
    ]
    if not records:
        lines.append(
            "目前还没有任何记录。这不是失败指标，而是**当前最大的证据缺口**："
            "`docs/real-use-validation.md` 把\"下一步值得修什么\"的导航权交给真实使用记录，"
            "而这个登记册还是空的。"
        )
    elif eligible == 0:
        lines.append(
            f"已有 {len(records)} 条记录，但没有一条计入冻结退出："
            f"退出只按 `collection_mode=prospective` 且 `observed_at` 晚于 "
            f"{freeze_opened_text()}、具有 `record_id` 和 `source` 的唯一 "
            "`real_use` 记录计数。"
            "回溯记录可以参与分析，但不解冻。"
        )
    else:
        lines.append(
            f"满 {FREEZE_EXIT_TARGET} 条后进行汇总复核，逐条列出纳入/排除的 `record_id` 与理由。"
        )
    lines.append("")
    lines.append(
        "这个数字由 `python3 scripts/log-fidelity-usage.py --render-status` 生成，"
        "不要手工编辑。"
    )
    lines.append(STATUS_END)
    return "\n".join(lines)


def sync_status(readme: Path, records: list[dict[str, Any]], *, check: bool) -> int:
    """Write or verify the README status block.

    `--check-status` is what required CI runs: it asserts the rendered surface still agrees
    with the log, and says nothing about whether the count is adequate. An empty log must
    keep CI green — turning a strategic gap into a merge blocker converts it into noise
    that gets routed around.
    """
    if not readme.is_file():
        print(f"- BLOCK [missing-readme] file: {readme} not found")
        return 1
    text = readme.read_text(encoding="utf-8")
    if STATUS_BEGIN not in text or STATUS_END not in text:
        print(f"- BLOCK [missing-status-block] file: {readme} has no real-use status block")
        return 1

    head, _, rest = text.partition(STATUS_BEGIN)
    current, _, tail = rest.partition(STATUS_END)
    updated = head + render_status_block(records) + tail
    if updated == text:
        print(f"real-use status block is current in {readme}")
        return 0
    if check:
        print(
            f"- BLOCK [stale-status] file: {readme} real-use status block disagrees with the log; "
            "run scripts/log-fidelity-usage.py --render-status"
        )
        return 1
    readme.write_text(updated, encoding="utf-8")
    print(f"updated real-use status block in {readme}")
    return 0


def append_record(path: Path, record: dict[str, Any]) -> int:
    findings = validate_record(record, 1)
    if findings:
        print("Fidelity Usage Log Report")
        print_findings(findings)
        return 1

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

    print(f"appended fidelity usage log record to {path}")
    if record["max_score"] is None:
        score_summary = "score=not_recorded"
    else:
        baseline = record["baseline_score"]
        delta = record["score_delta"]
        baseline_text = "none" if baseline is None else str(baseline)
        delta_text = "none" if delta is None else f"{delta:+d}"
        score_summary = (
            f"baseline={baseline_text}/{record['max_score']} "
            f"constrained={record['constrained_score']}/{record['max_score']} "
            f"delta={delta_text}"
        )
    print(
        "summary: "
        f"method={record['method']} model={record['model']} {score_summary} "
        f"helped={record['constraint_helped']} invocation={record['invocation_mode']}"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG, help="JSONL usage log path.")
    parser.add_argument("--validate", action="store_true", help="Validate an existing usage log.")
    parser.add_argument(
        "--render-status",
        action="store_true",
        help="Rewrite the real-use status block in README.md from the log.",
    )
    parser.add_argument(
        "--check-status",
        action="store_true",
        help=(
            "Verify the rendered status block still agrees with the log. Checks freshness "
            "only, never adequacy, so an empty log keeps required CI green."
        ),
    )
    parser.add_argument(
        "--readme",
        type=Path,
        default=Path("README.md"),
        help="Status surface to render or check.",
    )
    parser.add_argument(
        "--min-real-use",
        type=int,
        default=0,
        help=(
            "Exit non-zero when freeze-eligible real_use records fall below this count. "
            "Record-type, date, traceability, and stable-ID aware by design; repeated IDs "
            "count once. Not used by required CI."
        ),
    )
    parser.add_argument("--scenario", help="Redacted scenario summary.")
    parser.add_argument("--method", choices=METHODS, help="Mindthus method or skill used.")
    parser.add_argument("--model", help="Model that produced the method output.")
    parser.add_argument("--judge-model", help="Human or LLM judge identifier.")
    parser.add_argument("--baseline-score", type=int, help="Optional baseline score.")
    parser.add_argument("--constrained-score", type=int, help="Constrained or real-use judge score.")
    parser.add_argument("--max-score", type=int, help="Maximum judge score for this rubric.")
    parser.add_argument("--constraint-helped", choices=HELPED_VALUES, help="Whether constraints helped.")
    parser.add_argument(
        "--invocation-mode",
        default="unknown",
        choices=INVOCATION_MODES,
        help="How Mindthus entered the task.",
    )
    parser.add_argument(
        "--decision-changed",
        default="unknown",
        choices=HELPED_VALUES,
        help="Whether Mindthus materially changed the judgment or action.",
    )
    parser.add_argument(
        "--rework-reduced",
        default="unknown",
        choices=HELPED_VALUES,
        help="Whether Mindthus reduced downstream rework.",
    )
    parser.add_argument(
        "--overhead-level",
        default="unknown",
        choices=OVERHEAD_LEVELS,
        help="Observed extra process or attention cost.",
    )
    parser.add_argument(
        "--harm-observed",
        default="unknown",
        choices=HELPED_VALUES,
        help="Whether Mindthus caused a worse decision, delay, or avoidable burden.",
    )
    parser.add_argument("--mechanism", help="Redacted recurring success or failure mechanism.")
    parser.add_argument("--record-type", default="real_use", choices=RECORD_TYPES, help="Usage record type.")
    parser.add_argument("--logged-at", help="Override timestamp. Must be ISO-8601; validated.")
    parser.add_argument(
        "--observed-at",
        help=(
            "When the task actually occurred, if not now. Defaults to logged_at, which "
            "also means the record ID is only reproducible when this is passed explicitly."
        ),
    )
    parser.add_argument(
        "--collection-mode",
        default="prospective",
        choices=COLLECTION_MODES,
        help=(
            "prospective: observed as it happened. retrospective: reconstructed from an "
            "earlier task. Freeze exit needs prospective AND an observed_at after "
            "the exact time the freeze opened; declaring prospective does not by itself count."
        ),
    )
    parser.add_argument(
        "--record-id",
        help=(
            "Override the derived record ID. Normally left unset. Repeated IDs remain "
            "valid log rows but count once toward freeze exit."
        ),
    )
    parser.add_argument(
        "--source",
        help=(
            "Reviewable artifact, issue, incident, or commit pointer. Optional for legacy "
            "and non-freeze records; a prospective real_use record cannot count toward "
            "freeze exit without it."
        ),
    )
    parser.add_argument("--notes", help="Optional short note.")
    parser.add_argument("--tags", default="", help="Comma-separated tags.")
    args = parser.parse_args()

    if args.render_status or args.check_status:
        missing_default_log = not args.log.exists() and is_default_log_path(args.log)
        records, findings = read_jsonl(args.log, allow_missing_empty=missing_default_log)
        if findings:
            print_findings(findings)
            return 1
        return sync_status(args.readme, records, check=args.check_status)

    if args.validate:
        return validate_log(args.log, min_real_use=args.min_real_use)

    required = {
        "scenario": args.scenario,
        "method": args.method,
        "model": args.model,
        "constraint_helped": args.constraint_helped,
    }
    if args.record_type != "real_use":
        required.update(
            {
                "constrained_score": args.constrained_score,
                "max_score": args.max_score,
            }
        )
    missing = [name for name, value in required.items() if value is None or value == ""]
    if missing:
        raise SystemExit(f"missing required arguments for append: {', '.join(missing)}")

    score_values = (args.baseline_score, args.constrained_score, args.max_score)
    if any(value is not None for value in score_values) and (
        args.constrained_score is None or args.max_score is None
    ):
        raise SystemExit("partial scores are invalid: provide constrained_score and max_score together")

    return append_record(args.log, build_record(args))


if __name__ == "__main__":
    raise SystemExit(main())
