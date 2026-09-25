"""Call the frozen HD/C host once, then pause before artifact acceptance."""
from __future__ import annotations

import importlib.util
from pathlib import Path

SOURCE = Path(__file__).with_name('run.py')
spec = importlib.util.spec_from_file_location('formal_abc_frozen_run', SOURCE)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

runner.configure('HD')
runner.run_graph = lambda arm: None  # Defer consumption until original-host acceptance is recorded.
runner.run_host('C')
