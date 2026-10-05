"""Behavioral contracts for optional work estimates and their runtime boundary."""

import copy
import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "skills" / "tplan" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import tplan_runtime
from outcome_attribution import build_outcome_attribution
from work_plan import build_work_view, read_work_view_snapshot, validate_work_plan


SCHEMA_VERSION = "tplan.work_plan.v0.1"
ABSENT = object()


def task_inputs():
    return [
        {
            "id": "T1",
            "title": "Deliver the report",
            "role": "success-critical",
            "mission_contribution": "Produces the report required by A1.",
            "acceptance_evidence": ["A1"],
        },
        {
            "id": "S1",
            "parent_id": "T1",
            "title": "Collect evidence",
            "role": "supporting",
            "parent_contribution": "Provides the report's evidence.",
            "parent_acceptance": "The evidence is available to the report.",
            "mission_trace": "via T1 -> A1",
        },
        {
            "id": "P1",
            "parent_id": "S1",
            "kind": "step",
            "title": "Read the source",
            "role": "supporting",
            "parent_contribution": "Supplies the source facts.",
            "mission_trace": "via S1 -> T1 -> A1",
            "step_action": "Read the source facts.",
            "done_condition": "The source facts have been recorded.",
        },
        {
            "id": "S2",
            "parent_id": "T1",
            "title": "Draft the report",
            "role": "supporting",
            "parent_contribution": "Turns the evidence into the report.",
            "parent_acceptance": "The report is ready for review.",
            "mission_trace": "via T1 -> A1",
        },
        {
            "id": "T2",
            "title": "Review the report",
            "role": "success-critical",
            "mission_contribution": "Verifies the result required by A1.",
            "acceptance_evidence": ["A1"],
        },
    ]


def mission_arguments():
    return {
        "mission_id": "work-plan",
        "title": "Work Plan Mission",
        "objective": "Explain declared work without inventing verified progress.",
        "acceptance_evidence": [
            {"id": "A1", "description": "The report meets its acceptance criteria."}
        ],
        "human_in_loop": 0,
        "risk_tolerance": 50,
        "resource_sufficiency": 60,
        "tasks": task_inputs(),
    }


def mission_state(plan=ABSENT):
    # Unit fixtures do not read a runtime fingerprint or initialize a directory.
    args = mission_arguments()
    raw_tasks = args["tasks"]
    by_id = {task["id"]: task for task in raw_tasks}
    mission = {
        "schema_version": "tplan.v0.1",
        "mission": {
            key: value
            for key, value in args.items()
            if key not in {"tasks", "mission_id"}
        },
        "tasks": [
            tplan_runtime.normalize_task(task, raw_tasks_by_id=by_id)
            for task in raw_tasks
        ],
        "active_task_id": None,
    }
    mission["mission"]["id"] = args["mission_id"]
    mission["mission"]["status"] = "active"
    if plan is not ABSENT:
        mission["work_plan"] = copy.deepcopy(plan)
    return mission


def estimate(low, high=None, unit="hours"):
    return {
        "low": low,
        "high": low if high is None else high,
        "unit": unit,
        "basis": "A source owner's current estimate of the remaining work.",
        "confidence": "medium",
    }


def work_plan(blocks=None, **overrides):
    result = {
        "schema_version": SCHEMA_VERSION,
        "coverage": "complete",
        "scope_note": "All remaining report delivery and review work.",
        "blocks": (
            [
                {"task_id": "T1", "remaining": estimate(1, 2)},
                {"task_id": "T2", "remaining": estimate(3, 6)},
            ]
            if blocks is None
            else copy.deepcopy(blocks)
        ),
        "as_of": "2026-10-05T10:00:00Z",
        "source": "The report owner",
    }
    result.update(copy.deepcopy(overrides))
    return result


def rows_by_id(view):
    return {row["task_id"]: row for row in view["blocks"]}


def run_script(script_name, *args):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script_name), *map(str, args)],
        text=True,
        capture_output=True,
    )


def read_jsonl(path):
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def read_mission(mission_dir):
    return json.loads((mission_dir / "mission.json").read_text(encoding="utf-8"))


def artifact_snapshot(mission_dir):
    # Include mtimes: rewriting identical bytes is still a write for a no-op.
    return {
        str(path.relative_to(mission_dir)): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in mission_dir.rglob("*")
        if path.is_file() and path.name != ".execution_trace.lock"
    }


def create_mission(tmp):
    mission_dir = Path(tmp) / "work-plan"
    mission_dir.mkdir()
    mission = tplan_runtime.build_mission(**mission_arguments())
    tplan_runtime.write_mission(mission_dir, mission)
    (mission_dir / "evidence.jsonl").write_text("", encoding="utf-8")
    tplan_runtime.initialize_execution_trace(mission_dir, mission)
    return mission_dir


class WorkPlanValidationTests(unittest.TestCase):
    def assert_invalid(self, plan):
        errors = validate_work_plan(mission_state(), plan)
        self.assertIsInstance(errors, list)
        self.assertTrue(errors, "The invalid plan was accepted.")
        self.assertTrue(all(isinstance(error, str) and error for error in errors))

    def test_valid_plan_accepts_ranges_null_unknowns_and_summary_only_context(self):
        plan = work_plan(
            [
                {
                    "task_id": "T1",
                    "remaining": None,
                    "depends_on": None,
                    "parallel_conditions": None,
                },
                {
                    "task_id": "T2",
                    "remaining": estimate(3, 6),
                    "depends_on": ["T1"],
                    "parallel_conditions": ["The reviewer must be available."],
                },
            ],
            risks=[{"summary": "Source access may expire."}],
            blockers=[{"summary": "Waiting for the source owner."}],
        )
        original = copy.deepcopy(plan)
        self.assertEqual(validate_work_plan(mission_state(), plan), [])
        self.assertEqual(plan, original)

    def test_non_string_object_keys_return_validation_errors_instead_of_type_errors(self):
        for location in ("plan", "block", "remaining", "risk"):
            with self.subTest(location=location):
                plan = work_plan(risks=[{"summary": "A current concern."}])
                target = {
                    "plan": plan,
                    "block": plan["blocks"][0],
                    "remaining": plan["blocks"][0]["remaining"],
                    "risk": plan["risks"][0],
                }[location]
                target[1] = "An invalid Python API field name."
                self.assert_invalid(plan)

    def test_ranges_reject_negative_boolean_nonfinite_and_reversed_values(self):
        cases = [
            ("negative low", -1, 2),
            ("negative high", 0, -1),
            ("boolean low", True, 2),
            ("boolean high", 0, False),
            ("nan low", math.nan, 2),
            ("nan high", 0, math.nan),
            ("infinite low", math.inf, math.inf),
            ("infinite high", 0, math.inf),
            ("negative infinity", -math.inf, 2),
            ("reversed range", 3, 2),
            ("numeric string", "1", 2),
        ]
        for name, low, high in cases:
            with self.subTest(case=name):
                self.assert_invalid(
                    work_plan([{"task_id": "T1", "remaining": estimate(low, high)}])
                )

    def test_ranges_require_units_basis_and_a_valid_optional_confidence(self):
        for field, value in [
            ("unit", ""),
            ("unit", 12),
            ("basis", " "),
            ("confidence", "certain"),
        ]:
            with self.subTest(field=field, value=value):
                remaining = estimate(1, 2)
                remaining[field] = value
                self.assert_invalid(
                    work_plan([{"task_id": "T1", "remaining": remaining}])
                )

    def test_block_ids_are_real_unique_and_do_not_overlap_ancestors(self):
        cases = {
            "unknown task": [{"task_id": "missing"}],
            "duplicate task": [{"task_id": "T1"}, {"task_id": "T1"}],
            "parent and child": [{"task_id": "T1"}, {"task_id": "S1"}],
            "parent and grandchild": [{"task_id": "T1"}, {"task_id": "P1"}],
        }
        for name, blocks in cases.items():
            with self.subTest(case=name):
                self.assert_invalid(work_plan(blocks, coverage="partial"))

    def test_dependency_references_self_edges_and_cycles_are_rejected(self):
        cases = {
            "unknown dependency": [
                {"task_id": "T1", "depends_on": ["missing"]},
                {"task_id": "T2"},
            ],
            "self dependency": [
                {"task_id": "T1", "depends_on": ["T1"]},
                {"task_id": "T2"},
            ],
            "cycle": [
                {"task_id": "T1", "depends_on": ["T2"]},
                {"task_id": "T2", "depends_on": ["T1"]},
            ],
        }
        for name, blocks in cases.items():
            with self.subTest(case=name):
                self.assert_invalid(work_plan(blocks))

    def test_summary_and_optional_context_task_references_are_validated(self):
        for context_key in ("risks", "blockers"):
            for value in [
                {},
                {"summary": ""},
                {"summary": "A real concern.", "task_ids": ["missing"]},
            ]:
                with self.subTest(context=context_key, value=value):
                    self.assert_invalid(work_plan(**{context_key: [value]}))

    def test_declared_progress_requires_a_finite_value_and_source_basis(self):
        for value, basis in [(True, "Owner declaration"), (math.nan, "Owner declaration"),
                             (math.inf, "Owner declaration"), (25, "")]:
            with self.subTest(value=value, basis=basis):
                self.assert_invalid(
                    work_plan(
                        progress={
                            "label": "Reviewed coverage",
                            "value": value,
                            "unit": "percent",
                            "basis": basis,
                        }
                    )
                )


class WorkViewTests(unittest.TestCase):
    def test_no_plan_uses_real_roots_and_preserves_unknown_work_and_progress(self):
        mission = mission_state()
        view = build_work_view(mission)
        self.assertFalse(view["planning"]["present"])
        self.assertIsNone(view["progress"])
        self.assertEqual(set(rows_by_id(view)), {"T1", "T2"})
        self.assertIsNone(view["remaining"]["total"])
        self.assertEqual(set(view["remaining"]["unknown_task_ids"]), {"T1", "T2"})
        for row in view["blocks"]:
            self.assertIsNone(row["remaining"])
            self.assertIsNone(row["remaining_share"])
            self.assertIsNone(row["depends_on"])
            self.assertEqual(row["dependency_status"], "unknown")
        self.assertEqual(view["risks"], [])
        self.assertEqual(view["blockers"], [])
        self.assertTrue(view["limitations"])

    def test_unequal_ranges_aggregate_once_and_produce_conservative_remaining_shares(self):
        view = build_work_view(mission_state(work_plan()))
        self.assertEqual(set(rows_by_id(view)), {"T1", "T2"})
        self.assertEqual(
            view["remaining"]["total"], {"low": 4, "high": 8, "unit": "hours"}
        )
        shares = {key: row["remaining_share"] for key, row in rows_by_id(view).items()}
        self.assertAlmostEqual(shares["T1"]["low"], 100 / 7, delta=0.1)
        self.assertAlmostEqual(shares["T1"]["high"], 40, delta=0.1)
        self.assertAlmostEqual(shares["T2"]["low"], 60, delta=0.1)
        self.assertAlmostEqual(shares["T2"]["high"], 600 / 7, delta=0.1)
        for share in shares.values():
            self.assertEqual(share["unit"], "percent")
            self.assertEqual(share["denominator_unit"], "hours")
            self.assertTrue(share["basis"])
        self.assertIsNone(view["progress"])

    def test_large_finite_totals_do_not_overflow_intermediate_share_denominators(self):
        plan = work_plan([
            {"task_id": "T1", "remaining": estimate(8e307)},
            {"task_id": "T2", "remaining": estimate(8e307)},
        ])
        self.assertEqual(validate_work_plan(mission_state(), plan), [])
        view = build_work_view(mission_state(plan))
        self.assertEqual(
            view["remaining"]["total"], {"low": 1.6e308, "high": 1.6e308, "unit": "hours"}
        )
        for row in view["blocks"]:
            self.assertAlmostEqual(row["remaining_share"]["low"], 50)
            self.assertAlmostEqual(row["remaining_share"]["high"], 50)

    def test_partial_plan_adds_an_uncovered_frontier_without_parent_child_double_counting(self):
        plan = work_plan(
            [{"task_id": "S1", "remaining": estimate(2, 4)}],
            coverage="partial",
            scope_note="Only evidence collection has been estimated.",
        )
        view = build_work_view(mission_state(plan))
        rows = rows_by_id(view)
        self.assertEqual(set(rows), {"S1", "S2", "T2"})
        self.assertIsNone(view["remaining"]["total"])
        self.assertEqual(set(view["remaining"]["uncovered_task_ids"]), {"S2", "T2"})
        self.assertEqual(set(view["remaining"]["unknown_task_ids"]), {"S2", "T2"})
        self.assertIsNone(view["progress"])
        for task_id in ("S2", "T2"):
            self.assertIsNone(rows[task_id]["remaining"])
            self.assertIsNone(rows[task_id]["remaining_share"])
        # A subtotal share is allowed only if its restricted denominator is visible.
        share = rows["S1"]["remaining_share"]
        if share is not None:
            self.assertNotEqual(share["coverage"], "complete")
            self.assertEqual(share["denominator_unit"], "hours")
            self.assertTrue(share["basis"])

    def test_mixed_units_keep_separate_totals_and_have_no_global_total(self):
        plan = work_plan(
            [
                {"task_id": "T1", "remaining": estimate(2, 4, "hours")},
                {"task_id": "T2", "remaining": estimate(100, 200, "tokens")},
            ]
        )
        view = build_work_view(mission_state(plan))
        self.assertIsNone(view["remaining"]["total"])
        totals = {item["unit"]: item for item in view["remaining"]["totals_by_unit"]}
        self.assertEqual(set(totals), {"hours", "tokens"})
        self.assertEqual((totals["hours"]["low"], totals["hours"]["high"]), (2, 4))
        self.assertEqual((totals["tokens"]["low"], totals["tokens"]["high"]), (100, 200))
        self.assertEqual(totals["hours"]["task_ids"], ["T1"])
        self.assertEqual(totals["tokens"]["task_ids"], ["T2"])
        for row in view["blocks"]:
            if row["remaining_share"] is not None:
                self.assertEqual(
                    row["remaining_share"]["denominator_unit"], row["remaining"]["unit"]
                )
                self.assertTrue(row["remaining_share"]["basis"])
        self.assertIsNone(view["progress"])

    def test_omitted_and_null_estimates_are_unknown_while_explicit_zero_is_known(self):
        unknown = build_work_view(
            mission_state(work_plan([{"task_id": "T1"}, {"task_id": "T2", "remaining": None}]))
        )
        self.assertIsNone(unknown["remaining"]["total"])
        self.assertEqual(set(unknown["remaining"]["unknown_task_ids"]), {"T1", "T2"})
        self.assertTrue(all(row["remaining_share"] is None for row in unknown["blocks"]))
        zero = build_work_view(
            mission_state(
                work_plan(
                    [
                        {"task_id": "T1", "remaining": estimate(0)},
                        {"task_id": "T2", "remaining": estimate(0)},
                    ]
                )
            )
        )
        self.assertEqual(zero["remaining"]["total"], {"low": 0, "high": 0, "unit": "hours"})
        self.assertEqual(zero["remaining"]["unknown_task_ids"], [])
        self.assertTrue(all(row["remaining_share"] is None for row in zero["blocks"]))
        self.assertIsNone(zero["progress"])

    def test_explicitly_removed_blocks_keep_source_estimates_but_do_not_count_as_current_work(self):
        for status in ("pruned", "abandoned", "superseded"):
            with self.subTest(status=status):
                mission = mission_state(work_plan())
                next(task for task in mission["tasks"] if task["id"] == "T2")["status"] = status
                view = build_work_view(mission)
                row = rows_by_id(view)["T2"]
                self.assertFalse(row["is_remaining"])
                self.assertIsNone(row["remaining_share"])
                self.assertEqual(row["remaining"], estimate(3, 6))
                self.assertNotIn("T2", view["remaining"]["unknown_task_ids"])
                self.assertNotIn("T2", view["remaining"]["unresolved_task_ids"])
                self.assertEqual(
                    view["remaining"]["total"], {"low": 1, "high": 2, "unit": "hours"}
                )
                self.assertIsNone(view["progress"])

    def test_completed_block_with_positive_remaining_stays_uncertain_even_with_acceptance(self):
        for qualified in (False, True):
            with self.subTest(qualified_acceptance=qualified):
                mission = mission_state(work_plan())
                next(task for task in mission["tasks"] if task["id"] == "T2")["status"] = "completed"
                events = []
                if qualified:
                    events.append({
                        "id": "Eacceptance",
                        "timestamp": "2026-10-05T10:01:00Z",
                        "event_type": "acceptance_passed",
                        "task_id": "T2",
                        "summary": "The existing acceptance contract passed.",
                        "payload": {"acceptance_ids": ["A1"]},
                    })
                attribution = build_outcome_attribution(mission, events)
                self.assertEqual(
                    bool(attribution["tasks"]["T2"]["countable_progress"]), qualified
                )
                view = build_work_view(
                    mission, evidence=events, outcome_attribution=attribution
                )
                row = rows_by_id(view)["T2"]
                self.assertTrue(row["remaining_uncertain"])
                self.assertTrue(row["uncertainty_reasons"])
                self.assertEqual(row["remaining"], estimate(3, 6))
                self.assertIn("T2", view["remaining"]["unresolved_task_ids"])
                self.assertNotIn("T2", view["remaining"]["unknown_task_ids"])
                self.assertIsNone(view["remaining"]["total"])
                self.assertNotEqual(view["remaining"]["coverage"], "complete")
                subtotal = next(
                    item for item in view["remaining"]["totals_by_unit"] if item["unit"] == "hours"
                )
                self.assertEqual((subtotal["low"], subtotal["high"]), (4, 8))
                self.assertIsNone(view["progress"])

    def test_completed_block_without_estimate_or_qualified_evidence_is_not_zero_remaining(self):
        mission = mission_state(
            work_plan([
                {"task_id": "T1", "remaining": estimate(1, 2)},
                {"task_id": "T2"},
            ])
        )
        next(task for task in mission["tasks"] if task["id"] == "T2")["status"] = "completed"
        events = [{
            "id": "Elegacy",
            "timestamp": "2026-10-05T10:01:00Z",
            "event_type": "acceptance",
            "task_id": "T2",
            "summary": "A legacy completion claim without acceptance references.",
            "payload": {},
        }]
        attribution = build_outcome_attribution(mission, events)
        self.assertEqual(attribution["tasks"]["T2"]["countable_progress"], [])
        view = build_work_view(mission, evidence=events, outcome_attribution=attribution)
        row = rows_by_id(view)["T2"]
        self.assertTrue(row["remaining_uncertain"])
        self.assertTrue(row["uncertainty_reasons"])
        self.assertIsNone(row["remaining"])
        self.assertIsNone(row["remaining_share"])
        self.assertIn("T2", view["remaining"]["unresolved_task_ids"])
        self.assertIn("T2", view["remaining"]["unknown_task_ids"])
        self.assertIsNone(view["remaining"]["total"])

    def test_completed_block_with_zero_remaining_and_qualified_acceptance_can_close(self):
        mission = mission_state(
            work_plan([
                {"task_id": "T1", "remaining": estimate(1, 2)},
                {"task_id": "T2", "remaining": estimate(0)},
            ])
        )
        next(task for task in mission["tasks"] if task["id"] == "T2")["status"] = "completed"
        events = [{
            "id": "Eacceptance",
            "timestamp": "2026-10-05T10:01:00Z",
            "event_type": "acceptance_passed",
            "task_id": "T2",
            "summary": "The report passed the declared acceptance.",
            "payload": {"acceptance_ids": ["A1"]},
        }]
        attribution = build_outcome_attribution(mission, events)
        self.assertTrue(attribution["tasks"]["T2"]["countable_progress"])
        view = build_work_view(mission, evidence=events, outcome_attribution=attribution)
        row = rows_by_id(view)["T2"]
        self.assertFalse(row["remaining_uncertain"])
        self.assertFalse(row["is_remaining"])
        self.assertIsNone(row["remaining_share"])
        self.assertNotIn("T2", view["remaining"]["unresolved_task_ids"])
        self.assertEqual(
            view["remaining"]["total"], {"low": 1, "high": 2, "unit": "hours"}
        )

    def test_completed_root_does_not_hide_unfinished_descendants(self):
        mission = mission_state(work_plan())
        next(task for task in mission["tasks"] if task["id"] == "T1")["status"] = "completed"
        self.assertEqual(tplan_runtime.validate_mission(mission), [])
        attribution = build_outcome_attribution(mission, [])
        view = build_work_view(mission, evidence=[], outcome_attribution=attribution)
        rows = rows_by_id(view)
        self.assertTrue({"S1", "S2"}.issubset(rows))
        for task_id in ("S1", "S2"):
            self.assertTrue(rows[task_id]["is_remaining"])
            self.assertIsNone(rows[task_id]["remaining"])
            self.assertIn(task_id, view["remaining"]["unknown_task_ids"])
        self.assertTrue(view["diagnostics"])
        self.assertIsNone(view["remaining"]["total"])

    def test_closed_planned_children_do_not_hide_their_unfinished_parent(self):
        plan = work_plan([
            {"task_id": task_id, "remaining": estimate(1)}
            for task_id in ("S1", "S2", "T2")
        ])
        mission = mission_state(plan)
        for task in mission["tasks"]:
            if task["id"] != "T1":
                task["status"] = "completed"
        self.assertEqual(tplan_runtime.validate_mission(mission), [])
        attribution = build_outcome_attribution(mission, [])
        view = build_work_view(mission, evidence=[], outcome_attribution=attribution)
        self.assertIn("T1", rows_by_id(view))
        self.assertTrue(rows_by_id(view)["T1"]["is_remaining"])
        self.assertIn("T1", view["remaining"]["unknown_task_ids"])
        self.assertIsNone(view["remaining"]["total"])

    def test_progress_is_only_the_source_declaration_and_inputs_remain_unchanged(self):
        declared = {
            "label": "Reviewed acceptance coverage",
            "value": 23,
            "unit": "percent",
            "basis": "The owner's explicit acceptance review.",
        }
        mission = mission_state(work_plan(progress=declared))
        original = copy.deepcopy(mission)
        evidence = []
        view = build_work_view(mission, evidence=evidence)
        self.assertEqual(view["progress"], declared)
        self.assertEqual(mission, original)
        self.assertEqual(evidence, [])
        view["progress"]["value"] = 100
        view["blocks"][0]["remaining"]["low"] = 999
        self.assertEqual(mission, original)

    def test_declared_dependencies_are_separate_from_hierarchy_and_parallel_permission(self):
        plan = work_plan(
            [
                {"task_id": "S1", "depends_on": ["T2"]},
                {"task_id": "S2", "depends_on": []},
                {"task_id": "T2", "depends_on": None},
            ]
        )
        mission = mission_state(plan)
        rows = rows_by_id(build_work_view(mission))
        self.assertEqual(rows["S1"]["parent_id"], "T1")
        self.assertEqual(rows["S1"]["depends_on"], ["T2"])
        self.assertEqual(rows["S1"]["dependency_status"], "unmet")
        self.assertEqual(
            [(item["task_id"], item["satisfied"]) for item in rows["S1"]["dependencies"]],
            [("T2", False)],
        )
        self.assertEqual(rows["S2"]["dependency_status"], "declared_clear")
        self.assertEqual(rows["S2"]["dependencies"], [])
        self.assertEqual(rows["T2"]["dependency_status"], "unknown")
        self.assertIsNone(rows["T2"]["dependencies"])
        self.assertTrue(all(row["parallel_conditions"] is None for row in rows.values()))
        self.assertTrue(build_work_view(mission)["limitations"])
        next(task for task in mission["tasks"] if task["id"] == "T2")["status"] = "completed"
        updated = rows_by_id(build_work_view(mission))["S1"]
        self.assertEqual(updated["dependency_status"], "declared_clear")
        self.assertTrue(updated["dependencies"][0]["satisfied"])

    def test_unmeasured_completed_predecessor_keeps_its_named_evidence_gap_visible(self):
        from html import escape
        from render_progress_view import (
            build_progress_report,
            render_progress_html,
            render_progress_text,
        )

        plan = work_plan()
        plan["blocks"][1]["depends_on"] = ["S1"]
        mission = mission_state(plan)
        child = next(task for task in mission["tasks"] if task["id"] == "S1")
        child["status"] = "completed"
        self.assertEqual(tplan_runtime.validate_mission(mission), [])
        attribution = build_outcome_attribution(mission, [])
        warning_code = "completion_without_progress_evidence"
        self.assertTrue(any(
            warning["code"] == warning_code and warning["task_id"] == "S1"
            for warning in attribution["tasks"]["S1"]["warnings"]
        ))

        view = build_work_view(mission, evidence=[], outcome_attribution=attribution)
        self.assertEqual(set(rows_by_id(view)), {"T1", "T2"})
        self.assertEqual(len(view["blocks"]), 2)
        self.assertEqual(
            view["remaining"]["total"], {"low": 4, "high": 8, "unit": "hours"}
        )
        self.assertEqual(
            view["remaining"]["totals_by_unit"][0]["task_ids"], ["T1", "T2"]
        )
        gap = next(item for item in view["diagnostics"] if item["code"] == warning_code)
        self.assertIn("S1", gap["task_ids"])
        self.assertIn(child["title"], gap["message"])
        named_warnings = [
            message for message in view["limitations"]
            if child["title"] in message and "完成声明缺少合格推进证据" in message
        ]
        self.assertTrue(named_warnings)
        self.assertIn("不证明完成证据已通过", named_warnings[0])

        report = build_progress_report({"mission": mission, "events": [], "trace": []})
        self.assertEqual(set(rows_by_id(report["work_view"])), {"T1", "T2"})
        self.assertEqual(
            report["work_view"]["remaining"]["total"],
            {"low": 4, "high": 8, "unit": "hours"},
        )
        self.assertIn(named_warnings[0], render_progress_text(report))
        self.assertIn(escape(named_warnings[0]), render_progress_html(report))

    def test_current_shared_risk_is_visible_without_a_work_plan(self):
        from tests.tplan.test_shared_risk_context import valid_signal

        mission = mission_state()
        signal = valid_signal()
        mission["shared_context"] = {"risk_signals": [signal]}
        self.assertEqual(tplan_runtime.validate_mission(mission), [])
        self.assertEqual(tplan_runtime.active_risk_signals(mission), [signal])
        original = copy.deepcopy(mission)

        view = build_work_view(mission)
        self.assertFalse(view["planning"]["present"])
        self.assertEqual(len(view["risks"]), 1)
        risk = view["risks"][0]
        self.assertEqual(risk["severity"], "high")
        self.assertEqual(risk["summary"], signal["signal"])
        self.assertEqual(risk["value_effect"], signal["value_effect"])
        self.assertEqual(risk["recovery_condition"], signal["recovery_condition"])
        self.assertEqual(mission, original)

        signal["status"] = "resolved"
        self.assertEqual(tplan_runtime.active_risk_signals(mission), [])
        self.assertEqual(build_work_view(mission)["risks"], [])

    def test_summary_only_risks_and_blockers_are_visible_and_resolved_items_are_not_current(self):
        plan = work_plan(
            risks=[
                {"summary": "Source access may expire."},
                {"summary": "The source was previously unavailable.", "status": "resolved"},
            ],
            blockers=[
                {"summary": "Waiting for the owner's review."},
                {"summary": "The old access blocker was cleared.", "status": "resolved"},
            ],
        )
        self.assertEqual(validate_work_plan(mission_state(), plan), [])
        view = build_work_view(mission_state(plan))
        self.assertEqual(
            [item["summary"] for item in view["risks"]], ["Source access may expire."]
        )
        self.assertEqual(
            [item["summary"] for item in view["blockers"]], ["Waiting for the owner's review."]
        )


class WorkPlanRuntimeTests(unittest.TestCase):
    def test_build_mission_accepts_optional_top_level_plan_and_keeps_a_detached_copy(self):
        plan = work_plan()
        legacy = tplan_runtime.build_mission(**mission_arguments())
        self.assertNotIn("work_plan", legacy)
        mission = tplan_runtime.build_mission(**mission_arguments(), work_plan=plan)
        self.assertEqual(mission["work_plan"], plan)
        self.assertEqual(tplan_runtime.validate_mission(mission), [])
        plan["blocks"][0]["remaining"]["low"] = 999
        self.assertEqual(mission["work_plan"]["blocks"][0]["remaining"]["low"], 1)

    def test_record_changes_only_planning_metadata_and_cannot_count_as_progress(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            before = read_mission(mission_dir)
            plan = work_plan()
            result = tplan_runtime.record_work_plan(mission_dir, plan)
            after = read_mission(mission_dir)
            self.assertTrue(result["changed"])
            self.assertEqual(result["work_plan"], plan)
            self.assertEqual(result["event"]["event_type"], "planning_metadata_updated")
            self.assertEqual(after.pop("work_plan"), plan)
            self.assertEqual(after, before)
            events = read_jsonl(mission_dir / "evidence.jsonl")
            self.assertEqual(events, [result["event"]])
            self.assertFalse((mission_dir / ".mission-transaction.json").exists())
            trace = read_jsonl(mission_dir / "execution_trace.jsonl")
            attribution = build_outcome_attribution(read_mission(mission_dir), events, trace)
            self.assertEqual(attribution["mission"]["countable_progress"], [])
            self.assertTrue(
                all(scope["countable_progress"] == [] for scope in attribution["tasks"].values())
            )
            self.assertEqual(
                tplan_runtime.classify_evidence_outcome(read_mission(mission_dir), events[0])[
                    "classification"
                ],
                "planning_metadata",
            )
            self.assertIsNone(read_work_view_snapshot(mission_dir)["work_view"]["progress"])

    def test_identical_plan_is_a_true_noop_without_event_or_artifact_rewrites(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            plan = work_plan()
            tplan_runtime.record_work_plan(mission_dir, plan)
            before = artifact_snapshot(mission_dir)
            result = tplan_runtime.record_work_plan(
                mission_dir, copy.deepcopy(plan), summary="A duplicate delivery."
            )
            self.assertFalse(result["changed"])
            self.assertIsNone(result["event"])
            self.assertEqual(result["work_plan"], plan)
            self.assertEqual(artifact_snapshot(mission_dir), before)

    def test_transaction_prepare_failure_does_not_leave_a_plan_or_ghost_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            before = artifact_snapshot(mission_dir)
            original_write_json = tplan_runtime.write_json

            def fail_transaction(path, data, **kwargs):
                if Path(path).name == ".mission-transaction.json":
                    raise OSError("work plan transaction disk full")
                return original_write_json(path, data, **kwargs)

            with mock.patch.object(tplan_runtime, "write_json", side_effect=fail_transaction):
                with self.assertRaisesRegex(OSError, "disk full"):
                    tplan_runtime.record_work_plan(mission_dir, work_plan())
            self.assertEqual(artifact_snapshot(mission_dir), before)

    def test_invalid_plan_fails_before_any_runtime_artifact_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            before = artifact_snapshot(mission_dir)
            plan = work_plan([{"task_id": "missing", "remaining": estimate(1)}])
            with self.assertRaises(tplan_runtime.TplanError):
                tplan_runtime.record_work_plan(mission_dir, plan)
            self.assertEqual(artifact_snapshot(mission_dir), before)

    def test_open_interaction_guard_rejects_plan_mutation_without_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            tplan_runtime.begin_interaction_guard(
                mission_dir, platform="test-host", message_ref="work-plan-message"
            )
            before = artifact_snapshot(mission_dir)
            with self.assertRaisesRegex(tplan_runtime.TplanError, "guard"):
                tplan_runtime.record_work_plan(mission_dir, work_plan())
            self.assertEqual(artifact_snapshot(mission_dir), before)

    def test_pinned_incompatible_runtime_rejects_plan_mutation_without_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            mission = read_mission(mission_dir)
            mission["runtime_provenance"]["fingerprint"]["build_hash"] = "sha256:" + "0" * 64
            (mission_dir / "mission.json").write_text(
                json.dumps(mission, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            before = artifact_snapshot(mission_dir)
            with self.assertRaisesRegex(tplan_runtime.TplanError, "runtime fingerprint mismatch"):
                tplan_runtime.record_work_plan(mission_dir, work_plan())
            self.assertEqual(artifact_snapshot(mission_dir), before)

    def test_readonly_snapshot_preserves_files_and_refuses_pending_transaction_recovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            plan = work_plan()
            tplan_runtime.record_work_plan(mission_dir, plan)
            before = artifact_snapshot(mission_dir)
            snapshot = read_work_view_snapshot(mission_dir)
            self.assertEqual(snapshot["mission"]["work_plan"], plan)
            self.assertTrue(snapshot["work_view"]["planning"]["present"])
            self.assertEqual(artifact_snapshot(mission_dir), before)
            (mission_dir / ".mission-transaction.json").write_text("{}", encoding="utf-8")
            pending = artifact_snapshot(mission_dir)
            with self.assertRaisesRegex(tplan_runtime.TplanError, "pending Mission transaction"):
                read_work_view_snapshot(mission_dir)
            self.assertEqual(artifact_snapshot(mission_dir), pending)

    def test_planning_event_cannot_be_appended_outside_its_metadata_transaction(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            before = artifact_snapshot(mission_dir)
            with self.assertRaises(tplan_runtime.TplanError):
                tplan_runtime.append_event(
                    mission_dir,
                    {
                        "event_type": "planning_metadata_updated",
                        "summary": "This event must be owned by record_work_plan.",
                        "payload": {},
                    },
                )
            self.assertEqual(artifact_snapshot(mission_dir), before)

    def test_later_task_transition_preserves_the_plan_without_modifying_the_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            plan = work_plan()
            tplan_runtime.record_work_plan(mission_dir, plan)
            tplan_runtime.transition_task_status(mission_dir, "T2", "active")
            self.assertEqual(read_mission(mission_dir)["work_plan"], plan)
            snapshot = read_work_view_snapshot(mission_dir)
            self.assertEqual(rows_by_id(snapshot["work_view"])["T2"]["status"], "active")

    def test_init_entrypoints_accept_work_plan_json_before_persisting(self):
        for script_name in ("init_mission.py", "init_lite.py"):
            with self.subTest(script=script_name), tempfile.TemporaryDirectory() as tmp:
                mission_dir = Path(tmp) / "work-plan"
                plan = work_plan([{"task_id": "T1", "remaining": estimate(2, 4)}])
                plan_path = Path(tmp) / "work-plan.json"
                plan_path.write_text(json.dumps(plan), encoding="utf-8")
                args = [
                    "--dir", mission_dir, "--mission-id", "work-plan",
                    "--title", "Work Plan Mission", "--objective", "Keep estimates explicit.",
                    "--acceptance-evidence", "A1:The result meets acceptance.",
                    "--work-plan-json", plan_path,
                ]
                if script_name == "init_lite.py":
                    args.extend([
                        "--active-task-id", "T1", "--active-task-title", "Deliver the result",
                        "--active-task-contribution", "Produces A1.",
                    ])
                else:
                    tasks_path = Path(tmp) / "tasks.json"
                    tasks_path.write_text(json.dumps([task_inputs()[0]]), encoding="utf-8")
                    args.extend(["--task-json", tasks_path])
                result = run_script(script_name, *args)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(read_mission(mission_dir)["work_plan"], plan)
                check = run_script("check_mission.py", mission_dir)
                self.assertEqual(check.returncode, 0, check.stdout + check.stderr)

    def test_record_cli_returns_json_and_repeated_input_does_not_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            plan_path = Path(tmp) / "plan-input.json"
            plan_path.write_text(json.dumps(work_plan()), encoding="utf-8")
            args = [mission_dir, "--input", plan_path, "--summary", "Owner estimate update.", "--json"]
            result = run_script("record_work_plan.py", *args)
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["changed"])
            self.assertEqual(payload["event"]["summary"], "Owner estimate update.")
            before = artifact_snapshot(mission_dir)
            duplicate = run_script("record_work_plan.py", *args)
            self.assertEqual(duplicate.returncode, 0, duplicate.stderr)
            self.assertFalse(json.loads(duplicate.stdout)["changed"])
            self.assertIsNone(json.loads(duplicate.stdout)["event"])
            self.assertEqual(artifact_snapshot(mission_dir), before)


if __name__ == "__main__":
    unittest.main()
