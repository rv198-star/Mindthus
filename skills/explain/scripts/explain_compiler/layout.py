"""Choose Node when available; use a deterministic stdlib graph fallback otherwise."""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import unicodedata
from .model import CompilerError

ROOT = Path(__file__).resolve().parent
PROTOCOL = 'explain.geometry.v2'


def wrap_label(text: str, columns: int = 25) -> list[str]:
    lines, buf, width = [], '', 0
    for ch in text:
        w = 0 if unicodedata.combining(ch) else (2 if unicodedata.east_asian_width(ch) in ('W', 'F') else 1)
        if ch == '\n' or (buf and width + w > columns):
            lines.append(buf); buf, width = '', 0
        if ch != '\n': buf += ch; width += w
    if buf or not lines: lines.append(buf)
    return lines


def text_width(line: str) -> float:
    return sum(0 if unicodedata.combining(c) else (14 if unicodedata.east_asian_width(c) in ('W', 'F') else 7.6) for c in line)


def prepare_graphs(doc: dict) -> list[dict]:
    result = []
    for section in doc['sections']:
        for index, block in enumerate(section['blocks']):
            if block['kind'] != 'flow': continue
            graph = {**block, 'id': f'{section["id"]}-{index}'}
            graph['nodes'] = []
            for node in block['nodes']:
                lines = wrap_label(node['label'])
                graph['nodes'].append({**node, 'lines': lines,
                    'width': max(108, max(map(text_width, lines)) + 32), 'height': len(lines) * 20 + 32})
            graph['edges'] = []
            for edge in block['edges']:
                lines = wrap_label(edge['label'], 22) if edge['label'] else []
                graph['edges'].append({**edge, 'lines': lines,
                    'width': max(map(text_width, lines), default=0) + (16 if lines else 0),
                    'height': len(lines) * 18 + (10 if lines else 0)})
            result.append(graph)
    return result


def verify_assets(names: list[str]) -> None:
    try:
        manifest = json.loads((ROOT / 'assets.json').read_text(encoding='utf-8'))
        for name in names:
            expected = manifest['files'][name]
            actual = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            if actual != expected: raise ValueError('digest_mismatch')
    except (OSError, KeyError, ValueError) as exc:
        raise CompilerError('installation_integrity', 'Compiler assets are missing or incompatible; reinstall the matching package.', component='engine') from exc


def select_engine(requested: str = 'auto', *, probe_timeout: float = 2.0) -> tuple[str, str | None, str | None]:
    if requested not in ('auto', 'node', 'python'):
        raise CompilerError('invalid_engine', 'Choose auto, node or python.', component='engine')
    if requested == 'python': return 'python', None, None
    executable = shutil.which('node')
    reason = None
    if executable is None:
        reason = 'node_missing'
    else:
        try:
            probe = subprocess.run([executable, '--version'], text=True, capture_output=True,
                                   timeout=probe_timeout, check=False)
            version = re.fullmatch(r'v(\d+)\.\d+\.\d+(?:-[\w.-]+)?\s*', probe.stdout)
            if probe.returncode != 0 or not version: reason = 'node_probe_invalid'
            elif int(version[1]) < 20: reason = 'node_too_old'
        except subprocess.TimeoutExpired:
            reason = 'node_probe_timeout'
        except (OSError, UnicodeError):
            reason = 'node_unexecutable'
    if reason:
        if requested == 'node':
            raise CompilerError('engine_unavailable', f'Requested Node backend is unavailable: {reason}.', component='engine')
        return 'python', reason, None
    verify_assets(['layout.mjs', '_vendor/dagre.mjs'])
    return 'node', None, executable


def python_layout(graph: dict) -> dict:
    """Linear spine with distinct external lanes; all edges, including cycles, survive.

    This deliberately favors auditable geometry over reproducing Dagre in Python.
    Wide graphs scroll locally; the accompanying relation list is always available.
    """
    horizontal = graph['direction'] == 'LR'
    positioned, lookup, cursor = [], {}, 36.0
    cross = max((n['height'] if horizontal else n['width'] for n in graph['nodes']), default=100)
    for node in graph['nodes']:
        extent = node['width'] if horizontal else node['height']
        center = {'id': node['id'], 'x': cursor + extent / 2 if horizontal else 36 + cross / 2,
                  'y': 36 + cross / 2 if horizontal else cursor + extent / 2}
        positioned.append(center); lookup[node['id']] = {**node, **center}
        cursor += extent + 56
    routed, lane = [], cross + 70.0
    for edge in graph['edges']:
        a, b = lookup[edge['from']], lookup[edge['to']]
        if horizontal:
            start = {'x': a['x'], 'y': a['y'] + a['height']/2}
            end = {'x': b['x'], 'y': b['y'] + b['height']/2}
            pts = [start, {'x': start['x'], 'y': lane}, {'x': end['x'], 'y': lane}, end]
            if a['id'] == b['id']:
                end = {'x': b['x'] + min(24, b['width']/3), 'y': end['y']}
                pts[2] = {'x': end['x'], 'y': lane}; pts[3] = end
            x, y = (pts[1]['x'] + pts[2]['x'])/2, lane
            lane += max(46, edge['height'] + 20)
        else:
            start = {'x': a['x'] + a['width']/2, 'y': a['y']}
            end = {'x': b['x'] + b['width']/2, 'y': b['y']}
            pts = [start, {'x': lane, 'y': start['y']}, {'x': lane, 'y': end['y']}, end]
            if a['id'] == b['id']:
                end = {'x': end['x'], 'y': b['y'] + min(24, b['height']/3)}
                pts[2] = {'x': lane, 'y': end['y']}; pts[3] = end
            x, y = lane, (pts[1]['y'] + pts[2]['y'])/2
            lane += max(56, edge['width'] + 24)
        routed.append({'id': edge['id'], 'points': pts, 'x': x, 'y': y})
    width, height = (cursor, lane + 36) if horizontal else (lane + 36, cursor)
    # Include label extents (self-call labels can reach beyond the node spine).
    for geom, edge in zip(routed, graph['edges']):
        width = max(width, geom['x'] + edge['width']/2 + 24)
        height = max(height, geom['y'] + edge['height']/2 + 24)
    return {'id': graph['id'], 'width': width, 'height': height, 'nodes': positioned, 'edges': routed}


def validate_geometry(graphs: list[dict], result: dict) -> list[dict]:
    def finite(n) -> bool:
        return isinstance(n, (int, float)) and not isinstance(n, bool) and math.isfinite(n) and abs(n) <= 10_000_000
    try:
        if result['protocol'] != PROTOCOL or len(result['graphs']) != len(graphs): raise ValueError()
        for src, out in zip(graphs, result['graphs']):
            if out['id'] != src['id']: raise ValueError()
            if not all(finite(out[k]) and out[k] > 0 for k in ('width', 'height')): raise ValueError()
            for key in ('nodes', 'edges'):
                if [n['id'] for n in out[key]] != [n['id'] for n in src[key]]: raise ValueError()
                for obj in out[key]:
                    if not all(finite(obj[k]) for k in ('x', 'y')): raise ValueError()
                    if key == 'edges':
                        if len(obj['points']) < 2: raise ValueError()
                        if not all(finite(p['x']) and finite(p['y']) for p in obj['points']): raise ValueError()
    except (KeyError, ValueError, TypeError) as exc:
        raise CompilerError('renderer_invalid_output', 'Layout output failed the geometry contract.', component='engine') from exc
    return result['graphs']


def layout_graphs(doc: dict, *, engine: str = 'auto', render_timeout: float = 12.0) -> tuple[list[dict], str, str | None]:
    graphs = prepare_graphs(doc)
    selected, reason, executable = select_engine(engine)
    if selected == 'node' and graphs:
        try:
            process = subprocess.run([executable, str(ROOT / 'layout.mjs')],
                input=json.dumps({'protocol': PROTOCOL, 'graphs': graphs}, ensure_ascii=False),
                text=True, capture_output=True, timeout=render_timeout, check=False)
        except subprocess.TimeoutExpired as exc:
            raise CompilerError('renderer_timeout', 'Node layout exceeded its time limit; no backend retry was performed.', component='engine') from exc
        except (OSError, UnicodeError) as exc:
            raise CompilerError('renderer_failed', 'Node layout could not complete after preflight.', component='engine') from exc
        if process.returncode != 0:
            raise CompilerError('renderer_failed', 'Node layout failed; no backend retry was performed.', component='engine')
        try: payload = json.loads(process.stdout)
        except ValueError as exc:
            raise CompilerError('renderer_invalid_output', 'Node did not return geometry JSON.', component='engine') from exc
        geometry = validate_geometry(graphs, payload)
    else:
        geometry = [python_layout(g) for g in graphs]
        validate_geometry(graphs, {'protocol': PROTOCOL, 'graphs': geometry})
    return [{**g, 'geometry': geo} for g, geo in zip(graphs, geometry)], selected, reason
