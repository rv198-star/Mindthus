"""Exercise CLI serialization without starting Codex or calling any model."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

P=Path(__file__).resolve().parents[1]/'docs/internal/research/typed-decision/route-control-v0.2/design-reassessment-v1/live-v03-d1/run.py'
SPEC=importlib.util.spec_from_file_location('live_d_adapter_test',P)
runner=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(runner)

class AdapterTests(unittest.TestCase):
    def test_cli_schema_is_raw_and_session_resumes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);commands=[]
            class Proc:
                returncode=0
                def __init__(self,command,**kw):
                    commands.append(command);self.command=command;self.stdout=kw['stdout']
                    schema=json.loads(Path(command[command.index('--output-schema')+1]).read_text())
                    self_schema=schema
                    if self_schema!=runner.TEXT_SCHEMA:raise AssertionError('ledger wrapped schema')
                def communicate(self,prompt,timeout):
                    self.stdout.write(json.dumps({'type':'thread.started','thread_id':'real-test-context'})+'\n')
                    Path(self.command[self.command.index('-o')+1]).write_text('{"text":"test answer"}')
            with patch.object(runner,'verify',return_value={'codex_binary':'mock'}),patch.object(runner.subprocess,'Popen',Proc):
                first,receipt=runner.call(root,'first',{},runner.TEXT_SCHEMA,session_group='host')
                runner.call(root,'second',{},runner.TEXT_SCHEMA,session_group='host')
            self.assertEqual(first['text'],'test answer');self.assertEqual(receipt['status'],'complete')
            self.assertNotIn('resume',commands[0]);self.assertIn('resume',commands[1])
            self.assertIn('real-test-context',commands[1])

    def test_native_schema_allows_independent_dispute(self):
        schema=runner.schema_for({'schema':'mindthus.route-v03-native-request.v1'})
        self.assertIn('disputed',schema['properties']['decision_status']['enum'])
        self.assertIn('source_ids',schema['properties'])
