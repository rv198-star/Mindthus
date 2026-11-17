"""Read-only archive recheck of the actual C R2 contract driver."""
from __future__ import annotations

import ast
import contextlib
import io
import json
import tempfile
from pathlib import Path


def main() -> int:
    archive = Path(__file__).resolve().parent
    origin = json.loads((archive / "source-world.json").read_text())["original_world"]
    driver = archive / "c-out/r2/review_contract.py"
    source = driver.read_text().replace(origin, str(archive))
    tree = ast.parse(source, filename=str(driver))
    with tempfile.TemporaryDirectory(prefix="mindthus246-host-recheck-") as temp:
        output = Path(temp)
        replaced = False
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == "OUT" for target in node.targets
            ):
                node.value = ast.Call(
                    func=ast.Name(id="Path", ctx=ast.Load()),
                    args=[ast.Constant(value=str(output))], keywords=[],
                )
                replaced = True
        if not replaced:
            raise RuntimeError("Expected the recorded C output-directory assignment")
        ast.fix_missing_locations(tree)
        namespace = {"__name__": "__main__", "__file__": str(driver)}
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(captured):
            try:
                exec(compile(tree, str(driver), "exec"), namespace)
            except SystemExit as exc:
                if exc.code not in (None, 0):
                    raise RuntimeError(captured.getvalue()) from exc
        result = json.loads((output / "results.json").read_text())
        if (result["status"], result["total"], result["passed"], result["failed"]) != (
            "PASS", 443, 443, 0
        ):
            raise RuntimeError("Archived artifact contract recheck failed")
        print(json.dumps({
            "evidence_class": "mechanical_archive_recheck",
            "status": result["status"], "total": result["total"],
            "passed": result["passed"], "failed": result["failed"],
            "artifact_digest": result["artifact_digest"],
            "archive_mutated": False, "new_native_messages": 0,
        }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
