"""New CLI defaults only; transport is mocked and old frozen runs are not replayed."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

REPO = Path(__file__).resolve().parents[1]
DRIVER = REPO/'docs/internal/research/typed-decision/route-control-v0.2/single-cycle-repair-v1/run.py'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CliModelDefaults(unittest.TestCase):
    def test_prepare_cli_default_is_sol61_xhigh_without_dispatch(self):
        driver = load('new_cli_defaults_driver', DRIVER)
        with tempfile.TemporaryDirectory() as temp, patch.object(driver, 'prepare', return_value={}) as prepare:
            with patch('sys.argv', ['run.py', 'prepare', '--root', str(Path(temp)/'batch')]), patch('builtins.print'):
                driver.main()
        self.assertEqual(prepare.call_args.args[6:8], ('gpt-6.1-sol', 'xhigh'))

    def test_reviewer_command_and_intent_match_sol61_without_cli_start(self):
        reviewer = load('new_cli_defaults_reviewer', DRIVER.parent/'final-validation-v1/review_runner.py')
        process = Mock(returncode=0)
        process.communicate.return_value = ('', '')
        with tempfile.TemporaryDirectory() as temp:
            reviewer.BASE = Path(temp)
            with patch.object(reviewer.subprocess, 'Popen', return_value=process) as start, patch('builtins.print'):
                reviewer.run('mock-review', 'synthetic prompt')
            cmd = start.call_args.args[0]
            intent = json.loads((Path(temp)/'mock-review/intent.json').read_text())
            self.assertEqual(cmd[cmd.index('-m')+1], 'gpt-6.1-sol')
            self.assertIn('model_reasoning_effort="xhigh"', cmd)
            self.assertEqual((intent['requested_model'], intent['reasoning_effort']), ('gpt-6.1-sol', 'xhigh'))
            self.assertEqual(start.call_count, 1)


if __name__ == '__main__':
    unittest.main()
