#!/usr/bin/env python3
"""Review-only inline renderer using the existing authored sample bodies.

Stdout fragment/app-block is the normal output. --qa-out explicitly saves developer
fixtures, not user-facing downloads or a ChatGPT rendering receipt.
"""
from __future__ import annotations
import argparse
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from uuid import uuid4
import build

HERE = Path(__file__).resolve().parent
VOID = frozenset('area base br col embed hr img input link meta param source track wbr'.split())


class InlineBody(HTMLParser):
    """Scope ids and label responsive cells without editing the source facts."""
    def __init__(self, instance: str):
        super().__init__(convert_charrefs=False)
        self.instance, self.parts = instance, []
        self.skip = 0
        self.headers, self.header_text = [], None
        self.in_head, self.cell = False, 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if self.skip:
            if tag not in VOID: self.skip += 1
            return
        if 'toolbar' in a.get('class', '').split() or a.get('id') == 'empty':
            self.skip = 1
            return
        if tag == 'table': self.headers = []; a['role'] = 'table'
        if tag == 'thead': self.in_head = True; a['role'] = 'rowgroup'
        if tag == 'tbody': a['role'] = 'rowgroup'
        if tag == 'tr': self.cell = 0; a['role'] = 'row'
        if tag == 'th':
            a['role'] = 'rowheader' if a.get('scope') == 'row' else 'columnheader'
            if self.in_head: self.header_text = []
        if tag == 'td':
            a['role'] = 'cell'
            if self.cell < len(self.headers): a['data-label'] = self.headers[self.cell]
            self.cell += 1
        if 'id' in a:
            value = a.pop('id')
            if value: a['id'] = f'{self.instance}-{value}'; a['data-local-id'] = value
        for key, value in list(a.items()):
            if key in ('aria-labelledby', 'aria-describedby') and value:
                a[key] = ' '.join(f'{self.instance}-{v}' for v in value.split())
            elif isinstance(value, str) and 'url(#' in value:
                a[key] = value.replace('url(#', f'url(#{self.instance}-')
            elif key == 'href' and value and value.startswith('#'):
                a[key] = f'#{self.instance}-{value[1:]}'
        attributes = ''.join(f' {k}' if v is None else f' {k}="{escape(v, quote=True)}"' for k, v in a.items())
        self.parts.append(f'<{tag}{attributes}>')

    def handle_endtag(self, tag):
        if self.skip:
            self.skip -= 1
            return
        if tag == 'th' and self.header_text is not None:
            self.headers.append(''.join(self.header_text)); self.header_text = None
        if tag == 'thead': self.in_head = False
        self.parts.append(f'</{tag}>')

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)
            if self.header_text is not None: self.header_text.append(data)

    def handle_entityref(self, name):
        if not self.skip: self.parts.append(f'&{name};')

    def handle_charref(self, name):
        if not self.skip: self.parts.append(f'&#{name};')


def fragment(case: str, engine: str = 'node', *, instance: str | None = None) -> str:
    instance = instance or f'embed-{uuid4().hex[:12]}'
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*', instance):
        raise ValueError('instance must be a simple HTML identifier')
    source = build.pinned(build.SOURCES[case])
    body = build.mechanism(source, engine) if case == 'mechanism' else {
        'report': build.report, 'progress': build.progress, 'comparison': build.comparison}[case]()
    parser = InlineBody(instance); parser.feed(body); parser.close()
    css, js = [(HERE / f'inline.{ext}').read_text(encoding='utf-8') for ext in ('css', 'js')]
    metadata = json.dumps({'case': case, 'source_sha256': build.sha(source.encode()),
        'source_path': build.SOURCES[case], 'engine': engine, 'scope': 'prototype fragment, not host receipt'}, ensure_ascii=False).replace('<', '\\u003c')
    return (f'<article class="ex-inline" id="{instance}" lang="zh-CN" data-case="{case}">'
        f'<style>{css}</style><header class="inline-head"><h1>{escape(build.TITLES[case])}</h1>'
        '<span class="demo-mark">演示材料 · 非真实项目进度</span></header>'
        + ''.join(parser.parts)
        + '<details class="sources"><summary>原材料与来源</summary><div class="source-inner">'
        f'<p class="source-note">{escape(build.SOURCES[case])}<br>SHA-256: {build.sha(source.encode())}</p>'
        '<div class="source-actions"><button type="button" class="js" data-copy-source>复制原材料</button></div>'
        f'<pre class="source-text" data-source-text>{escape(source)}</pre><p class="status" role="status"></p>'
        f'</div></details><script type="application/json" data-embed-metadata>{metadata}</script><script>{js}</script></article>')


def app_block(case: str, html: str) -> dict:
    # This matches the existing prepare-only envelope; it does not invoke a host.
    return {'language':'html', 'entrypoint':'index.html', 'bundle_version':1,
            'title':build.TITLES[case], 'variant':'inline', 'icon':'app', 'content':html}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--case', choices=list(build.SOURCES), default='report')
    p.add_argument('--engine', choices=['node', 'python'], default='node')
    p.add_argument('--format', choices=['fragment', 'app-block'], default='fragment')
    p.add_argument('--qa-out', type=Path, help='Explicit development fixtures; not normal delivery')
    args = p.parse_args()
    if not args.qa_out:
        html = fragment(args.case, args.engine)
        print(json.dumps(app_block(args.case, html), ensure_ascii=False) if args.format == 'app-block' else html)
        return
    root = args.qa_out.resolve()
    if root.exists(): raise SystemExit('Use a new QA directory; prior evidence is immutable.')
    root.mkdir(parents=True)
    rows = []
    for case, source_path in build.SOURCES.items():
        for engine in ['node', 'python']:
            html = fragment(case, engine, instance=f'embed-{case}-{engine}')
            (root / f'{case}-{engine}.fragment.html').write_text(html, encoding='utf-8')
            (root / f'{case}-{engine}.app-block.json').write_text(json.dumps(app_block(case, html), ensure_ascii=False), encoding='utf-8')
            rows.append({'case':case, 'engine':engine, 'source_sha256':build.sha(build.pinned(source_path).encode()), 'fragment_sha256':build.sha(html.encode())})
    (root / 'manifest.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'fixtures':len(rows), 'out':str(root), 'actual_host_receipt':False}))


if __name__ == '__main__': main()
