import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "skills" / "tplan" / "scripts"

import sys

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import tplan_guard_control_server
import tplan_runtime


def create_mission(tmp):
    mission_dir = Path(tmp) / "mission"
    mission = tplan_runtime.build_mission(
        mission_id="guard-control-server",
        title="Guard Control Server",
        objective="Keep agent control bounded to fixed guard dispositions.",
        acceptance_evidence=[{"id": "A1", "description": "Control surface is bounded."}],
        human_in_loop=0,
        risk_tolerance=50,
        resource_sufficiency=50,
        tasks=[
            {
                "id": "T1",
                "title": "Protect the baseline",
                "role": "success-critical",
                "mission_contribution": "Provides the fixed stop baseline.",
                "acceptance_evidence": ["A1"],
            }
        ],
    )
    mission_dir.parent.mkdir(parents=True, exist_ok=True)
    mission_dir.mkdir()
    tplan_runtime.write_mission(mission_dir, mission)
    tplan_runtime.initialize_execution_trace(mission_dir, mission)
    tplan_runtime.transition_task_status(mission_dir, "T1", "active")
    return mission_dir


class GuardControlServerTests(unittest.TestCase):
    def test_agent_surface_exposes_only_bounded_tools(self):
        self.assertEqual({item["name"] for item in tplan_guard_control_server.TOOLS}, {"inspect", "await_proposal", "stop_fixed"})
        self.assertNotIn("resume_original", {item["name"] for item in tplan_guard_control_server.TOOLS})

    def test_inspect_and_fixed_stop_are_bound_to_server_mission(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            other_dir = create_mission(Path(tmp) / "other")
            guard = tplan_runtime.begin_interaction_guard(mission_dir, platform="test-host", message_ref="M1")

            inspect = tplan_guard_control_server.call_tool(mission_dir, "inspect", {})
            self.assertEqual(inspect["guard"]["guard_id"], guard["guard_id"])
            with self.assertRaisesRegex(tplan_runtime.TplanError, "unsupported"):
                tplan_guard_control_server.call_tool(mission_dir, "resume_original", {})
            with self.assertRaisesRegex(tplan_runtime.TplanError, "unsupported arguments"):
                tplan_guard_control_server.call_tool(mission_dir, "inspect", {"mission_dir": str(other_dir)})

            result = tplan_guard_control_server.call_tool(
                mission_dir,
                "stop_fixed",
                {
                    "guard_id": guard["guard_id"],
                    "expected_revision": guard["revision"],
                    "message_refs": ["M1"],
                    "task_id": "T1",
                },
            )
            self.assertEqual(result["disposition"], "stop")
            self.assertIsNone(tplan_runtime.read_interaction_guard(mission_dir))
            self.assertEqual(tplan_runtime.read_mission(mission_dir)["mission"]["status"], "requires_human")
            self.assertIsNone(tplan_runtime.read_interaction_guard(other_dir))

    def test_mcp_dispatch_lists_tools_and_returns_tool_errors_without_process_exit(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            listing = tplan_guard_control_server.dispatch(
                mission_dir, {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
            )
            self.assertEqual(listing["result"]["tools"], list(tplan_guard_control_server.TOOLS))
            error = tplan_guard_control_server.dispatch(
                mission_dir,
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {"name": "resume_original", "arguments": {}},
                },
            )
            self.assertTrue(error["result"]["isError"])
            self.assertIn("unsupported", error["result"]["content"][0]["text"])

    def test_mcp_rejects_unknown_arguments_and_non_jsonrpc_requests(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            with self.assertRaisesRegex(tplan_runtime.TplanError, "unsupported arguments"):
                tplan_guard_control_server.call_tool(mission_dir, "inspect", {"mission_dir": "other"})
            response = tplan_guard_control_server.dispatch(mission_dir, {"id": 1, "method": "tools/list"})
            self.assertEqual(response["error"]["code"], -32600)
