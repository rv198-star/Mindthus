#!/usr/bin/env python3
"""Measure one host-side model SDK call and emit paired sanitized trace events."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Generic, TypeVar

from tplan_runtime import record_execution_span, start_execution_span


T = TypeVar("T")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class ModelCallObserver(Generic[T]):
    """Strict observer for the caller-visible elapsed time of one model request.

    The callable and its return value are never inspected or serialized. An optional
    usage extractor may return only the numeric usage fields accepted by TPlan.
    """

    def __init__(
        self,
        mission_dir: Path,
        *,
        task_id: str | None,
        label: str,
        attribution: str = "exact",
        attempt: int = 1,
        parent_span_id: str | None = None,
        shared_task_ids: list[str] | None = None,
        provider: str | None = None,
        model: str | None = None,
        operation: str | None = None,
        usage_source: str = "platform_reported",
    ) -> None:
        self.mission_dir = Path(mission_dir)
        self.task_id = task_id
        self.label = label
        self.attribution = attribution
        self.attempt = attempt
        self.parent_span_id = parent_span_id
        self.shared_task_ids = list(shared_task_ids or [])
        self.usage_source = usage_source
        self.metadata = {
            field: value
            for field, value in {
                "provider": provider,
                "model": model,
                "operation": operation,
            }.items()
            if value is not None
        }
        self.started_record: dict[str, Any] | None = None
        self.completed_record: dict[str, Any] | None = None
        self._invoked = False

    def _start(self) -> None:
        span: dict[str, Any] = {
            "kind": "model",
            "label": self.label,
            "measurement_source": "host_measured",
            "attribution": self.attribution,
            "attempt": self.attempt,
            "parent_span_id": self.parent_span_id,
        }
        if self.shared_task_ids:
            span["shared_task_ids"] = self.shared_task_ids
        raw: dict[str, Any] = {"task_id": self.task_id, "span": span}
        if self.metadata:
            raw["metadata"] = self.metadata
        self.started_record = start_execution_span(self.mission_dir, raw)

    def _complete(
        self,
        *,
        status: str,
        started_at: str,
        finished_at: str,
        duration_ms: int,
        usage: dict[str, int] | None = None,
    ) -> None:
        if self.started_record is None:
            raise RuntimeError("model call observer was not started")
        raw: dict[str, Any] = {
            "span": {
                "span_id": self.started_record["span"]["span_id"],
                "status": status,
                "started_at": started_at,
                "finished_at": finished_at,
                "duration_ms": duration_ms,
            },
        }
        if usage:
            raw["usage"] = usage
            raw["usage_source"] = self.usage_source
        self.completed_record = record_execution_span(self.mission_dir, raw)

    def invoke(
        self,
        call: Callable[[], T],
        *,
        usage_from_result: Callable[[T], dict[str, int]] | None = None,
    ) -> T:
        """Invoke one model call and return its untouched result.

        Timing begins immediately before ``call`` and stops immediately after it
        returns or raises, excluding trace-file I/O and usage normalization.
        """
        if self._invoked:
            raise RuntimeError("model call observer instances are single-use")
        self._invoked = True
        self._start()
        started_at = now_iso()
        started_clock = time.perf_counter_ns()
        try:
            result = call()
        except BaseException as call_error:
            finished_clock = time.perf_counter_ns()
            finished_at = now_iso()
            try:
                self._complete(
                    status="error",
                    started_at=started_at,
                    finished_at=finished_at,
                    duration_ms=max(0, round((finished_clock - started_clock) / 1_000_000)),
                )
            except Exception as trace_error:
                if hasattr(call_error, "add_note"):
                    call_error.add_note(f"TPlan could not record model-call completion: {trace_error}")
            raise

        finished_clock = time.perf_counter_ns()
        finished_at = now_iso()
        duration_ms = max(0, round((finished_clock - started_clock) / 1_000_000))
        usage: dict[str, int] | None = None
        if usage_from_result is not None:
            try:
                usage = usage_from_result(result)
            except BaseException as usage_error:
                try:
                    self._complete(
                        status="ok",
                        started_at=started_at,
                        finished_at=finished_at,
                        duration_ms=duration_ms,
                    )
                except Exception as trace_error:
                    if hasattr(usage_error, "add_note"):
                        usage_error.add_note(
                            f"TPlan could not record model-call completion: {trace_error}"
                        )
                raise
        self._complete(
            status="ok",
            started_at=started_at,
            finished_at=finished_at,
            duration_ms=duration_ms,
            usage=usage,
        )
        return result
