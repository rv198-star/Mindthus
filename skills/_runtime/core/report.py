"""Adapter-neutral report primitives.

Reports expose shape and evidence risks. They do not validate semantic truth.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    message: str
    subject: str = ""


def finding(severity: str, code: str, message: str, subject: str = "") -> Finding:
    return Finding(severity, code, message, subject)


def print_shape_report(
    *,
    title: str,
    path: Path,
    findings: list[Finding],
    truth_boundary: str,
    accepted_exit: str = "",
    no_risks_message: str = "No shape or evidence risks detected.",
) -> None:
    print(title)
    print(f"Path: {path}")
    print()
    if accepted_exit:
        print(f"method exit accepted: {accepted_exit}")
        print()

    if not findings:
        print(no_risks_message)
    else:
        for item in findings:
            subject = f" [{item.subject}]" if item.subject else ""
            print(f"- {item.severity.upper()} [{item.code}]{subject}: {item.message}")

    print()
    print(f"Reminder: agentic audit remains required; this report does not validate {truth_boundary}.")

