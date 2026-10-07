#!/usr/bin/env python3
"""Run the preregistered 18 Codex jobs once; preserve raw outputs and failed cases."""
from __future__ import annotations
import concurrent.futures, datetime, hashlib, json, os, re, signal, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
CACHE = Path('/srv/agentdock/.cache/mindthus-explain-v2-d2-model-r1')
sys.path.insert(0, str(ROOT / 'skills/explain/scripts'))
from explain_compiler import compile_source


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def normalize(raw: str) -> tuple[str, str | None]:
    text = raw.strip().lstrip('\ufeff')
    match = re.fullmatch(r'```(?:html|markdown|md)?\s*\n([\s\S]*?)\n```', text)
    if match:
        return match.group(1), 'outer_fence_removed'
    return text, 'outer_whitespace_only' if text != raw else None


def run_one(row: dict, reg: dict) -> dict:
    rid = row['id']; work = CACHE/'work'/rid; work.mkdir(parents=True, exist_ok=True)
    target = HERE/'runs'/rid; target.mkdir(parents=True, exist_ok=True)
    receipt = target/'result.json'
    if receipt.exists():
        print(f'SKIP {rid}: recorded result', flush=True)
        return json.loads(receipt.read_text())
    started = target/'started.json'
    stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with started.open('x') as f:
        json.dump({'id': rid, 'started_at_utc': stamp, 'no_automatic_retry': True}, f)
    prompt = (HERE/'prompts'/f'{rid}.txt').read_bytes()
    assert digest(prompt) == row['prompt_sha256']
    rawlog = CACHE/f'{rid}.events.jsonl'; errlog = CACHE/f'{rid}.stderr.log'
    command = ['codex', 'exec', '--json', '--ephemeral', '--sandbox', 'read-only',
               '--skip-git-repo-check', '-C', str(work), '-m', reg['model'],
               '-c', f'model_reasoning_effort="{reg["reasoning_effort"]}"',
               '-c', 'web_search="disabled"', '--color', 'never',
               '-o', str(target/'output.txt'), '-']
    before = time.perf_counter(); timeout = False
    print(f'START {rid} {row["case"]} {row["arm"]}', flush=True)
    with rawlog.open('wb') as out, errlog.open('wb') as err:
        proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=out, stderr=err, start_new_session=True)
        try:
            proc.communicate(prompt, timeout=300)
        except subprocess.TimeoutExpired:
            timeout = True; os.killpg(proc.pid, signal.SIGTERM)
            try: proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL); proc.wait()
    model_wall = time.perf_counter() - before
    usage = []; tool_items = []; sessions = []; messages = []; errors = []
    for line in rawlog.read_text(errors='replace').splitlines():
        try: event = json.loads(line)
        except json.JSONDecodeError: continue
        typ = event.get('type')
        if typ == 'thread.started': sessions.append(event.get('thread_id'))
        if typ == 'turn.completed': usage.append(event.get('usage', {}))
        if typ in ('error', 'turn.failed'):
            errors.append({'type': typ, 'record_sha256': digest(line.encode())})
        if typ == 'item.completed':
            item = event.get('item', {}); kind = item.get('type')
            if kind == 'agent_message': messages.append(item.get('text', ''))
            elif kind not in ('reasoning',): tool_items.append(kind)
    result = {**row, 'started_at_utc': stamp, 'model': reg['model'],
              'reasoning_effort': reg['reasoning_effort'], 'exit_code': proc.returncode,
              'timed_out': timeout, 'cli_wall_seconds': round(model_wall, 3),
              'usage_turns': usage, 'session_ids': sessions, 'tool_items': tool_items,
              'transport_errors': errors, 'render_wall_seconds': 0,
              'cost_usd': None, 'host_transport_seconds': None,
              'raw_log_sha256': digest(rawlog.read_bytes()), 'stderr_sha256': digest(errlog.read_bytes())}
    output = target/'output.txt'
    if not output.exists() and messages: output.write_text(messages[-1])
    if proc.returncode != 0 or not output.exists() or not output.read_text().strip():
        result['status'] = 'generation_failed'
    else:
        raw = output.read_text(); normalized, change = normalize(raw)
        result.update({'output_sha256': digest(output.read_bytes()), 'model_output_bytes':len(output.read_bytes()),
                       'normalization': change})
        ext = 'html' if row['arm'] == 'A' else 'md'
        (target/f'generated.{ext}').write_text(normalized)
        try:
            compile_start = time.perf_counter()
            if row['arm'] == 'B':
                rendered = compile_source(normalized, engine='node', output_format='document')
                (target/'page.html').write_text(rendered['html'])
                python_page = compile_source(normalized, engine='python', output_format='document')
                (target/'page-python.html').write_text(python_page['html'])
                fragment = compile_source(normalized, engine='node', output_format='fragment')
                (target/'fragment.html').write_text(fragment['html'])
                result['warnings'] = rendered['warnings']
                result['render_primary_ms'] = rendered['render_elapsed_ms']
                result['source_sha256'] = rendered['source_sha256']
            else:
                if not re.match(r'(?is)<!doctype\s+html', normalized):
                    raise ValueError('Expected complete HTML; no content repair attempted')
                (target/'page.html').write_text(normalized)
            result['render_wall_seconds'] = round(time.perf_counter()-compile_start, 4)
            page = target/'page.html'; readstart = time.perf_counter(); data = page.read_bytes()
            result['file_readback_ms'] = round((time.perf_counter()-readstart)*1000, 3)
            result['page_sha256'] = digest(data); result['page_bytes'] = len(data)
            result['status'] = 'generated_and_rendered' if not tool_items else 'generated_with_unplanned_tools'
        except Exception as exc:
            result['status'] = 'compile_failed'; result['compile_error'] = str(exc)
    result['local_delivery_seconds'] = round(model_wall+result['render_wall_seconds'],3)
    result['finished_at_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    write_json(receipt, result)
    print(f'DONE {rid} {result["status"]} {model_wall:.1f}s usage={usage}', flush=True)
    return result


def main() -> int:
    reg = json.loads((HERE/'registration.json').read_text())
    for name, expected in reg['runtime_files'].items():
        assert digest((ROOT/'skills/explain'/name).read_bytes()) == expected, name
    CACHE.mkdir(parents=True, exist_ok=True)
    rows = reg['matrix']
    if len(sys.argv)>1: rows=[r for r in rows if r['id'] in sys.argv[1:]]
    groups = [[r for r in rows if r['case_index']==n] for n in (1,2,3)]
    def series(group): return [run_one(r,reg) for r in group]
    with concurrent.futures.ThreadPoolExecutor(max_workers=reg['max_concurrent']) as pool:
        futures=[pool.submit(series, group) for group in groups if group]
        while futures:
            done, pending=concurrent.futures.wait(futures,timeout=20,return_when=concurrent.futures.FIRST_COMPLETED)
            for f in done: f.result()
            futures=list(pending)
            print(f'PROGRESS {len(list((HERE/"runs").glob("*/result.json")))}/18 recorded; {len(futures)} case streams active',flush=True)
    return 0

if __name__=='__main__': raise SystemExit(main())
