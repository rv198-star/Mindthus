import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock


REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "skills" / "tplan" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from codex_telemetry_activation import (
    HOOK_EVENT_NAMES,
    cleanup_activation,
    evaluate_preflight,
    install_source,
    query_hook_inventory,
    uninstall_dispatcher,
)
from codex_telemetry_adapter import (
    bind_session,
    coverage_path,
    handle_hook,
    hook_command,
)
from codex_telemetry_dispatcher import dispatch_hook, registry_path
from execution_cost_tree import build_execution_cost_tree, render_markdown
from tests.tplan.test_codex_telemetry_adapter import (
    at,
    create_mission,
    hook,
    run_script,
)
from tplan_runtime import TplanError, read_execution_trace


def hook_inventory(
    mission_dir,
    state_dir,
    source_path,
    *,
    cwd,
    source_scope,
    trust_status="trusted",
    enabled=True,
    command=None,
    host_build=None,
    codex_version="codex-cli 0.146.0",
):
    command = command or hook_command(mission_dir, state_dir)
    rows = []
    for public_name, host_name in HOOK_EVENT_NAMES.items():
        rows.append(
            {
                "key": f"test-{host_name}",
                "eventName": host_name,
                "handlerType": "command",
                "command": command,
                "currentHash": f"sha256:{public_name.lower()}",
                "displayOrder": 1,
                "enabled": enabled,
                "isManaged": False,
                "source": source_scope,
                "sourcePath": str(Path(source_path).resolve()),
                "timeoutSec": 10,
                "trustStatus": trust_status,
            }
        )
    return {
        "initialize": {
            "userAgent": "Codex Desktop/0.146.0 test-host",
            "platformFamily": "unix",
            "platformOs": "macos",
        },
        "hooks_list": {
            "data": [
                {
                    "cwd": str(Path(cwd).resolve()),
                    "hooks": rows,
                    "warnings": [],
                    "errors": [],
                }
            ]
        },
        "codex_version": codex_version,
        **({"host_build": host_build} if host_build else {}),
    }


class CodexTelemetryActivationTests(unittest.TestCase):
    def test_app_cli_and_user_project_preflights_are_separate_and_observable(self):
        for surface, source_scope in (
            ("codex_app", "project"),
            ("codex_cli", "project"),
            ("codex_app", "user"),
            ("codex_cli", "user"),
        ):
            with self.subTest(surface=surface, scope=source_scope):
                with tempfile.TemporaryDirectory() as tmp:
                    mission_dir = create_mission(tmp)
                    state_dir = Path(tmp) / "host-state"
                    state_dir.mkdir()
                    generated = run_script(
                        "generate_codex_telemetry_hooks.py",
                        str(mission_dir),
                        "--state-dir",
                        str(state_dir),
                        "--session-id",
                        "session-1",
                    )
                    self.assertEqual(generated.returncode, 0, generated.stderr)
                    source_root = Path(tmp) / f"{source_scope}-root"
                    source_path = source_root / ".codex" / "hooks.json"
                    installed = install_source(
                        mission_dir,
                        state_dir,
                        surface=surface,
                        source_scope=source_scope,
                        source_path=source_path,
                    )
                    self.assertEqual(installed["added_handler_groups"], 4)
                    result = evaluate_preflight(
                        mission_dir,
                        state_dir,
                        surface=surface,
                        source_scope=source_scope,
                        source_path=source_path,
                        cwd=source_root,
                        inventory=hook_inventory(
                            mission_dir,
                            state_dir,
                            source_path,
                            cwd=source_root,
                            source_scope=source_scope,
                            host_build="Codex App build 146"
                            if surface == "codex_app"
                            else None,
                        ),
                        host_build=None,
                        codex_bin="codex",
                    )
                    self.assertTrue(result["ready"], result)
                    self.assertEqual(result["source"]["sha256"], installed["source_sha256"])
                    coverage = json.loads(
                        coverage_path(mission_dir).read_text(encoding="utf-8")
                    )
                    self.assertEqual(
                        coverage["activation"]["surfaces"][surface]["status"], "ready"
                    )
                    other = (
                        "codex_cli" if surface == "codex_app" else "codex_app"
                    )
                    self.assertEqual(
                        coverage["activation"]["surfaces"][other]["status"],
                        "not_tested",
                    )
                    self.assertTrue(
                        coverage["activation"]["surfaces"][surface]["host_build"]
                    )
                    self.assertEqual(coverage["binding"]["generation"], 1)
                    self.assertEqual(
                        coverage["activation"]["surfaces"][surface][
                            "binding_generation"
                        ],
                        1,
                    )

                    base = datetime.now(timezone.utc) + timedelta(seconds=1)
                    handle_hook(
                        mission_dir,
                        state_dir,
                        hook(
                            "PreToolUse",
                            tool_name="Bash",
                            tool_use_id="tool-activation",
                        ),
                        observed_at=at(base, 0),
                    )
                    handle_hook(
                        mission_dir,
                        state_dir,
                        hook(
                            "PostToolUse",
                            tool_name="Bash",
                            tool_use_id="tool-activation",
                            tool_response={"exit_code": 0},
                        ),
                        observed_at=at(base, 1),
                    )
                    coverage = json.loads(
                        coverage_path(mission_dir).read_text(encoding="utf-8")
                    )
                    self.assertEqual(coverage["activation"]["status"], "observed")
                    self.assertEqual(
                        coverage["channels"]["local_tools"]["observed_span_count"], 1
                    )
                    for channel in ("hosted_tools", "model_turns", "tokens", "waits"):
                        self.assertEqual(
                            coverage["channels"][channel]["status"], "not_reported"
                        )

    def test_trusted_dispatcher_is_reused_by_a_second_mission_without_hash_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_root = root / "project"
            first_root = root / "first"
            second_root = root / "second"
            project_root.mkdir()
            first_root.mkdir()
            second_root.mkdir()
            first_mission = create_mission(first_root)
            second_mission = create_mission(second_root)
            state_dir = root / "host-state"
            state_dir.mkdir()
            source_path = project_root / ".codex" / "hooks.json"
            source_hashes = []
            for mission, session in (
                (first_mission, "session-first"),
                (second_mission, "session-second"),
            ):
                generated = run_script(
                    "generate_codex_telemetry_hooks.py",
                    str(mission),
                    "--state-dir",
                    str(state_dir),
                    "--session-id",
                    session,
                )
                self.assertEqual(generated.returncode, 0, generated.stderr)
                installed = install_source(
                    mission,
                    state_dir,
                    surface="codex_app",
                    source_scope="project",
                    source_path=source_path,
                )
                source_hashes.append(installed["source_sha256"])
                preflight = evaluate_preflight(
                    mission,
                    state_dir,
                    surface="codex_app",
                    source_scope="project",
                    source_path=source_path,
                    cwd=project_root,
                    inventory=hook_inventory(
                        mission,
                        state_dir,
                        source_path,
                        cwd=project_root,
                        source_scope="project",
                        host_build="Codex App stable-dispatcher-build",
                    ),
                    host_build=None,
                    codex_bin="codex",
                )
                self.assertTrue(preflight["ready"], preflight)
            self.assertEqual(source_hashes[0], source_hashes[1])

            base = datetime.now(timezone.utc) + timedelta(seconds=1)
            dispatch_hook(
                state_dir,
                hook(
                    "PreToolUse",
                    session="session-second",
                    tool_name="Bash",
                    tool_use_id="stable-dispatch-tool",
                ),
                observed_at=at(base, 0),
            )
            dispatch_hook(
                state_dir,
                hook(
                    "PostToolUse",
                    session="session-second",
                    tool_name="Bash",
                    tool_use_id="stable-dispatch-tool",
                    tool_response={"exit_code": 0},
                ),
                observed_at=at(base, 1),
            )
            coverage = json.loads(
                coverage_path(second_mission).read_text(encoding="utf-8")
            )
            self.assertEqual(coverage["activation"]["status"], "observed")
            self.assertEqual(
                coverage["channels"]["local_tools"]["observed_span_count"],
                1,
            )

    def test_preflight_distinguishes_every_activation_failure(self):
        cases = (
            ("source_absent", None, {}),
            ("source_not_enumerated", "trusted", {"rows": []}),
            ("needs_trust", "modified", {}),
            ("disabled", "trusted", {"enabled": False}),
            (
                "binding_mismatch",
                "trusted",
                {"command": "python3 /tmp/not-the-bound-adapter.py"},
            ),
        )
        for expected, trust, options in cases:
            with self.subTest(status=expected), tempfile.TemporaryDirectory() as tmp:
                mission_dir = create_mission(tmp)
                state_dir = Path(tmp) / "host-state"
                state_dir.mkdir()
                generated = run_script(
                    "generate_codex_telemetry_hooks.py",
                    str(mission_dir),
                    "--state-dir",
                    str(state_dir),
                    "--session-id",
                    "session-1",
                )
                self.assertEqual(generated.returncode, 0, generated.stderr)
                source_root = Path(tmp) / "repo"
                source_path = source_root / ".codex" / "hooks.json"
                inventory = {
                    "hooks_list": {
                        "data": [
                            {
                                "cwd": str(source_root.resolve()),
                                "hooks": [],
                                "warnings": [],
                                "errors": [],
                            }
                        ]
                    },
                    "initialize": {},
                    "codex_version": "codex-cli 0.146.0",
                }
                if expected != "source_absent":
                    install_source(
                        mission_dir,
                        state_dir,
                        surface="codex_cli",
                        source_scope="project",
                        source_path=source_path,
                    )
                    inventory = hook_inventory(
                        mission_dir,
                        state_dir,
                        source_path,
                        cwd=source_root,
                        source_scope="project",
                        trust_status=trust,
                        enabled=options.get("enabled", True),
                        command=options.get("command"),
                    )
                    if "rows" in options:
                        inventory["hooks_list"]["data"][0]["hooks"] = options["rows"]
                result = evaluate_preflight(
                    mission_dir,
                    state_dir,
                    surface="codex_cli",
                    source_scope="project",
                    source_path=source_path,
                    cwd=source_root,
                    inventory=inventory,
                    host_build="codex-cli 0.146.0",
                    codex_bin="codex",
                )
                self.assertEqual(result["status"], expected)
                self.assertFalse(result["ready"])
                coverage = json.loads(
                    coverage_path(mission_dir).read_text(encoding="utf-8")
                )
                self.assertEqual(coverage["activation"]["status"], expected)
                self.assertIn(
                    expected, coverage["channels"]["local_tools"]["reason"]
                )

    def test_app_preflight_never_uses_cli_app_server_as_host_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            state_dir = Path(tmp) / "host-state"
            state_dir.mkdir()
            run_script(
                "generate_codex_telemetry_hooks.py",
                str(mission_dir),
                "--state-dir",
                str(state_dir),
                "--session-id",
                "session-1",
            )
            source_root = Path(tmp) / "repo"
            source_path = source_root / ".codex" / "hooks.json"
            install_source(
                mission_dir,
                state_dir,
                surface="codex_app",
                source_scope="project",
                source_path=source_path,
            )
            with mock.patch(
                "codex_telemetry_activation.query_hook_inventory"
            ) as query:
                result = evaluate_preflight(
                    mission_dir,
                    state_dir,
                    surface="codex_app",
                    source_scope="project",
                    source_path=source_path,
                    cwd=source_root,
                    inventory=None,
                    host_build="Codex App 2026.730.1",
                    codex_bin="must-not-run",
                )
            query.assert_not_called()
            self.assertEqual(result["status"], "inventory_unavailable")
            self.assertFalse(result["ready"])
            self.assertIn("not App evidence", result["reason"])

    def test_preflight_rejects_duplicate_bound_handlers(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            state_dir = Path(tmp) / "host-state"
            state_dir.mkdir()
            run_script(
                "generate_codex_telemetry_hooks.py",
                str(mission_dir),
                "--state-dir",
                str(state_dir),
                "--session-id",
                "session-1",
            )
            source_root = Path(tmp) / "repo"
            source_path = source_root / ".codex" / "hooks.json"
            install_source(
                mission_dir,
                state_dir,
                surface="codex_cli",
                source_scope="project",
                source_path=source_path,
            )
            inventory = hook_inventory(
                mission_dir,
                state_dir,
                source_path,
                cwd=source_root,
                source_scope="project",
            )
            inventory["hooks_list"]["data"][0]["hooks"].append(
                dict(inventory["hooks_list"]["data"][0]["hooks"][0])
            )
            result = evaluate_preflight(
                mission_dir,
                state_dir,
                surface="codex_cli",
                source_scope="project",
                source_path=source_path,
                cwd=source_root,
                inventory=inventory,
                host_build="codex-cli 0.146.0",
                codex_bin="codex",
            )
            self.assertEqual(result["status"], "binding_mismatch")
            self.assertFalse(result["ready"])

    def test_preflight_fails_if_source_changes_during_host_inventory(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            state_dir = Path(tmp) / "host-state"
            state_dir.mkdir()
            run_script(
                "generate_codex_telemetry_hooks.py",
                str(mission_dir),
                "--state-dir",
                str(state_dir),
                "--session-id",
                "session-1",
            )
            source_root = Path(tmp) / "repo"
            source_path = source_root / ".codex" / "hooks.json"
            install_source(
                mission_dir,
                state_dir,
                surface="codex_cli",
                source_scope="project",
                source_path=source_path,
            )
            inventory = hook_inventory(
                mission_dir,
                state_dir,
                source_path,
                cwd=source_root,
                source_scope="project",
            )

            def mutate_source(*_args, **_kwargs):
                source_path.write_bytes(source_path.read_bytes() + b"\n")
                return inventory

            with mock.patch(
                "codex_telemetry_activation.query_hook_inventory",
                side_effect=mutate_source,
            ), mock.patch(
                "codex_telemetry_activation.query_codex_version",
                return_value="codex-cli 0.146.0",
            ), self.assertRaisesRegex(TplanError, "changed during activation"):
                evaluate_preflight(
                    mission_dir,
                    state_dir,
                    surface="codex_cli",
                    source_scope="project",
                    source_path=source_path,
                    cwd=source_root,
                    inventory=None,
                    host_build=None,
                    codex_bin="codex",
                )

    def test_required_activation_blocks_callbacks_until_ready_and_reports_unpaired(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            state_dir = Path(tmp) / "host-state"
            state_dir.mkdir()
            generated = run_script(
                "generate_codex_telemetry_hooks.py",
                str(mission_dir),
                "--state-dir",
                str(state_dir),
                "--session-id",
                "session-1",
            )
            self.assertEqual(generated.returncode, 0, generated.stderr)
            before = read_execution_trace(mission_dir)
            blocked = handle_hook(
                mission_dir,
                state_dir,
                hook(
                    "PreToolUse",
                    tool_name="Bash",
                    tool_use_id="tool-before-preflight",
                ),
            )
            self.assertEqual(blocked["reason"], "activation_preflight_required")
            self.assertEqual(read_execution_trace(mission_dir), before)

            source_root = Path(tmp) / "repo"
            source_path = source_root / ".codex" / "hooks.json"
            install_source(
                mission_dir,
                state_dir,
                surface="codex_cli",
                source_scope="project",
                source_path=source_path,
            )
            evaluate_preflight(
                mission_dir,
                state_dir,
                surface="codex_cli",
                source_scope="project",
                source_path=source_path,
                cwd=source_root,
                inventory=hook_inventory(
                    mission_dir,
                    state_dir,
                    source_path,
                    cwd=source_root,
                    source_scope="project",
                ),
                host_build="codex-cli 0.146.0",
                codex_bin="codex",
            )
            handle_hook(
                mission_dir,
                state_dir,
                hook(
                    "PreToolUse",
                    tool_name="Bash",
                    tool_use_id="tool-unpaired",
                ),
            )
            coverage = json.loads(
                coverage_path(mission_dir).read_text(encoding="utf-8")
            )
            self.assertEqual(coverage["activation"]["status"], "callback_unpaired")
            self.assertEqual(
                coverage["channels"]["local_tools"]["status"],
                "available_not_observed",
            )

    def test_binding_mismatch_replaces_ready_status_and_writes_no_span(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            state_dir = Path(tmp) / "host-state"
            state_dir.mkdir()
            run_script(
                "generate_codex_telemetry_hooks.py",
                str(mission_dir),
                "--state-dir",
                str(state_dir),
                "--session-id",
                "session-1",
            )
            source_root = Path(tmp) / "repo"
            source_path = source_root / ".codex" / "hooks.json"
            install_source(
                mission_dir,
                state_dir,
                surface="codex_cli",
                source_scope="project",
                source_path=source_path,
            )
            evaluate_preflight(
                mission_dir,
                state_dir,
                surface="codex_cli",
                source_scope="project",
                source_path=source_path,
                cwd=source_root,
                inventory=hook_inventory(
                    mission_dir,
                    state_dir,
                    source_path,
                    cwd=source_root,
                    source_scope="project",
                ),
                host_build="codex-cli 0.146.0",
                codex_bin="codex",
            )
            result = handle_hook(
                mission_dir,
                state_dir,
                hook(
                    "PreToolUse",
                    session="different-session",
                    tool_name="Bash",
                    tool_use_id="tool-wrong-session",
                ),
            )
            self.assertEqual(result["reason"], "session_binding_mismatch")
            coverage = json.loads(
                coverage_path(mission_dir).read_text(encoding="utf-8")
            )
            self.assertEqual(coverage["activation"]["status"], "binding_mismatch")
            self.assertEqual(coverage["binding"]["generation"], 1)
            self.assertFalse(
                any(
                    record["event_type"] == "span_completed"
                    for record in read_execution_trace(mission_dir)
                )
            )

    def test_cleanup_preserves_unrelated_hooks_and_removes_stale_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            state_dir = Path(tmp) / "host-state"
            state_dir.mkdir()
            run_script(
                "generate_codex_telemetry_hooks.py",
                str(mission_dir),
                "--state-dir",
                str(state_dir),
                "--session-id",
                "session-1",
            )
            source_path = Path(tmp) / "user" / ".codex" / "hooks.json"
            source_path.parent.mkdir(parents=True)
            unrelated = {
                "description": "keep me",
                "hooks": {
                    "PreToolUse": [
                        {
                            "matcher": "Bash",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "python3 /tmp/unrelated.py",
                                }
                            ],
                        }
                    ]
                },
            }
            source_path.write_text(
                json.dumps(unrelated, indent=2) + "\n", encoding="utf-8"
            )
            install_source(
                mission_dir,
                state_dir,
                surface="codex_cli",
                source_scope="user",
                source_path=source_path,
            )
            result = cleanup_activation(
                mission_dir,
                state_dir,
                remove_dispatcher=True,
            )
            self.assertTrue(result["binding_state_removed"])
            self.assertTrue(result["coverage_claim_removed"])
            retained = json.loads(source_path.read_text(encoding="utf-8"))
            self.assertEqual(retained, unrelated)
            self.assertFalse(coverage_path(mission_dir).exists())

    def test_cleanup_removes_source_created_only_for_tplan(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            state_dir = Path(tmp) / "host-state"
            state_dir.mkdir()
            run_script(
                "generate_codex_telemetry_hooks.py",
                str(mission_dir),
                "--state-dir",
                str(state_dir),
                "--session-id",
                "session-1",
            )
            source_path = Path(tmp) / "project" / ".codex" / "hooks.json"
            install_source(
                mission_dir,
                state_dir,
                surface="codex_cli",
                source_scope="project",
                source_path=source_path,
            )
            self.assertTrue(source_path.exists())
            result = cleanup_activation(
                mission_dir,
                state_dir,
                remove_dispatcher=True,
            )
            self.assertFalse(source_path.exists())
            self.assertEqual(
                result["sources"][0]["status"], "removed_owned_source"
            )
            self.assertTrue(result["registry_removed"])
            self.assertFalse(registry_path(state_dir).exists())

    def test_default_cleanup_unroutes_mission_but_retains_stable_dispatcher(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            state_dir = Path(tmp) / "host-state"
            state_dir.mkdir()
            run_script(
                "generate_codex_telemetry_hooks.py",
                str(mission_dir),
                "--state-dir",
                str(state_dir),
                "--session-id",
                "session-1",
            )
            source_path = Path(tmp) / "project" / ".codex" / "hooks.json"
            installed = install_source(
                mission_dir,
                state_dir,
                surface="codex_app",
                source_scope="project",
                source_path=source_path,
            )
            source_before = source_path.read_bytes()
            result = cleanup_activation(mission_dir, state_dir)
            self.assertTrue(source_path.exists())
            self.assertEqual(source_path.read_bytes(), source_before)
            self.assertEqual(result["removed_binding_count"], 1)
            self.assertEqual(result["active_binding_count"], 0)
            self.assertFalse(result["dispatcher_removed"])
            self.assertEqual(
                result["sources"][0]["status"],
                "retained_stable_dispatcher",
            )
            self.assertFalse(coverage_path(mission_dir).exists())
            registry = json.loads(
                registry_path(state_dir).read_text(encoding="utf-8")
            )
            self.assertEqual(registry["bindings"], {})
            self.assertIn(
                installed["source_path"],
                registry["sources"],
            )
            uninstalled = uninstall_dispatcher(state_dir)
            self.assertTrue(uninstalled["dispatcher_removed"])
            self.assertTrue(uninstalled["registry_removed"])
            self.assertFalse(source_path.exists())

    def test_standalone_uninstall_refuses_active_mission_bindings(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            state_dir = Path(tmp) / "host-state"
            state_dir.mkdir()
            run_script(
                "generate_codex_telemetry_hooks.py",
                str(mission_dir),
                "--state-dir",
                str(state_dir),
                "--session-id",
                "session-1",
            )
            source_path = Path(tmp) / "project" / ".codex" / "hooks.json"
            install_source(
                mission_dir,
                state_dir,
                surface="codex_app",
                source_scope="project",
                source_path=source_path,
            )
            with self.assertRaisesRegex(TplanError, "active Mission bindings"):
                uninstall_dispatcher(state_dir)
            self.assertTrue(source_path.exists())
            self.assertTrue(registry_path(state_dir).exists())

    def test_dispatcher_uninstall_waits_for_last_mission_binding(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first_root = root / "first"
            second_root = root / "second"
            first_root.mkdir()
            second_root.mkdir()
            first_mission = create_mission(first_root)
            second_mission = create_mission(second_root)
            state_dir = root / "host-state"
            state_dir.mkdir()
            source_path = root / "project" / ".codex" / "hooks.json"
            for mission, session in (
                (first_mission, "session-first"),
                (second_mission, "session-second"),
            ):
                generated = run_script(
                    "generate_codex_telemetry_hooks.py",
                    str(mission),
                    "--state-dir",
                    str(state_dir),
                    "--session-id",
                    session,
                )
                self.assertEqual(generated.returncode, 0, generated.stderr)
                installed = install_source(
                    mission,
                    state_dir,
                    surface="codex_app",
                    source_scope="project",
                    source_path=source_path,
                )
                if mission == first_mission:
                    first_source_hash = installed["source_sha256"]
                    self.assertEqual(installed["added_handler_groups"], 4)
                else:
                    self.assertEqual(installed["added_handler_groups"], 0)
                    self.assertEqual(
                        installed["source_sha256"],
                        first_source_hash,
                    )

            first_cleanup = cleanup_activation(
                first_mission,
                state_dir,
                remove_dispatcher=True,
            )
            self.assertEqual(first_cleanup["active_binding_count"], 1)
            self.assertFalse(first_cleanup["dispatcher_removed"])
            self.assertEqual(
                first_cleanup["sources"][0]["status"],
                "retained_active_bindings",
            )
            self.assertTrue(source_path.exists())

            second_cleanup = cleanup_activation(
                second_mission,
                state_dir,
                remove_dispatcher=True,
            )
            self.assertEqual(second_cleanup["active_binding_count"], 0)
            self.assertTrue(second_cleanup["dispatcher_removed"])
            self.assertFalse(source_path.exists())

    def test_rebind_requires_fresh_preflight_before_new_callbacks(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            state_dir = Path(tmp) / "host-state"
            state_dir.mkdir()
            run_script(
                "generate_codex_telemetry_hooks.py",
                str(mission_dir),
                "--state-dir",
                str(state_dir),
                "--session-id",
                "session-1",
            )
            source_root = Path(tmp) / "repo"
            source_path = source_root / ".codex" / "hooks.json"
            install_source(
                mission_dir,
                state_dir,
                surface="codex_cli",
                source_scope="project",
                source_path=source_path,
            )
            evaluate_preflight(
                mission_dir,
                state_dir,
                surface="codex_cli",
                source_scope="project",
                source_path=source_path,
                cwd=source_root,
                inventory=hook_inventory(
                    mission_dir,
                    state_dir,
                    source_path,
                    cwd=source_root,
                    source_scope="project",
                ),
                host_build="codex-cli 0.146.0",
                codex_bin="codex",
            )
            bind_session(
                mission_dir,
                state_dir,
                session_id="session-2",
                replace=True,
                activation_required=True,
            )
            coverage = json.loads(
                coverage_path(mission_dir).read_text(encoding="utf-8")
            )
            self.assertEqual(coverage["activation"]["status"], "binding_mismatch")
            self.assertEqual(coverage["binding"]["generation"], 2)
            blocked = handle_hook(
                mission_dir,
                state_dir,
                hook(
                    "PreToolUse",
                    session="session-2",
                    tool_name="Bash",
                    tool_use_id="tool-after-rebind",
                ),
            )
            self.assertEqual(blocked["reason"], "activation_binding_mismatch")
            refreshed = evaluate_preflight(
                mission_dir,
                state_dir,
                surface="codex_cli",
                source_scope="project",
                source_path=source_path,
                cwd=source_root,
                inventory=hook_inventory(
                    mission_dir,
                    state_dir,
                    source_path,
                    cwd=source_root,
                    source_scope="project",
                ),
                host_build="codex-cli 0.146.0",
                codex_bin="codex",
            )
            self.assertTrue(refreshed["ready"])
            base = datetime.now(timezone.utc) + timedelta(seconds=1)
            handle_hook(
                mission_dir,
                state_dir,
                hook(
                    "PreToolUse",
                    session="session-2",
                    tool_name="Bash",
                    tool_use_id="tool-after-refreshed-preflight",
                ),
                observed_at=at(base, 0),
            )
            handle_hook(
                mission_dir,
                state_dir,
                hook(
                    "PostToolUse",
                    session="session-2",
                    tool_name="Bash",
                    tool_use_id="tool-after-refreshed-preflight",
                    tool_response={"exit_code": 0},
                ),
                observed_at=at(base, 1),
            )
            coverage = json.loads(
                coverage_path(mission_dir).read_text(encoding="utf-8")
            )
            self.assertEqual(coverage["activation"]["status"], "observed")
            self.assertEqual(
                coverage["activation"]["surfaces"]["codex_cli"][
                    "binding_generation"
                ],
                2,
            )

    def test_audit_retains_activation_build_hash_trust_and_no_raw_hook_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            state_dir = Path(tmp) / "host-state"
            state_dir.mkdir()
            run_script(
                "generate_codex_telemetry_hooks.py",
                str(mission_dir),
                "--state-dir",
                str(state_dir),
                "--session-id",
                "session-1",
            )
            source_root = Path(tmp) / "repo"
            source_path = source_root / ".codex" / "hooks.json"
            install_source(
                mission_dir,
                state_dir,
                surface="codex_app",
                source_scope="project",
                source_path=source_path,
            )
            inventory = hook_inventory(
                mission_dir,
                state_dir,
                source_path,
                cwd=source_root,
                source_scope="project",
                trust_status="modified",
                host_build="Codex App 2026.730.1",
            )
            inventory["hooks_list"]["data"][0]["warnings"] = [
                "raw prompt and secret must not enter coverage"
            ]
            evaluate_preflight(
                mission_dir,
                state_dir,
                surface="codex_app",
                source_scope="project",
                source_path=source_path,
                cwd=source_root,
                inventory=inventory,
                host_build=None,
                codex_bin="codex",
            )
            report = build_execution_cost_tree(mission_dir, view="audit")
            serialized = json.dumps(report["telemetry_capture"], ensure_ascii=False)
            self.assertNotIn(hook_command(mission_dir, state_dir), serialized)
            self.assertNotIn("raw prompt and secret", serialized)
            self.assertNotIn("session-1", serialized)
            markdown = render_markdown(report)
            self.assertIn("Codex App 2026.730.1", markdown)
            self.assertIn("needs_trust", markdown)
            self.assertIn("modified", markdown)
            self.assertIn("sha256:", markdown)

    def test_app_server_inventory_query_records_protocol_and_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / "fake-codex"
            fake.write_text(
                "#!"
                + sys.executable
                + "\n"
                + "import json, sys\n"
                + "if len(sys.argv) > 1 and sys.argv[1] == '--version':\n"
                + "    print('codex-cli 9.9.9')\n"
                + "    raise SystemExit(0)\n"
                + "for line in sys.stdin:\n"
                + "    message = json.loads(line)\n"
                + "    if message.get('id') == 0:\n"
                + "        print(json.dumps({'id': 0, 'result': {'userAgent': 'Codex Test/9.9.9', 'platformFamily': 'unix', 'platformOs': 'test'}}), flush=True)\n"
                + "    elif message.get('id') == 1:\n"
                + "        print(json.dumps({'id': 1, 'result': {'data': [{'cwd': "
                + repr(str(Path(tmp).resolve()))
                + ", 'hooks': [], 'warnings': [], 'errors': []}]}}), flush=True)\n",
                encoding="utf-8",
            )
            fake.chmod(0o755)
            result = query_hook_inventory(str(fake), Path(tmp))
            self.assertEqual(result["codex_version"], "codex-cli 9.9.9")
            self.assertEqual(
                result["initialize"]["userAgent"], "Codex Test/9.9.9"
            )
            self.assertEqual(result["hooks_list"]["data"][0]["hooks"], [])


if __name__ == "__main__":
    unittest.main()
