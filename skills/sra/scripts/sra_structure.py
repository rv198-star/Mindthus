"""Validate the bounded Schema vocabulary emitted by SRA, using that same schema.

This is deliberately not a general JSON Schema implementation. Unsupported schema
keywords fail closed even in branches that the current instance does not exercise.
Semantic resource and authorization rules remain in the domain validators.
"""
from __future__ import annotations

import math
import re
from typing import Any

KEYWORDS = frozenset({
    "$schema", "title", "description", "type", "properties", "required",
    "additionalProperties", "items", "minItems", "maxItems", "uniqueItems",
    "const", "enum", "oneOf", "anyOf", "not", "minLength", "maxLength",
    "pattern", "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum",
})
TYPES = {"object", "array", "string", "boolean", "number", "integer", "null"}


def _equal(left: Any, right: Any) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(_equal(left[k], right[k]) for k in left)
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(_equal(a, b) for a, b in zip(left, right))
    return left == right


def schema_findings(schema: Any, path: str = "schema") -> list[str]:
    if not isinstance(schema, dict):
        return [f"{path} must be a supported schema object"]
    errors = [f"{path}: unsupported schema keyword {key}" for key in sorted(set(schema) - KEYWORDS)]
    if "type" in schema and (not isinstance(schema["type"], str) or schema["type"] not in TYPES):
        errors.append(f"{path}: unsupported schema type")
    for key in ("properties",):
        if key in schema:
            if not isinstance(schema[key], dict):
                errors.append(f"{path}.{key} must be an object")
            else:
                for name, child in schema[key].items():
                    errors.extend(schema_findings(child, f"{path}.{key}.{name}"))
    for key in ("items", "not"):
        if key in schema:
            errors.extend(schema_findings(schema[key], f"{path}.{key}"))
    for key in ("oneOf", "anyOf"):
        if key in schema:
            choices = schema[key]
            if not isinstance(choices, list) or not choices:
                errors.append(f"{path}.{key} must contain schema variants")
            else:
                for index, child in enumerate(choices):
                    errors.extend(schema_findings(child, f"{path}.{key}[{index}]"))
    if "additionalProperties" in schema and not isinstance(schema["additionalProperties"], bool):
        errors.append(f"{path}: only boolean additionalProperties is supported")
    return errors


def _instance_findings(value: Any, schema: dict[str, Any], path: str) -> list[str]:
    errors: list[str] = []
    for branch in ("oneOf", "anyOf"):
        if branch not in schema:
            continue
        reports = [_instance_findings(value, variant, path) for variant in schema[branch]]
        matches = sum(not report for report in reports)
        if (branch == "oneOf" and matches != 1) or (branch == "anyOf" and matches == 0):
            errors.append(f"{path}: {branch} requires {'exactly one' if branch == 'oneOf' else 'a'} valid variant")
            if reports:
                errors.extend(min(reports, key=len))
    if "not" in schema and not _instance_findings(value, schema["not"], path):
        errors.append(f"{path}: value uses a reserved or excluded variant")
    expected = schema.get("type")
    numeric = isinstance(value, (int, float)) and not isinstance(value, bool)
    finite = numeric and (isinstance(value, int) or math.isfinite(value))
    valid_type = {
        "object": isinstance(value, dict), "array": isinstance(value, list),
        "string": isinstance(value, str), "boolean": isinstance(value, bool),
        "number": finite, "integer": finite and value == int(value),
        "null": value is None,
    }
    if expected is not None and not valid_type[expected]:
        return errors + [f"{path} must be {expected} (numbers must be finite; bool is not a number)"]
    if "const" in schema and not _equal(value, schema["const"]):
        constant = str(schema["const"]).lower() if isinstance(schema["const"], bool) else repr(schema["const"])
        errors.append(f"{path} must be {constant}")
    if "enum" in schema and not any(_equal(value, allowed) for allowed in schema["enum"]):
        errors.append(f"{path} contains an unsupported enum value: {value!r}")
    if isinstance(value, dict):
        props = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path}.{key} is a required field")
        if schema.get("additionalProperties") is False:
            for key in sorted(set(value) - set(props)):
                errors.append(f"{path}.{key} is an unsupported field")
        for key in value.keys() & props.keys():
            errors.extend(_instance_findings(value[key], props[key], f"{path}.{key}"))
    elif isinstance(value, list):
        for keyword, predicate in (("minItems", lambda n: len(value) >= n), ("maxItems", lambda n: len(value) <= n)):
            if keyword in schema and not predicate(schema[keyword]):
                errors.append(f"{path} violates {keyword}={schema[keyword]}")
        if schema.get("uniqueItems") and any(_equal(value[i], value[j]) for i in range(len(value)) for j in range(i)):
            errors.append(f"{path} contains duplicate items")
        if "items" in schema:
            for index, item in enumerate(value):
                errors.extend(_instance_findings(item, schema["items"], f"{path}[{index}]"))
    elif isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            errors.append(f"{path} must be a non-empty string of the required length")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            errors.append(f"{path} exceeds maxLength")
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            errors.append(f"{path} does not match pattern")
    elif finite:
        for key, valid in (("minimum", lambda n: value >= n), ("maximum", lambda n: value <= n),
                           ("exclusiveMinimum", lambda n: value > n), ("exclusiveMaximum", lambda n: value < n)):
            if key in schema and not valid(schema[key]):
                errors.append(f"{path} violates {key}={schema[key]}")
    return errors


def validate_structure(value: Any, schema: dict[str, Any], path: str = "judgment") -> list[str]:
    """Return shape findings without mutating either the value or its schema."""
    errors = schema_findings(schema)
    return errors or _instance_findings(value, schema, path)
