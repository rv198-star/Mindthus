"""One parser for both engines; the source and line spans stay recoverable."""
from __future__ import annotations
import json
import re
import shlex
from decimal import Decimal, InvalidOperation
from .model import CompilerError, SCHEMA, MAX_SOURCE_BYTES, MAX_NODES, MAX_EDGES, source_hash
from ._vendor.mistune import create_markdown
from ._vendor.mistune.plugins.table import table

CODE_LANGUAGES = frozenset('text txt plaintext python py javascript js typescript ts json yaml yml bash sh shell zsh sql css html svg xml diff toml ini rust rs go java c cpp csharp ruby rb php md markdown dockerfile powershell ps1'.split())
EXAMPLES = {
    'flow': '```flow LR\n输入 -> 编译: 语义稿\n编译 -> 页面\n```',
    'progress': '```progress\n已声明进度 | 62 | % | 上游给出的指标\n剩余工作 | 6..9 | 小时 | 估计，不是测量\n未知项 | ? | 小时 | 尚未估计\n```',
    'callout': '```callout info\n结论标题\n结论与重要限定。\n```',
    'document': '---\ntitle: 报告\nlayout: sheet\n---\n## 结论 {#result}\n内容。',
}
FENCE = re.compile(r'^ {0,3}(`{3,}|~{3,})([^\r\n]*)\r?\n?$')
HEADING = re.compile(r'^ {0,3}##[ \t]+(.+?)\s*$')
ID = re.compile(r'^[A-Za-z][A-Za-z0-9_-]{0,63}$')
_META = {'title': None, 'subtitle': None, 'layout': {'doc', 'sheet'},
         'theme': {'paper', 'blueprint'}, 'lang': None, 'style': {'warn', 'off'}}
_AST = create_markdown(renderer='ast', plugins=[table])


def error(message: str, line: int, kind: str = 'document', code: str = 'syntax_error') -> None:
    raise CompilerError(code, message, line=line, component=kind,
                        example=EXAMPLES.get(kind, EXAMPLES['document']))


def _sections(source: str) -> tuple[dict, list[dict]]:
    """Scan only frontmatter, level-two headings and fence boundaries, not Markdown."""
    lines = source.splitlines(keepends=True)
    offsets, pos = [], 0
    for line in lines:
        offsets.append(pos)
        pos += len(line)
    offsets.append(pos)
    meta = {'title': 'Explain', 'subtitle': '', 'layout': 'doc', 'theme': 'paper',
            'lang': 'zh-CN', 'style': 'warn'}
    i = 0
    if lines and lines[0].strip() == '---':
        seen = set()
        i = 1
        while i < len(lines) and lines[i].strip() != '---':
            if lines[i].strip():
                match = re.fullmatch(r'([a-z]+):[ \t]*(.*?)\s*', lines[i].rstrip('\r\n'))
                if not match or match[1] not in _META:
                    error('Use a supported scalar frontmatter key.', i + 1)
                key, value = match.groups()
                if key in seen:
                    error(f'Duplicate frontmatter key: {key}', i + 1)
                seen.add(key)
                if value.startswith('"'):
                    try:
                        value = json.loads(value)
                    except json.JSONDecodeError:
                        error('Invalid quoted scalar.', i + 1)
                elif len(value) >= 2 and value.startswith("'") and value.endswith("'"):
                    value = value[1:-1].replace("''", "'")
                if not isinstance(value, str) or not value:
                    error('Frontmatter values must be nonempty strings.', i + 1)
                if _META[key] is not None and value not in _META[key]:
                    error(f'Unsupported {key}: {value}', i + 1)
                if key == 'lang' and not re.fullmatch(r'[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*', value):
                    error('Invalid language tag.', i + 1)
                meta[key] = value
            i += 1
        if i == len(lines):
            error('Unclosed frontmatter.', 1)
        i += 1
    sections = []
    current = {'id': 'intro', 'title': '', 'collapsed': False, 'span': 1,
               'start': offsets[i], 'body_start': offsets[i], 'line': i + 1}
    opened = None
    explicit_ids = {'intro'}
    for j in range(i, len(lines)):
        raw = lines[j]
        fence = FENCE.match(raw)
        if opened:
            if fence and fence[1][0] == opened[0][0] and len(fence[1]) >= len(opened[0]) and not fence[2].strip():
                opened = None
            continue
        if fence:
            opened = (fence[1], j + 1)
            continue
        match = HEADING.match(raw.rstrip('\r\n'))
        if not match:
            continue
        current['end'] = offsets[j]
        sections.append(current)
        title = match[1]
        spec = re.search(r'\s+\{([^{}]+)\}\s*$', title)
        sid, collapsed, span = f'section-{len(sections)}', False, 1
        if spec:
            title = title[:spec.start()].rstrip()
            for flag in shlex.split(spec[1]):
                if flag.startswith('#'):
                    sid = flag[1:]
                    if not ID.fullmatch(sid):
                        error('Block IDs must be ASCII identifiers (1–64 characters).', j + 1)
                elif flag == 'collapsed':
                    collapsed = True
                elif flag in ('span=1', 'span=2'):
                    span = int(flag[-1])
                else:
                    error(f'Unknown block option: {flag}', j + 1)
        if not title:
            error('A section needs a title.', j + 1)
        if sid in explicit_ids:
            error(f'Duplicate block ID: {sid}', j + 1, code='ambiguous_block')
        explicit_ids.add(sid)
        current = {'id': sid, 'title': title, 'collapsed': collapsed, 'span': span,
                   'start': offsets[j], 'body_start': offsets[j + 1], 'line': j + 2}
    if opened:
        error('Unclosed fenced block.', opened[1])
    current['end'] = len(source)
    sections.append(current)
    return meta, sections


def _outside_split(text: str, separator: str) -> list[str]:
    """Split delimiters outside quotes and node brackets. Backslash escapes a delimiter."""
    result, part, stack, quote, escape = [], [], [], None, False
    pairs = {'[': ']', '(': ')', '{': '}'}
    i = 0
    while i < len(text):
        ch = text[i]
        if escape:
            part.append(ch); escape = False; i += 1; continue
        if ch == '\\':
            escape = True; part.append(ch); i += 1; continue
        if quote:
            part.append(ch)
            if ch == quote: quote = None
            i += 1; continue
        if ch in ('"', "'"):
            quote = ch; part.append(ch); i += 1; continue
        if ch in pairs:
            stack.append(pairs[ch]); part.append(ch); i += 1; continue
        if stack and ch == stack[-1]:
            stack.pop(); part.append(ch); i += 1; continue
        if not stack and text.startswith(separator, i):
            result.append(''.join(part).strip()); part = []; i += len(separator); continue
        part.append(ch); i += 1
    if stack or quote:
        raise ValueError('Unclosed quote or node bracket.')
    result.append(''.join(part).strip())
    return result


def parse_flow(text: str, args: list[str], line: int) -> dict:
    if len(args) > 1 or (args and args[0] not in ('LR', 'TB')):
        error('flow accepts LR or TB.', line, 'flow')
    nodes, edges = {}, []

    def node(raw: str, at: int) -> str:
        raw = raw.strip()
        if raw in nodes:
            return nodes[raw]['id']
        explicit = re.fullmatch(r'([A-Za-z][A-Za-z0-9_.-]*)\[(.*)\]', raw)
        if explicit:
            key, label = explicit.groups()
        else:
            if raw.startswith('[') and raw.endswith(']'):
                label = raw[1:-1]
            elif raw.startswith('"'):
                try: label = json.loads(raw)
                except json.JSONDecodeError: error('Invalid quoted node label.', at, 'flow')
            else:
                label = raw
            key = label
        if not isinstance(label, str) or not label.strip() or len(label) > 2000:
            error('Node labels must be nonempty and at most 2000 characters.', at, 'flow')
        if key in nodes:
            if nodes[key]['label'] != label:
                error(f'Conflicting labels for node {key}.', at, 'flow')
        else:
            if len(nodes) >= MAX_NODES:
                error('flow node limit exceeded.', at, 'flow', 'size_limit')
            nodes[key] = {'id': f'n{len(nodes)}', 'label': label, 'line': at}
        return nodes[key]['id']

    for offset, raw in enumerate(text.splitlines()):
        if not raw.strip(): continue
        at = line + offset
        try:
            parts = _outside_split(raw, ':')
            relation, label = parts[0], ':'.join(parts[1:]).strip()
            # Chains have one terminal edge label; no inference from punctuation or position.
            chain = _outside_split(relation, '->')
            if len(chain) == 1:
                if label:
                    error('Use id[label] for a node declaration, or A -> B: label.', at, 'flow')
                node(chain[0], at)
                continue
            groups = [_outside_split(item, '&') for item in chain]
            for k in range(len(groups) - 1):
                for left in groups[k]:
                    dashed = left.endswith('-')
                    if dashed: left = left[:-1].rstrip()
                    for right in groups[k + 1]:
                        if right.endswith('-'): right = right[:-1].rstrip()
                        if len(edges) >= MAX_EDGES:
                            error('flow edge limit exceeded.', at, 'flow', 'size_limit')
                        edges.append({'id': f'e{len(edges)}', 'from': node(left, at),
                                      'to': node(right, at), 'label': label if k == len(groups) - 2 else '',
                                      'dashed': dashed, 'line': at})
        except ValueError as exc:
            if isinstance(exc, CompilerError): raise
            error(str(exc), at, 'flow')
    if not nodes:
        error('flow needs at least one node.', line, 'flow')
    if len(nodes) > MAX_NODES or len(edges) > MAX_EDGES:
        error(f'flow supports at most {MAX_NODES} nodes and {MAX_EDGES} edges per block.', line, 'flow', 'size_limit')
    return {'kind': 'flow', 'direction': args[0] if args else 'TB',
            'nodes': list(nodes.values()), 'edges': edges, 'line': line}


def parse_progress(text: str, args: list[str], line: int) -> dict:
    if args: error('progress accepts no options.', line, 'progress')
    rows = []
    for offset, raw in enumerate(text.splitlines()):
        if not raw.strip(): continue
        try: fields = _outside_split(raw, '|')
        except ValueError as exc: error(str(exc), line + offset, 'progress')
        if len(fields) != 4 or any(not field for field in fields):
            error('Use label | value or low..high or ? | unit | basis.', line + offset, 'progress')
        label, value, unit, basis = fields
        row = {'label': label, 'value': value, 'unit': unit, 'basis': basis,
               'low': None, 'high': None, 'line': line + offset}
        if value != '?':
            values = value.split('..')
            if len(values) not in (1, 2): error('Invalid range.', line + offset, 'progress')
            try:
                numbers = [Decimal(x) for x in values]
                if any(not n.is_finite() or n < 0 for n in numbers): raise InvalidOperation()
            except (InvalidOperation, ValueError):
                error('Use finite nonnegative decimal values.', line + offset, 'progress')
            if numbers[0] > numbers[-1]: error('Range lower bound exceeds upper bound.', line + offset, 'progress')
            if unit in ('%', 'percent') and numbers[-1] > 100:
                error('Percentage values must be between 0 and 100.', line + offset, 'progress')
            if any(n > Decimal('1e100') for n in numbers):
                error('Value exceeds the supported display range.', line + offset, 'progress', 'size_limit')
            row['low'], row['high'] = str(numbers[0]), str(numbers[-1])
        rows.append(row)
    if not rows: error('progress needs at least one row.', line, 'progress')
    return {'kind': 'progress', 'rows': rows, 'line': line}


def _blocks(body: str, start_line: int) -> list[dict]:
    lines = body.splitlines(keepends=True)
    blocks, pending = [], []
    first = start_line

    def flush() -> None:
        nonlocal pending
        if pending and ''.join(pending).strip():
            text = ''.join(pending)
            blocks.append({'kind': 'markdown', 'text': text, 'tokens': _AST(text), 'line': first})
        pending = []

    i = 0
    while i < len(lines):
        match = FENCE.match(lines[i])
        if not match:
            if not pending: first = start_line + i
            pending.append(lines[i]); i += 1; continue
        flush()
        at = start_line + i
        marker, info = match.groups()
        try: args = shlex.split(info.strip())
        except ValueError as exc: error(str(exc), at)
        kind = args.pop(0).lower() if args else 'text'
        if kind == 'component':
            if not args: error('Name the component after component.', at)
            kind = args.pop(0)
        i += 1
        inner = []
        while i < len(lines):
            end = FENCE.match(lines[i])
            if end and end[1][0] == marker[0] and len(end[1]) >= len(marker) and not end[2].strip(): break
            inner.append(lines[i]); i += 1
        if i == len(lines): error('Unclosed fenced block.', at, kind)
        content = ''.join(inner)
        if kind == 'flow':
            blocks.append(parse_flow(content, args, at + 1))
        elif kind in ('progress', 'range'):
            blocks.append(parse_progress(content, args, at + 1))
        elif kind == 'callout':
            if len(args) > 1 or (args and args[0] not in ('info', 'ok', 'warn', 'error')):
                error('callout accepts info, ok, warn or error.', at, kind)
            content_lines = content.splitlines()
            if not content_lines or not content_lines[0].strip(): error('callout needs a title.', at, kind)
            rest = '\n'.join(content_lines[1:])
            blocks.append({'kind': kind, 'tone': args[0] if args else 'info',
                           'title': content_lines[0], 'text': rest, 'tokens': _AST(rest), 'line': at + 1})
        elif kind in CODE_LANGUAGES:
            if args: error('Code fences accept a language only; file reads are not supported.', at, kind)
            blocks.append({'kind': 'code', 'language': kind, 'text': content, 'line': at + 1})
        else:
            error(f'Unsupported component or code language: {kind}', at, kind, 'unsupported_component')
        i += 1
    flush()
    return blocks


def parse_source(source: str) -> dict:
    if not isinstance(source, str) or not source.strip() or '\x00' in source:
        error('Source must be nonempty UTF-8 text without NUL.', 1, code='invalid_source')
    if len(source.encode('utf-8')) > MAX_SOURCE_BYTES:
        error('Source exceeds 1 MB.', 1, code='size_limit')
    meta, sections = _sections(source)
    for section in sections:
        section['blocks'] = _blocks(source[section['body_start']:section['end']], section['line'])
    return {'schema': SCHEMA, 'meta': meta, 'sections': sections, 'source_sha256': source_hash(source)}


def patch_source(source: str, block_id: str, replacement: str) -> str:
    """Replace only the body of one section. No file writes or whole-source rewrite."""
    doc = parse_source(source)
    matches = [p for p in doc['sections'] if p['id'] == block_id and p['title']]
    if len(matches) != 1:
        raise CompilerError('unknown_block', 'Provide exactly one existing section ID.', component='patch')
    p = matches[0]
    # Section headings belong to the original source, not to the replacement body.
    _, candidate_sections = _sections(replacement)
    if len(candidate_sections) != 1:
        raise CompilerError('invalid_patch', 'A block patch is body-only; do not add ## sections.', component='patch')
    eol = '\r\n' if '\r\n' in source else '\n'
    body = replacement
    if body and not body.endswith(('\n', '\r')): body += eol
    if body and not body.endswith(eol + eol): body += eol
    result = source[:p['body_start']] + body + source[p['end']:]
    parse_source(result)
    return result
