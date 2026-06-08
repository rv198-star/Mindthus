"""Adapter-neutral shape primitives.

These helpers validate data shape only. They do not validate semantic truth.
"""

from __future__ import annotations

from typing import Any, Iterable

from _runtime.core.report import Finding, finding


def non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def findings_from_messages(
    messages: Iterable[str],
    *,
    severity: str = "block",
    code: str = "invalid-shape",
    subject: str = "",
) -> list[Finding]:
    return [finding(severity, code, message, subject) for message in messages]


def require_object(value: Any, message: str) -> list[Finding]:
    if isinstance(value, dict):
        return []
    return [finding("block", "invalid-root", message)]


def require_fields(data: dict[str, Any], fields: Iterable[str], message_prefix: str = "missing field") -> list[Finding]:
    return [
        finding("block", "missing-field", f"{message_prefix}: {field}")
        for field in fields
        if field not in data
    ]


def require_string_field(
    findings: list[Finding],
    data: dict[str, Any],
    field: str,
    *,
    missing_message: str,
    invalid_message: str,
) -> None:
    if field not in data:
        findings.append(finding("block", "missing-field", missing_message))
    elif not isinstance(data.get(field), str):
        findings.append(finding("block", "invalid-field", invalid_message))


def require_bool_field(findings: list[Finding], data: dict[str, Any], field: str, message: str) -> None:
    if not isinstance(data.get(field), bool):
        findings.append(finding("block", "invalid-field", message))


def require_list_field(findings: list[Finding], data: dict[str, Any], field: str, message: str) -> None:
    if not isinstance(data.get(field), list):
        findings.append(finding("block", "invalid-field", message))


def require_int_range(
    findings: list[Finding],
    value: Any,
    *,
    minimum: int,
    maximum: int,
    message: str,
) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        findings.append(finding("block", "invalid-field", message))


def require_enum_value(
    findings: list[Finding],
    value: Any,
    allowed: set[str],
    *,
    type_message: str,
    unsupported_message: str,
) -> None:
    if not isinstance(value, str):
        findings.append(finding("block", "invalid-field", type_message))
    elif value not in allowed:
        findings.append(finding("block", "unsupported-enum", unsupported_message))
