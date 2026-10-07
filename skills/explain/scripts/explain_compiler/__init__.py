"""Explain HTML V2: source -> single IR -> selected layout -> shared safe HTML."""
from __future__ import annotations
import time
from .model import CompilerError, VERSION, SCHEMA
from .parser import parse_source, patch_source
from .render import render_html, recover_source
from .layout import layout_graphs
from .lint import lint_document

__all__ = ['compile_source', 'parse_source', 'patch_source', 'recover_source', 'CompilerError', 'VERSION']


def compile_source(source: str, *, engine: str = 'auto', output_format: str = 'fragment',
                   style: str | None = None, glossary: dict | None = None) -> dict:
    """Generate content only. The caller owns submission, visibility and persistence."""
    started = time.perf_counter()
    if style not in (None, 'warn', 'off'):
        raise CompilerError('invalid_style', 'Writing checks support warn or off only.', component='lint')
    if glossary is not None and (not isinstance(glossary, dict) or not all(
            isinstance(k, str) and isinstance(v, str) and k and v for k, v in glossary.items())):
        raise CompilerError('invalid_glossary', 'Glossary must map nonempty strings to nonempty strings.', component='lint')
    doc = parse_source(source)
    warnings = lint_document(doc, mode=style, glossary=glossary)
    graphs, selected, reason = layout_graphs(doc, engine=engine)
    html = render_html(doc, source, graphs, output_format=output_format)
    return {'schema': SCHEMA, 'compiler_version': VERSION,
            'source_sha256': doc['source_sha256'], 'title': doc['meta']['title'],
            'engine_selected': selected, 'fallback_reason': reason,
            'warnings': warnings, 'html': html,
            'render_elapsed_ms': round((time.perf_counter() - started) * 1000, 3)}
