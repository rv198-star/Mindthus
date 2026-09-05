"""Pure interval reconciliation and token counting for TPlan cost projections."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Iterable

RECONCILABLE_KINDS = {"model", "script", "tool", "wait", "runtime"}
EXACT_MEASUREMENT_SOURCES = {"platform_reported", "host_measured"}


def _parse_timestamp(value: str) -> datetime:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    return datetime.fromisoformat(normalized)


def _timestamp_ms(value: str) -> int:
    return round(_parse_timestamp(value).timestamp() * 1000)


def _iso_from_ms(value: int) -> str:
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _union_duration_ms(intervals: Iterable[tuple[int, int]]) -> int:
    ordered = sorted((start, finish) for start, finish in intervals if finish >= start)
    if not ordered:
        return 0
    total = 0
    current_start, current_finish = ordered[0]
    for start, finish in ordered[1:]:
        if start <= current_finish:
            current_finish = max(current_finish, finish)
            continue
        total += current_finish - current_start
        current_start, current_finish = start, finish
    return total + current_finish - current_start


def _record_interval(record: dict[str, Any]) -> tuple[int, int]:
    span = record["span"]
    return _timestamp_ms(span["started_at"]), _timestamp_ms(span["finished_at"])


def _is_reconcilable(record: dict[str, Any]) -> bool:
    span = record["span"]
    return (
        span["kind"] in RECONCILABLE_KINDS
        and span["measurement_source"] in EXACT_MEASUREMENT_SOURCES
    )


def _clip_interval(
    interval: tuple[int, int],
    started_at: str | None,
    finished_at: str | None,
) -> tuple[int, int] | None:
    start, finish = interval
    if started_at is not None:
        start = max(start, _timestamp_ms(started_at))
    if finished_at is not None:
        finish = min(finish, _timestamp_ms(finished_at))
    if finish < start:
        return None
    return start, finish


def _elapsed_reconciliation(
    records: Iterable[dict[str, Any]],
    *,
    elapsed_ms: int | None,
    observed_elapsed_ms: int | None,
    coverage: str,
    started_at: str | None,
    finished_at: str | None,
) -> dict[str, Any]:
    records = list(records)
    intervals = []
    for record in records:
        if not _is_reconcilable(record):
            continue
        clipped = _clip_interval(_record_interval(record), started_at, finished_at)
        if clipped is not None:
            intervals.append(clipped)
    exact_interval_coverage_ms = _union_duration_ms(intervals)
    if observed_elapsed_ms is not None:
        exact_interval_coverage_ms = min(exact_interval_coverage_ms, observed_elapsed_ms)
    exact_partition = coverage == "exact" and elapsed_ms is not None
    not_exactly_recorded_elapsed_ms = (
        max(0, elapsed_ms - exact_interval_coverage_ms) if exact_partition else None
    )
    exact_interval_coverage_ratio = None
    if exact_partition:
        exact_interval_coverage_ratio = 1.0 if elapsed_ms == 0 and exact_interval_coverage_ms == 0 else (
            exact_interval_coverage_ms / elapsed_ms if elapsed_ms else 0.0
        )
    return {
        "coverage": coverage,
        "elapsed_ms": elapsed_ms,
        "observed_elapsed_ms": observed_elapsed_ms,
        "exact_interval_coverage_ms": (
            exact_interval_coverage_ms if observed_elapsed_ms is not None else None
        ),
        "not_exactly_recorded_elapsed_ms": not_exactly_recorded_elapsed_ms,
        "exact_interval_coverage_ratio": exact_interval_coverage_ratio,
        "included_exact_interval_count": len(intervals),
        "excluded_envelope_span_count": sum(
            1 for record in records if record["span"]["kind"] == "agent_turn"
        ),
    }


def _counted_tokens(usage: dict[str, int]) -> int:
    """Count billable totals without re-adding cached/reasoning subsets."""

    return usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
