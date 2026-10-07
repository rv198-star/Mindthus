#!/usr/bin/env python3
"""Compile an Explain draft to HTML, recover its source, or patch one section.

The default is stdout-only. An explicit --output creates a file; --overwrite is
required to replace one. No browser, server, model, install, or network is invoked.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
from explain_compiler import compile_source, recover_source, patch_source, CompilerError, VERSION
from explain_compiler.layout import select_engine
from explain_compiler.model import MAX_SOURCE_BYTES


def read_text(name: str, limit: int = MAX_SOURCE_BYTES) -> str:
    if name == '-':
        data = sys.stdin.buffer.read(limit + 1)
    else:
        with Path(name).expanduser().open('rb') as f:
            data = f.read(limit + 1)
    if len(data) > limit:
        raise CompilerError('size_limit', 'Input exceeds the supported size.', component='input')
    return data.decode('utf-8')


def write_output(text: str, filename: str | None, *, overwrite: bool = False,
                 suffix: str | None = None) -> None:
    if filename is None:
        sys.stdout.write(text)
        return
    target = Path(filename).expanduser()
    if suffix and target.suffix.lower() != suffix:
        raise CompilerError('invalid_output_path', f'This output needs a {suffix} suffix.', component='output')
    if target.is_symlink() or (target.exists() and not overwrite):
        raise CompilerError('output_exists', 'Refusing to replace the output; use a new path or explicit --overwrite.', component='output')
    if not target.parent.is_dir():
        raise CompilerError('output_parent_missing', 'Create the explicit output directory first.', component='output')
    # Validate and render before opening the destination. Failed renders leave it intact.
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='wb', dir=target.parent, prefix='.explain-', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(text.encode('utf-8')); stream.flush(); os.fsync(stream.fileno())
        if overwrite:
            os.replace(temporary, target)
        else:
            # Hard-link creation is atomic and never overwrites a concurrently-created file.
            os.link(temporary, target)
            temporary.unlink()
    finally:
        if temporary is not None and temporary.exists(): temporary.unlink()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', action='version', version=VERSION)
    subs = parser.add_subparsers(dest='action', required=True)
    for name in ('render', 'patch'):
        sub = subs.add_parser(name)
        sub.add_argument('input', help='UTF-8 draft, or existing exported HTML for patch; - reads stdin')
        sub.add_argument('--engine', choices=('auto', 'node', 'python'), default='auto')
        sub.add_argument('--format', choices=('fragment', 'document', 'app-block', 'json'), default='fragment')
        sub.add_argument('--style', choices=('warn', 'off'))
        sub.add_argument('--glossary', help='Explicit JSON alias-to-preferred-term mapping')
        sub.add_argument('--output')
        sub.add_argument('--overwrite', action='store_true')
        if name == 'patch':
            sub.add_argument('--block', required=True)
            sub.add_argument('--replacement', required=True, help='Body-only UTF-8 Markdown, or - for stdin')
    recover = subs.add_parser('recover')
    recover.add_argument('input')
    recover.add_argument('--output')
    recover.add_argument('--overwrite', action='store_true')
    probe = subs.add_parser('probe')
    probe.add_argument('--engine', choices=('auto', 'node', 'python'), default='auto')
    args = parser.parse_args(argv)
    try:
        if args.action == 'probe':
            selected, reason, _ = select_engine(args.engine)
            print(json.dumps({'engine_selected': selected, 'fallback_reason': reason}, ensure_ascii=False))
            return 0
        if args.action == 'recover':
            source = recover_source(read_text(args.input, MAX_SOURCE_BYTES * 30))
            write_output(source, args.output, overwrite=args.overwrite, suffix='.md' if args.output else None)
            return 0
        if args.action == 'patch':
            if args.input == '-' and args.replacement == '-':
                raise CompilerError('invalid_input', 'Only one patch input can use stdin.', component='patch')
            source = recover_source(read_text(args.input, MAX_SOURCE_BYTES * 30))
            source = patch_source(source, args.block, read_text(args.replacement))
        else:
            source = read_text(args.input)
        glossary = json.loads(read_text(args.glossary)) if args.glossary else None
        fmt = args.format
        if args.output and fmt in ('fragment', 'app-block'):
            raise CompilerError('invalid_delivery', 'A saved HTML page needs --format document; use stdout for inline delivery.', component='output')
        result = compile_source(source, engine=args.engine,
            output_format='document' if fmt == 'document' else 'fragment', style=args.style, glossary=glossary)
        if fmt == 'app-block':
            output = json.dumps({'language': 'html', 'entrypoint': 'index.html', 'bundle_version': 1,
                'title': result['title'], 'variant': 'inline', 'icon': 'app', 'content': result['html']}, ensure_ascii=False)
        elif fmt == 'json':
            output = json.dumps(result, ensure_ascii=False)
        else:
            output = result['html']
        suffix = ('.json' if fmt == 'json' else '.html') if args.output else None
        write_output(output, args.output, overwrite=args.overwrite, suffix=suffix)
        diagnostics = {k: result[k] for k in ('engine_selected', 'fallback_reason', 'source_sha256', 'render_elapsed_ms', 'warnings')}
        print(json.dumps(diagnostics, ensure_ascii=False), file=sys.stderr)
        return 0
    except (CompilerError, OSError, UnicodeError, ValueError) as exc:
        data = exc.as_dict() if isinstance(exc, CompilerError) else {'code': 'input_output_error', 'message': str(exc)}
        print(json.dumps({'error': data}, ensure_ascii=False), file=sys.stderr)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
