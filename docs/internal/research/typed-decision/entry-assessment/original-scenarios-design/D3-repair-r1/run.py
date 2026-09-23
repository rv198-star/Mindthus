"""Delegate the R1 input repair to the existing public-entry D3 harness."""
import argparse
import hashlib
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'D3-live/run.py'
spec = importlib.util.spec_from_file_location('d3_existing_harness_r1', SOURCE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
m.HERE = HERE
m.ROOT = Path('/srv/agentdock/tmp/mindthus-relationship-D3-repair-r1')
m.FREEZE = HERE / 'freeze.json'
m.AUTH = 'Owner authorizes internal iteration through actual correction; D3-repair-r1/protocol.md'
original_hashes = m.file_hashes

def hashes():
    return {**original_hashes(), str(SOURCE.relative_to(m.REPO)): hashlib.sha256(SOURCE.read_bytes()).hexdigest()}
m.file_hashes = hashes

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('action', choices=['prepare', 'preflight', 'run'])
    a = p.parse_args()
    if a.action == 'prepare': m.prepare()
    elif a.action == 'preflight':
        m.preflight(); print('R1 source/input/provider preflight PASS; zero inference')
    else: m.run()
