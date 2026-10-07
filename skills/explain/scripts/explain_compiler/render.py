"""Shared safe HTML serialization. Both layout engines use this exact renderer."""
from __future__ import annotations
from decimal import Decimal
from html import escape, unescape
from html.parser import HTMLParser
import json
import re
from urllib.parse import urlsplit
from .model import CompilerError, SCHEMA, VERSION, source_hash, MAX_SOURCE_BYTES
from .layout import ROOT, verify_assets
from ._vendor.mistune import create_markdown
from ._vendor.mistune.core import BlockState
from ._vendor.mistune.renderers.html import HTMLRenderer
from ._vendor.mistune.plugins.table import table


class SafeMarkdown(HTMLRenderer):
    def safe_url(self, url: str) -> str:
        value = unescape(url)
        normalized = re.sub(r'[\x00-\x20\x7f]', '', value)
        try: scheme = urlsplit(normalized).scheme.lower()
        except ValueError: scheme = 'invalid'
        if scheme not in ('', 'http', 'https', 'mailto'):
            raise CompilerError('unsafe_link', 'Only relative, HTTP(S), and mailto links are supported.', component='markdown')
        return escape(value, quote=True)

    def link(self, text: str, url: str, title: str | None = None) -> str:
        t = f' title="{escape(title, quote=True)}"' if title else ''
        return f'<a href="{self.safe_url(url)}" rel="noopener noreferrer"{t}>{text}</a>'

    def image(self, text: str, url: str, title: str | None = None) -> str:
        # Images are explicit links, never implicit requests or embedded executable SVG.
        return '<span class="ex-image-link">' + self.link(text or escape(url), url, title) + '</span>'


_MD = create_markdown(renderer=SafeMarkdown(escape=True), plugins=[table])


def markdown(tokens: list[dict]) -> str:
    html = _MD.renderer.render_tokens(tokens, BlockState())
    # Only renderer-generated table tags can match, because input HTML is escaped.
    return html.replace('<table>', '<div class="ex-table-scroll" tabindex="0" role="region" aria-label="Table"><table>')\
               .replace('</table>', '</table></div>')


def fmt(number: float) -> str:
    return f'{number:.3f}'.rstrip('0').rstrip('.')


def svg_text(lines: list[str], x: float, y: float, css: str, gap: int = 20) -> str:
    top = y - (len(lines) - 1) * gap / 2
    body = ''.join(f'<tspan x="{fmt(x)}" y="{fmt(top + i*gap)}">{escape(line)}</tspan>' for i, line in enumerate(lines))
    return f'<text class="{css}" text-anchor="middle" dominant-baseline="central">{body}</text>'


def graph_html(graph: dict, prefix: str, zh: bool) -> str:
    geo = graph['geometry']; marker = prefix + '-arrow'
    lookup = {n['id']: n for n in graph['nodes']}
    parts = [f'<figure data-component="flow"><div class="ex-graph-scroll" tabindex="0" role="region" aria-label="{ "流程关系图" if zh else "Flow diagram" }">',
             f'<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="{prefix}-title" width="{fmt(geo["width"])}" height="{fmt(geo["height"])}" viewBox="0 0 {fmt(geo["width"])} {fmt(geo["height"])}">',
             f'<title id="{prefix}-title">{escape("；".join(n["label"] for n in graph["nodes"]))}</title>',
             f'<defs><marker id="{marker}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="ex-arrow" d="M0 0 L10 5 L0 10 Z"/></marker></defs>']
    for edge, geometry in zip(graph['edges'], geo['edges']):
        path = ' '.join(('M' if i == 0 else 'L') + fmt(p['x']) + ' ' + fmt(p['y']) for i, p in enumerate(geometry['points']))
        cls = 'ex-edge ex-edge-dashed' if edge['dashed'] else 'ex-edge'
        parts.append(f'<g data-edge-id="{edge["id"]}" data-from="{edge["from"]}" data-to="{edge["to"]}"><path class="{cls}" d="{path}" marker-end="url(#{marker})"/>')
        if edge['label']:
            x, y, w, h = geometry['x'], geometry['y'], edge['width'], edge['height']
            parts.append(f'<rect class="ex-edge-label-box" x="{fmt(x-w/2)}" y="{fmt(y-h/2)}" width="{fmt(w)}" height="{fmt(h)}" rx="5"/>')
            parts.append(svg_text(edge['lines'], x, y, 'ex-edge-label', 18))
        parts.append('</g>')
    for node, geometry in zip(graph['nodes'], geo['nodes']):
        x, y, w, h = geometry['x'], geometry['y'], node['width'], node['height']
        parts.append(f'<g data-node-id="{node["id"]}"><rect class="ex-node-box" x="{fmt(x-w/2)}" y="{fmt(y-h/2)}" width="{fmt(w)}" height="{fmt(h)}" rx="9"/>')
        parts.append(svg_text(node['lines'], x, y, 'ex-node-text'))
        parts.append('</g>')
    parts.extend(['</svg></div>', '<details class="ex-relations"><summary>' + ('查看文字关系' if zh else 'Read the relationships') + '</summary><ul>'])
    if not graph['edges']:
        parts.extend(f'<li>{escape(n["label"])}</li>' for n in graph['nodes'])
    for edge in graph['edges']:
        description = lookup[edge['from']]['label'] + ' → ' + lookup[edge['to']]['label']
        if edge['label']: description += '：' + edge['label']
        parts.append('<li>' + escape(description) + '</li>')
    parts.append('</ul></details></figure>')
    return ''.join(parts)


def progress_html(block: dict, zh: bool) -> str:
    parts, interval = ['<div class="ex-metrics" data-component="progress">'], False
    for row in block['rows']:
        label, unit = escape(row['label']), escape(row['unit'])
        unknown = row['low'] is None
        shown = ('未提供' if zh else 'Not supplied') if unknown else row['value'].replace('..', '–')
        cls = 'ex-unknown' if unknown else 'ex-value'
        parts.append(f'<div class="ex-metric"><div class="ex-metric-top"><strong>{label}</strong><span class="{cls}">{escape(shown)} <small>{unit}</small></span></div>')
        if not unknown and row['unit'] in ('%', 'percent'):
            low, high = Decimal(row['low']), Decimal(row['high'])
            if low == high:
                attrs = f'role="progressbar" aria-label="{label}" aria-valuemin="0" aria-valuemax="100" aria-valuenow="{row["low"]}"'
            else:
                attrs = f'role="img" aria-label="{label}: {row["low"]}–{row["high"]}%"'
                interval = True
            parts.append(f'<div class="ex-bar" {attrs}><span class="ex-bar-solid" style="width:{low}%"></span><span class="ex-bar-uncertain" style="width:{high-low}%"></span></div>')
        parts.append(f'<p class="ex-basis">{escape(row["basis"])}</p></div>')
    if interval:
        parts.append('<p class="ex-range-legend">' + ('实色：已知下界 · 斜纹：不确定区间；不取中值。' if zh else 'Solid: lower bound · Hatched: uncertain interval; no midpoint is substituted.') + '</p>')
    parts.append('</div>')
    return ''.join(parts)


def render_html(doc: dict, source: str, graphs: list[dict], *, output_format: str = 'fragment') -> str:
    if output_format not in ('fragment', 'document'):
        raise CompilerError('invalid_format', 'Choose fragment or document.', component='delivery')
    verify_assets(['page.css', 'page.js'])
    css = (ROOT/'page.css').read_text(encoding='utf-8')
    script = (ROOT/'page.js').read_text(encoding='utf-8')
    meta = doc['meta']; zh = meta['lang'].lower().startswith('zh')
    graph_map = {g['id']: g for g in graphs}
    prefix = 'ex-' + doc['source_sha256'][:12]
    labels = ('线性阅读', '深色模式', '展开详情', '复制源稿', '本页交付稿') if zh else ('Linear reading', 'Dark mode', 'Expand details', 'Copy source', 'Page source')
    parts = [f'<div class="ex-root" data-layout="{meta["layout"]}" data-theme="{meta["theme"]}" data-mode="light" data-lang="{escape(meta["lang"],quote=True)}">',
             f'<style>{css}</style><header class="ex-hero"><div class="ex-eyebrow">MINDTHUS / EXPLAIN</div>',
             f'<h1>{escape(meta["title"])}</h1>']
    if meta['subtitle']: parts.append(f'<p class="ex-subtitle">{escape(meta["subtitle"])}</p>')
    parts.append('<div class="ex-tools">')
    for action, label in zip(('layout', 'dark', 'expand'), labels):
        pressed = 'true' if action == 'layout' and meta['layout'] == 'doc' else 'false'
        parts.append(f'<button type="button" class="ex-js-only" data-ex-action="{action}" aria-pressed="{pressed}">{label}</button>')
    if output_format == 'document':
        parts.append(f'<button type="button" class="ex-js-only" data-ex-action="copy">{labels[3]}</button>')
    parts.append('</div></header><nav class="ex-nav" aria-label="' + ('章节导航' if zh else 'Sections') + '">')
    for p in doc['sections']:
        if p['title']: parts.append(f'<a href="#{prefix}-{p["id"]}">{escape(p["title"])}</a>')
    parts.append('</nav><div class="ex-grid">')
    serial = 0
    for section in doc['sections']:
        if not section['blocks'] and not section['title']: continue
        serial += 1
        tag = 'details' if section['collapsed'] else 'section'
        span = ' ex-span-2' if section['span'] == 2 or not section['title'] else ''
        parts.append(f'<{tag} class="ex-panel{span}" id="{prefix}-{section["id"]}" data-block-id="{section["id"]}">')
        if section['title']:
            if section['collapsed']:
                parts.append(f'<summary>{escape(section["title"])}</summary>')
            else:
                parts.append(f'<div class="ex-panel-head"><span class="ex-number">{serial:02}</span><h2>{escape(section["title"])}</h2></div>')
        parts.append('<div class="ex-content">')
        for index, block in enumerate(section['blocks']):
            kind = block['kind']
            if kind == 'markdown': parts.append(markdown(block['tokens']))
            elif kind == 'callout':
                parts.append(f'<aside class="ex-callout" data-component="callout" data-tone="{block["tone"]}"><span class="ex-tone">{escape(block["tone"])}</span><h3>{escape(block["title"])}</h3>{markdown(block["tokens"])}</aside>')
            elif kind == 'code':
                parts.append(f'<div><div class="ex-code-label">{escape(block["language"])}</div><pre><code>{escape(block["text"])}</code></pre></div>')
            elif kind == 'flow':
                key = f'{section["id"]}-{index}'
                parts.append(graph_html(graph_map[key], f'{prefix}-{key}', zh))
            elif kind == 'progress': parts.append(progress_html(block, zh))
            else: raise CompilerError('unsupported_component', 'No renderer for ' + kind, component=kind)
        parts.append(f'</div></{tag}>')
    parts.append('</div>')
    if output_format == 'document':
        data = json.dumps({'schema': SCHEMA, 'source_sha256': source_hash(source), 'source': source}, ensure_ascii=False)
        data = data.replace('&','\\u0026').replace('<','\\u003c').replace('>','\\u003e').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
        parts.append(f'<script type="application/json" data-explain-source="v2">{data}</script>')
        parts.append(f'<details class="ex-source-view"><summary>{labels[4]}</summary><textarea readonly aria-label="{labels[4]}">{escape(source)}</textarea></details><p class="ex-status" aria-live="polite"></p>')
    parts.append(f'<footer class="ex-footer">Explain HTML {VERSION} · {doc["source_sha256"][:12]}</footer>')
    parts.append(f'<script>{script}</script></div>')
    fragment = ''.join(parts)
    if output_format == 'fragment': return fragment
    return f'<!doctype html>\n<html lang="{escape(meta["lang"],quote=True)}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(meta["title"])}</title></head><body>{fragment}</body></html>\n'


class _SourceReader(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.collecting = False
        self.entries = []
        self.parts = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'script' and attrs.get('data-explain-source') == 'v2':
            if attrs.get('type') != 'application/json':
                raise CompilerError('invalid_source_record', 'Source record has an invalid type.', component='recover')
            self.collecting = True; self.parts = []

    def handle_endtag(self, tag):
        if tag == 'script' and self.collecting:
            self.entries.append(''.join(self.parts)); self.collecting = False

    def handle_data(self, data):
        if self.collecting: self.parts.append(data)


def recover_source(html: str) -> str:
    if len(html.encode('utf-8')) > MAX_SOURCE_BYTES * 30:
        raise CompilerError('size_limit', 'HTML is too large to recover.', component='recover')
    reader = _SourceReader(); reader.feed(html); reader.close()
    if len(reader.entries) != 1 or reader.collecting:
        raise CompilerError('source_missing_or_ambiguous', 'Expected exactly one complete source record.', component='recover')
    try:
        data = json.loads(reader.entries[0]); source = data['source']
        if data['schema'] != SCHEMA or not isinstance(source, str) or source_hash(source) != data['source_sha256']:
            raise ValueError()
    except (ValueError, KeyError, TypeError) as exc:
        raise CompilerError('source_integrity', 'Embedded source does not match its digest or schema.', component='recover') from exc
    return source
