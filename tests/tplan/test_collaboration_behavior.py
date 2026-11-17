"""Executed goal-preservation behavior evidence (Issue #246 R02).

These tests drive the real collaboration runtime through T23/T25/T26-T29 and verify
the actual resulting state, not prewritten ideal answers. The committed execution
transcript must reproduce the same outcome flags as a fresh run.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from tests.tplan import collaboration_behavior_driver as driver


REPO = Path(__file__).resolve().parents[2]
COMMITTED = REPO / "docs/internal/tplan-collaboration/reviews/r2/behavior-execution.jsonl"


class CollaborationBehaviorExecutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = {r["case"]: r for r in driver.run_all()}

    def test_all_six_cases_execute_with_real_state_and_pass(self):
        self.assertEqual(set(self.records), {"T23", "T25", "T26", "T27", "T28", "T29"})
        for case, record in self.records.items():
            self.assertEqual(record["evidence_class"], "agent_behavior_execution", case)
            self.assertFalse(record["real_host_e2e"], case)
            self.assertTrue(record["steps"], case)
            self.assertTrue(all(record["outcome"].values()), (case, record["outcome"]))
            for step in record["steps"]:
                self.assertIn(step["response_status"], {"committed", "read", "no_change", "replayed"}, case)
                self.assertIn("before", step)
                self.assertIn("after", step)
                self.assertIn("focus_task_id", step["after"])

    def test_specific_goal_preservation_outcomes(self):
        r = self.records
        self.assertTrue(r["T23"]["outcome"]["no_delegation_created"])
        self.assertTrue(r["T25"]["outcome"]["only_existing_delegation"])
        self.assertTrue(r["T26"]["outcome"]["no_new_tasks"])
        self.assertTrue(r["T26"]["outcome"]["no_new_delegations"])
        self.assertTrue(r["T27"]["outcome"]["debug_stays_with_B"])
        self.assertTrue(r["T28"]["outcome"]["pending_cleared"])
        self.assertTrue(r["T28"]["outcome"]["one_adoption"])
        self.assertTrue(r["T29"]["outcome"]["replacement_delegation_created"])
        self.assertTrue(r["T29"]["outcome"]["history_preserved"])

    def test_committed_execution_transcript_reproduces_outcomes(self):
        self.assertTrue(COMMITTED.is_file(), "committed execution evidence must exist")
        committed = {json.loads(line)["case"]: json.loads(line) for line in COMMITTED.read_text(encoding="utf-8").splitlines() if line.strip()}
        self.assertEqual(set(committed), set(self.records))
        for case, record in self.records.items():
            self.assertEqual(committed[case]["evidence_class"], "agent_behavior_execution")
            self.assertEqual(committed[case]["outcome"], record["outcome"], case)


if __name__ == "__main__":
    unittest.main()
