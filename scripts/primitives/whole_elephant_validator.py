#!/usr/bin/env python3
"""Shared Whole Elephant Protocol audit validator.

This validator only checks whether an agent exposed the required audit fields. It does
not judge semantic truth, definition correctness, evidence sufficiency, or domain value.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "mindthus-whole-elephant-audit-v0.1"
ALLOWED_STRATEGIES = {"weighted_synthesis", "whole_first_re_evaluation"}
ALLOWED_USER_NAMED_OBJECT_RELATIONS = {
    "canonical_object",
    "component_or_interface",
    "umbrella_context",
    "ambiguous_needs_evidence",
}
COMPACT_REQUIRED_STRING_FIELDS = (
    "canonical_object",
    "result_controller",
    "misdirection_if_local_wins",
    "local_frame_wins",
    "whole_object_wins",
    "better_direction_for_target",
)
EXPANDED_STRING_FIELDS = (
    "whole_object",
    "formal_thesis_subject",
    "umbrella_context",
    "subject_alignment_reason",
    "corrected_thesis",
    "primary_value_distribution",
    "control_owner_shift",
    "definition_owner",
    "decision_consequence",
)
OBJECT_HIERARCHY_FIELDS = (
    "user_named_object",
    "whole_object",
    "component_layer",
    "role_layer",
)
WHOLE_OBJECT_RECONSTRUCTION_FIELDS = (
    "target_job",
    "main_use_cases",
    "primary_value_carrier",
    "local_interface_role",
)
FORMAL_ANSWER_PLAN_FIELDS = (
    "opening_core_thesis",
    "canonical_subject",
    "definition_disposition",
    "local_truth_boundary",
    "definition_consequence",
    "optimization_misdirection",
)
DEFINITION_DISPOSITIONS = {
    "grant_as_definition",
    "reject_as_definition",
    "qualify_as_component",
    "blocked_by_missing_evidence",
}
SCRIPT_MUST_NOT_DECIDE = (
    "semantic_truth",
    "definition_correctness",
    "evidence_sufficiency",
    "domain_value",
    "user_authority",
)
INTERNAL_STDOUT_MARKERS = (
    "script_verdict",
    "agentic_judgment_required",
    "script_must_not_decide",
    "Primitive Activation Report",
    "Whole Elephant Protocol Shape Report",
)


def non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def normalize_text(value: Any) -> str:
    return " ".join(str(value).casefold().split())


def normalized_word_tokens(value: Any) -> set[str]:
    tokens = re.findall(r"[a-z0-9]+", normalize_text(value))
    return {token[:-1] if token.endswith("s") else token for token in tokens if len(token) > 2}


def labels_align(user_named_object: Any, canonical_candidate: Any) -> bool:
    user_text = normalize_text(user_named_object)
    candidate_text = normalize_text(canonical_candidate)
    if not user_text or not candidate_text:
        return False
    if user_text == candidate_text or user_text in candidate_text or candidate_text in user_text:
        return True
    user_tokens = normalized_word_tokens(user_named_object)
    candidate_tokens = normalized_word_tokens(canonical_candidate)
    return bool(user_tokens) and user_tokens.issubset(candidate_tokens)


def text_overlap_score(left: Any, right: Any) -> float:
    left_text = normalize_text(left)
    right_text = normalize_text(right)
    if not left_text or not right_text:
        return 0.0
    if left_text == right_text or left_text in right_text or right_text in left_text:
        return 1.0
    left_tokens = normalized_word_tokens(left)
    right_tokens = normalized_word_tokens(right)
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / max(1, min(len(left_tokens), len(right_tokens)))


def thesis_aligns_with_plan(corrected_thesis: Any, opening_core_thesis: Any) -> bool:
    if not non_empty_string(corrected_thesis) or not non_empty_string(opening_core_thesis):
        return True
    return text_overlap_score(corrected_thesis, opening_core_thesis) >= 0.35


def looks_like_rejected_local_interface_granted_definition(
    corrected_thesis: Any, local_interface_role: Any
) -> bool:
    thesis_text = normalize_text(corrected_thesis)
    if not thesis_text:
        return False
    definition_markers = (
        "define",
        "defines",
        "defined by",
        "definition",
        "is carried by",
        "is owned by",
        "本质",
        "定义",
        "定义权",
        "就是",
    )
    if not any(marker in thesis_text for marker in definition_markers):
        return False
    local_text = normalize_text(local_interface_role)
    for delimiter in (" as ", "作为", "当作"):
        if delimiter in local_text:
            local_text = local_text.split(delimiter, 1)[0]
            break
    if local_text:
        escaped_local = re.escape(local_text)
        if re.search(rf"\bnot\b.{{0,30}}\b{escaped_local}\b", thesis_text):
            return False
        if re.search(rf"\b{escaped_local}\b.{{0,20}}\balone\b", thesis_text) and re.search(
            rf"\bnot\b.{{0,30}}\b{escaped_local}\b", thesis_text
        ):
            return False
    local_tokens = normalized_word_tokens(local_text)
    thesis_tokens = normalized_word_tokens(corrected_thesis)
    if local_text and local_text in thesis_text:
        return True
    overlap_count = len(local_tokens & thesis_tokens)
    required_overlap = 1 if len(local_tokens) == 1 else 2
    return overlap_count >= required_overlap


def first_visible_sentence(value: Any) -> str:
    text = str(value).strip()
    if not text:
        return ""
    candidates = [index for mark in (".", "。", "!", "！", "?", "？", "\n") if (index := text.find(mark)) >= 0]
    if not candidates:
        return text
    end = min(candidates)
    return text[: end + 1].strip()


def looks_like_score_concession(value: Any) -> bool:
    text = normalize_text(value)
    return any(marker in text for marker in ("70%", "70分", "half-right", "half right")) or (
        any(marker in text for marker in ("%", "分"))
        and any(marker in text for marker in ("right", "对", "correct", "成立"))
    )


def looks_like_both_sides_concession(value: Any) -> bool:
    text = normalize_text(value)
    return any(
        marker in text
        for marker in (
            "both sides have a point",
            "both sides are right",
            "两边都有道理",
            "双方都有道理",
            "各有道理",
            "都有道理",
        )
    )


def looks_like_soft_not_wrong_concession(value: Any) -> bool:
    text = normalize_text(value)
    return any(
        marker in text
        for marker in (
            "i would not say this claim is wrong",
            "i won't say this claim is wrong",
            "this claim is not wrong",
            "i would not say it is wrong",
            "i won't say it is wrong",
            "我不会说这句话错",
            "不能说它错",
            "不能说这句话错",
            "不是错",
            "不算错",
            "只是还不完整",
            "有道理但不完整",
            "有道理但还不完整",
            "对但不完整",
            "成立但不完整",
            "right but incomplete",
            "valid but incomplete",
            "has a point but incomplete",
            "not wrong but incomplete",
            "not wrong, just incomplete",
            "not wrong, only incomplete",
        )
    )


def exposes_internal_stdout(value: Any) -> bool:
    text = str(value)
    return any(marker in text for marker in INTERNAL_STDOUT_MARKERS)


def looks_like_generic_not_only_caveat(value: Any) -> bool:
    text = normalize_text(value)
    generic_marker = any(
        marker in text
        for marker in (
            "not only",
            "not just",
            "not merely",
            "不只是",
            "不是只有",
            "不仅仅",
            "并非只有",
            "并不只有",
            "并非只是",
            "并不只是",
            "不光是",
            "不单是",
            "不止是",
        )
    )
    if generic_marker:
        return True
    if "也很重要" not in text:
        return False
    return not any(
        marker in text
        for marker in (
            "but only",
            "but just",
            "not definition authority",
            "只是其中一类证据",
            "只是证据",
            "没有定义权",
            "不能拥有定义权",
            "定义权属于",
        )
    )


def looks_like_local_truth_concession_first(value: Any) -> bool:
    text = normalize_text(value)
    if re.match(
        r"^[\w\s-]{0,80}\b(is|are)\s+(a\s+)?(valid|real|strong)\s+(local|visible|partial)\b",
        text,
    ):
        return True
    return text.startswith(
        (
            "prompt injection is a valid",
            "the local signal is valid",
            "the local truth is",
            "local truth is",
            "it is true that",
            "it's true that",
            "you are right that",
            "green tests are important",
            "tests are important",
            "确实",
            "当然很重要",
            "当然很关键",
            "测试通过当然",
            "测试全绿当然",
            "测试当然",
            "对的地方",
            "你说得对",
            "这个说法对",
            "这个判断有道理",
            "这个说法有道理",
            "这句话有道理",
            "有道理但",
            "局部成立",
            "局部上成立",
        )
    )


def looks_like_scope_correction_authority_transfer(value: Any) -> bool:
    text = normalize_text(value)
    scope_markers = (
        "your correction is valid",
        "your correction is right",
        "you are right to correct",
        "你这句纠正是成立",
        "你这个纠正是成立",
        "你纠正得对",
        "严格限定为",
        "限定为",
        "strictly limited to",
        "limited to",
    )
    authority_markers = (
        "core engineering value basically",
        "core value is basically",
        "核心工程价值基本就是",
        "核心价值基本就是",
        "本质就是",
        "本质上就是",
        "basically is",
        "is basically",
        "mostly right",
        "相当准",
        "抓得比我",
        "主要是",
        "primarily",
    )
    return any(marker in text for marker in scope_markers) and any(
        marker in text for marker in authority_markers
    )


def audit_mentions_scope_correction(data: dict[str, Any]) -> bool:
    text_parts: list[str] = []
    for field in (
        "subject_alignment_reason",
        "umbrella_context",
        "control_owner_shift",
        "decision_consequence",
    ):
        value = data.get(field)
        if non_empty_string(value):
            text_parts.append(str(value))
    local_success_points = data.get("local_success_points")
    if isinstance(local_success_points, list):
        text_parts.extend(str(point) for point in local_success_points)
    plan = data.get("formal_answer_plan")
    if isinstance(plan, dict):
        for field in ("opening_core_thesis", "local_truth_boundary", "definition_consequence"):
            value = plan.get(field)
            if non_empty_string(value):
                text_parts.append(str(value))

    text = normalize_text(" ".join(text_parts))
    return any(
        marker in text
        for marker in (
            "scope correction",
            "corrected the previous",
            "previous answer",
            "over-expanded",
            "over expanded",
            "broader agent",
            "broader agent system",
            "agent framing",
            "umbrella subject",
            "umbrella context",
            "not about the broader",
            "not the broader agent",
            "wrongly shifted",
            "corrected an agent-level",
            "纠正",
            "限定",
            "不是更大的",
            "不是更广义",
            "拖大",
            "上提",
            "收回",
        )
    )


def looks_like_scope_correction_object_downgrade(
    user_named_object: Any, labels: tuple[Any, ...]
) -> bool:
    user_text = normalize_text(user_named_object)
    if not user_text:
        return False

    local_carrier_markers = (
        "context artifact",
        "context artifacts",
        "prompt wrapper",
        "attention mechanism",
        "delivery format",
        "context injection",
        "prompt injection",
        "text injection",
        "injection unit",
        "context unit",
        "instruction unit",
        "context/instruction",
        "attention steering",
        "behavior shaping",
        "single metric",
        "metric",
        "test signal",
        "green test",
        "symptom",
        "visible symptom",
        "artifact",
        "implementation detail",
        "local signal",
        "observable signal",
        "上下文工件",
        "提示词包装",
        "注意力机制",
        "交付格式",
        "上下文注入",
        "提示词注入",
        "文本注入",
        "注入单元",
        "上下文单元",
        "指令单元",
        "注意力锚点",
        "行为约束注入",
        "单一指标",
        "指标",
        "测试信号",
        "测试通过",
        "症状",
        "可见症状",
        "工件",
        "产物",
        "实现细节",
        "局部信号",
        "可观察信号",
    )
    if any(marker in user_text for marker in local_carrier_markers):
        return False

    for label in labels:
        label_text = normalize_text(label)
        if not label_text or not labels_align(user_named_object, label):
            continue
        if any(marker in label_text for marker in local_carrier_markers):
            return True
        if re.search(
            r"\bas\b.+\b(context|prompt|attention|delivery|carrier|surface|injection)\b",
            label_text,
        ):
            return True
        if "作为" in label_text and any(
            marker in label_text
            for marker in (
                "上下文",
                "提示词",
                "注意力",
                "交付",
                "载体",
                "表面",
                "注入",
                "指标",
                "测试",
                "症状",
                "工件",
                "产物",
                "实现细节",
                "局部信号",
            )
        ):
            return True
    return False


def looks_like_reduction_accepted_as_corrected_thesis(value: Any) -> bool:
    text = normalize_text(value)
    return any(
        marker in text
        for marker in (
            "the user's reduction is mostly right",
            "user's reduction is mostly right",
            "用户的还原基本正确",
            "用户的归约基本正确",
            "这个还原基本正确",
            "这个归约基本正确",
        )
    )


def looks_like_core_thesis_lacks_authority_shape(value: Any) -> bool:
    text = normalize_text(value)
    if not text:
        return False
    broad_placeholders = (
        "broader view",
        "broader perspective",
        "more complete view",
        "more holistic view",
        "needs a broader",
        "need a broader",
        "更全面的视角",
        "更完整的视角",
        "需要更全面",
    )
    if any(marker in text for marker in broad_placeholders):
        return True
    authority_or_consequence_markers = (
        "defined by",
        "definition authority",
        "definition-level",
        "not definition authority",
        "definition owner",
        "owns the definition",
        "owned by",
        "carried by",
        "carries the",
        "result controller",
        "control surface",
        "control structure",
        "target result",
        "governs",
        "governing",
        "governed by",
        "not by",
        "misdirect",
        "optimization",
        "优化",
        "定义权",
        "定义",
        "属于",
        "承载",
        "主导",
        "控制",
        "只是证据",
        "没有定义权",
        "不能定义",
        "不是定义",
    )
    return not any(marker in text for marker in authority_or_consequence_markers)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_audit(data: Any) -> list[str]:
    findings: list[str] = []
    if not isinstance(data, dict):
        return ["audit root must be an object"]

    if data.get("schema_version") != SCHEMA_VERSION:
        findings.append(f"schema_version must be {SCHEMA_VERSION}")

    for field in COMPACT_REQUIRED_STRING_FIELDS:
        if not non_empty_string(data.get(field)):
            findings.append(f"{field} must be a non-empty string")

    for field in EXPANDED_STRING_FIELDS:
        if field in data and not non_empty_string(data.get(field)):
            findings.append(f"{field} must be a non-empty string")

    raw_plan = data.get("formal_answer_plan")
    raw_disposition = (
        raw_plan.get("definition_disposition") if isinstance(raw_plan, dict) else None
    )
    strategy_choice = data.get("strategy_choice")
    strategy_package_fields = (
        "strategy_choice",
        "variant_map",
        "primary_value_distribution",
        "control_owner_shift",
        "local_success_points",
    )
    has_strategy_package = any(field in data for field in strategy_package_fields)
    has_formal_package = raw_plan is not None or has_strategy_package
    has_subject_alignment_package = (
        data.get("object_hierarchy") is not None
        or data.get("user_named_object_relation") is not None
        or any(field in data for field in ("whole_object", "formal_thesis_subject", "umbrella_context", "subject_alignment_reason"))
    )

    required_expanded_fields: list[str] = []
    if has_subject_alignment_package:
        required_expanded_fields.extend(
            ("whole_object", "formal_thesis_subject", "umbrella_context", "subject_alignment_reason")
        )
    if has_strategy_package:
        required_expanded_fields.extend(
            ("primary_value_distribution", "control_owner_shift", "definition_owner", "decision_consequence")
        )
    if has_formal_package:
        required_expanded_fields.append("corrected_thesis")

    for field in required_expanded_fields:
        if not non_empty_string(data.get(field)):
            findings.append(f"{field} must be a non-empty string")

    variant_map = data.get("variant_map")
    if not isinstance(variant_map, list) or not variant_map:
        if variant_map is not None or has_strategy_package:
            findings.append("variant_map must be a non-empty list")
    elif len(variant_map) < 2 and raw_disposition != "grant_as_definition":
        findings.append("variant_map must include at least two candidate variants")
    elif any(not non_empty_string(item) for item in variant_map):
        findings.append("variant_map must contain only non-empty strings")

    hierarchy = data.get("object_hierarchy")
    if hierarchy is not None:
        if not isinstance(hierarchy, dict):
            findings.append("object_hierarchy must be an object when present")
            hierarchy = {}
        for field in OBJECT_HIERARCHY_FIELDS:
            if not non_empty_string(hierarchy.get(field)):
                findings.append(f"object_hierarchy.{field} must be a non-empty string")
        if (
            non_empty_string(hierarchy.get("whole_object"))
            and non_empty_string(data.get("whole_object"))
            and not labels_align(hierarchy.get("whole_object"), data.get("whole_object"))
        ):
            findings.append("object_hierarchy.whole_object must align with whole_object")
        if (
            non_empty_string(hierarchy.get("whole_object"))
            and non_empty_string(data.get("canonical_object"))
            and not labels_align(hierarchy.get("whole_object"), data.get("canonical_object"))
        ):
            findings.append("object_hierarchy.whole_object must align with canonical_object")

    reconstruction = data.get("whole_object_reconstruction")
    if reconstruction is None:
        if has_strategy_package:
            findings.append("whole_object_reconstruction is required")
        reconstruction = {}
    else:
        if not isinstance(reconstruction, dict):
            findings.append("whole_object_reconstruction must be an object when present")
            reconstruction = {}
        for field in WHOLE_OBJECT_RECONSTRUCTION_FIELDS:
            if not non_empty_string(reconstruction.get(field)):
                findings.append(f"whole_object_reconstruction.{field} must be a non-empty string")
        if (
            non_empty_string(reconstruction.get("primary_value_carrier"))
            and normalize_text(reconstruction.get("primary_value_carrier"))
            == normalize_text(reconstruction.get("local_interface_role"))
            and raw_disposition != "grant_as_definition"
        ):
            findings.append(
                "whole_object_reconstruction.primary_value_carrier must differ from local_interface_role"
            )

    plan = data.get("formal_answer_plan")
    if plan is None:
        if has_strategy_package:
            findings.append("formal_answer_plan is required")
        plan = {}
    else:
        if not isinstance(plan, dict):
            findings.append("formal_answer_plan must be an object when present")
            plan = {}
        for field in FORMAL_ANSWER_PLAN_FIELDS:
            if not non_empty_string(plan.get(field)):
                findings.append(f"formal_answer_plan.{field} must be a non-empty string")
        disposition = plan.get("definition_disposition")
        if non_empty_string(disposition) and disposition not in DEFINITION_DISPOSITIONS:
            choices = ", ".join(sorted(DEFINITION_DISPOSITIONS))
            findings.append(f"formal_answer_plan.definition_disposition must be one of: {choices}")
        if (
            non_empty_string(plan.get("canonical_subject"))
            and non_empty_string(data.get("canonical_object"))
            and normalize_text(plan.get("canonical_subject")) != normalize_text(data.get("canonical_object"))
        ):
            findings.append("formal_answer_plan.canonical_subject must match canonical_object")
        if looks_like_score_concession(plan.get("opening_core_thesis")):
            findings.append("formal_answer_plan.opening_core_thesis must not use score-as-concession framing")
        if looks_like_local_truth_concession_first(plan.get("opening_core_thesis")):
            findings.append(
                "formal_answer_plan.opening_core_thesis must start with the global thesis, not local-truth concession"
            )
        if looks_like_scope_correction_authority_transfer(plan.get("opening_core_thesis")):
            findings.append(
                "formal_answer_plan.opening_core_thesis must not transfer definition authority while correcting scope"
            )
        if looks_like_generic_not_only_caveat(plan.get("opening_core_thesis")):
            findings.append(
                "formal_answer_plan.opening_core_thesis must not over-accommodate local truth as a generic not-only caveat"
            )
        if looks_like_core_thesis_lacks_authority_shape(plan.get("opening_core_thesis")):
            findings.append(
                "formal_answer_plan.opening_core_thesis must carry definition authority, result control, or optimization consequence"
            )
        if looks_like_reduction_accepted_as_corrected_thesis(data.get("corrected_thesis")):
            findings.append("corrected_thesis must not accept a local reduction as the corrected thesis")
        if (
            plan.get("definition_disposition") == "reject_as_definition"
            and not thesis_aligns_with_plan(data.get("corrected_thesis"), plan.get("opening_core_thesis"))
        ):
            findings.append("corrected_thesis must align with formal_answer_plan.opening_core_thesis")
        if (
            plan.get("definition_disposition") == "reject_as_definition"
            and looks_like_rejected_local_interface_granted_definition(
                data.get("corrected_thesis"),
                reconstruction.get("local_interface_role"),
            )
        ):
            findings.append("corrected_thesis must align with formal_answer_plan.opening_core_thesis")
        if looks_like_both_sides_concession(plan.get("local_truth_boundary")):
            findings.append(
                "formal_answer_plan.local_truth_boundary must name the boundary of the local truth, not a both-sides concession"
            )
        if (
            plan.get("definition_disposition") == "reject_as_definition"
            and looks_like_soft_not_wrong_concession(plan.get("opening_core_thesis"))
        ):
            findings.append(
                "formal_answer_plan.opening_core_thesis must not soften a rejected definition into a not-wrong concession"
            )
        forbidden = plan.get("forbidden_answer_forms")
        if not isinstance(forbidden, list) or not forbidden:
            findings.append("formal_answer_plan.forbidden_answer_forms must be a non-empty list")
        elif any(not non_empty_string(item) for item in forbidden):
            findings.append("formal_answer_plan.forbidden_answer_forms must contain only non-empty strings")

    visible_answer = data.get("visible_formal_answer")
    if visible_answer is not None:
        if not non_empty_string(visible_answer):
            findings.append("visible_formal_answer must be a non-empty string when present")
        else:
            first_sentence = first_visible_sentence(visible_answer)
            opening = plan.get("opening_core_thesis")
            if non_empty_string(opening) and not normalize_text(first_sentence).startswith(
                normalize_text(opening)
            ):
                findings.append(
                    "visible_formal_answer first sentence must start with formal_answer_plan.opening_core_thesis"
                )
            if exposes_internal_stdout(visible_answer):
                findings.append("visible_formal_answer must not expose internal script stdout")
            if looks_like_local_truth_concession_first(first_sentence):
                findings.append(
                    "visible_formal_answer first sentence must start with the global thesis, not local-truth concession"
                )
            if looks_like_score_concession(visible_answer):
                findings.append("visible_formal_answer must not use score-as-concession framing")
            if looks_like_soft_not_wrong_concession(visible_answer):
                findings.append(
                    "visible_formal_answer must not soften a rejected definition into a not-wrong concession"
                )
            if looks_like_generic_not_only_caveat(first_sentence):
                findings.append("visible_formal_answer first sentence must not be a generic not-only caveat")

    local_success_points = data.get("local_success_points")
    if local_success_points is None:
        if has_strategy_package:
            findings.append("local_success_points must be a non-empty list")
    else:
        if not isinstance(local_success_points, list) or not local_success_points:
            findings.append("local_success_points must be a non-empty list")
        elif any(not non_empty_string(point) for point in local_success_points):
            findings.append("local_success_points must contain only non-empty strings")

    if strategy_choice is None:
        if has_strategy_package:
            choices = ", ".join(sorted(ALLOWED_STRATEGIES))
            findings.append(f"strategy_choice must be one of: {choices}")
    elif strategy_choice not in ALLOWED_STRATEGIES:
        choices = ", ".join(sorted(ALLOWED_STRATEGIES))
        findings.append(f"strategy_choice must be one of: {choices}")

    user_named_object_relation = data.get("user_named_object_relation")
    if user_named_object_relation is None:
        if has_strategy_package:
            choices = ", ".join(sorted(ALLOWED_USER_NAMED_OBJECT_RELATIONS))
            findings.append(f"user_named_object_relation must be one of: {choices}")
    elif user_named_object_relation not in ALLOWED_USER_NAMED_OBJECT_RELATIONS:
        choices = ", ".join(sorted(ALLOWED_USER_NAMED_OBJECT_RELATIONS))
        findings.append(f"user_named_object_relation must be one of: {choices}")
    elif user_named_object_relation == "canonical_object" and isinstance(hierarchy, dict):
        user_named = hierarchy.get("user_named_object")
        canonical_candidates = (
            data.get("canonical_object"),
            data.get("whole_object"),
            data.get("formal_thesis_subject"),
        )
        if not any(labels_align(user_named, candidate) for candidate in canonical_candidates):
            findings.append(
                "user_named_object_relation cannot be canonical_object when user_named_object is not aligned with canonical_object"
            )
        if audit_mentions_scope_correction(data) and looks_like_scope_correction_object_downgrade(
            user_named,
            (
                data.get("canonical_object"),
                data.get("whole_object"),
                data.get("formal_thesis_subject"),
                hierarchy.get("whole_object"),
            ),
        ):
            findings.append(
                "canonical_object must not downgrade the user-named object into a local carrier after scope correction"
            )

    return findings


def build_report(path: Path, data: Any, findings: list[str]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "path": str(path),
        "script_verdict": "shape_only_failed" if findings else "shape_only",
        "agentic_judgment_required": True,
        "findings": findings,
        "script_must_not_decide": list(SCRIPT_MUST_NOT_DECIDE),
        "observed_fields": sorted(data) if isinstance(data, dict) else [],
    }


def print_text_report(report: dict[str, Any]) -> None:
    print("Whole Elephant Protocol Shape Report")
    print(f"path: {report['path']}")
    if report["findings"]:
        for finding in report["findings"]:
            print(f"- BLOCK [invalid-audit]: {finding}")
    else:
        print("- OK [shape]: required audit fields are present")
    print(f"script_verdict: {report['script_verdict']}")
    print("agentic_judgment_required: true")
    print("script_must_not_decide: " + ", ".join(report["script_must_not_decide"]))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Whole Elephant Protocol audit shape.")
    parser.add_argument("path", help="Path to a Whole Elephant audit JSON file.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    path = Path(args.path)
    try:
        data = load_json(path)
    except (OSError, json.JSONDecodeError) as exc:
        data = {}
        findings = [f"audit-read-failed: {exc}"]
    else:
        findings = validate_audit(data)

    report = build_report(path, data, findings)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_text_report(report)
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
