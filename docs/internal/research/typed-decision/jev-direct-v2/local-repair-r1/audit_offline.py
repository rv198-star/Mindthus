"""Reproduce scoped tests from an exported source tree without git/Codex/network.

Only substitute git HEAD identity and the hash-only executable fixture path.
Model transport remains mocked by tests; the outer guards reject accidental calls.
"""
import argparse
import shutil
import socket
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

REPO=next(p for p in Path(__file__).resolve().parents if (p/'experiments/jev_direct').is_dir())
sys.path.insert(0,str(REPO))
from experiments.jev_direct import pilot


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source-commit',required=True)
    args=parser.parse_args()
    original=subprocess.check_output;which=shutil.which
    def check_output(command,*a,**kw):
        if list(command)==['git','rev-parse','HEAD']:
            value=args.source_commit+'\n'
            return value if kw.get('text') else value.encode()
        return original(command,*a,**kw)
    with patch.object(subprocess,'check_output',side_effect=check_output), \
         patch.object(shutil,'which',side_effect=lambda name,*a,**kw:sys.executable if name=='codex' else which(name,*a,**kw)), \
         patch.object(socket.socket,'connect',side_effect=AssertionError('audit_network_forbidden')), \
         patch.object(pilot.wire,'_run_cli',side_effect=AssertionError('audit_model_call_forbidden')):
        suite=unittest.defaultTestLoader.loadTestsFromNames([
            'tests.test_jev_direct_local','tests.test_jev_direct_router','tests.test_test_lifecycle'])
        return 0 if unittest.TextTestRunner(verbosity=1).run(suite).wasSuccessful() else 1

if __name__=='__main__':raise SystemExit(main())
