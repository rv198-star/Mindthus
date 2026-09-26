"""Lossless full-source preparation; no LLM shortlist, inference or silent trimming."""
from pathlib import Path, PurePosixPath
from typing import Any
import hashlib
import json
import subprocess

SCHEMA = 'mindthus.jev-direct-full-context.v1'
SCOPES = ('all_skill_entries_and_methodologies', 'all_skill_markdown_and_methodologies')
ROUTABLE = ('3l5s', 'edsp', 'mpg', 'sela', 'sra', 'tplan', 'tvg', 'wae')
EXPLICIT_ONLY = ('case-prep',)
ENTRY = 'using-mindthus'


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf8')


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def need(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def source_paths(repo: Path, *, include_resources: bool = False) -> list[str]:
    repo = repo.resolve()
    entries = set(repo.glob('skills/*/SKILL.md'))
    methods = set(repo.glob('docs/methodologies/**/*.md'))
    need(bool(entries) and bool(methods), 'full_source_roots_missing')
    paths = entries | methods
    if include_resources:
        paths |= set(repo.glob('skills/**/*.md'))
    output = []
    for p in sorted(paths):
        need(p.is_file() and not p.is_symlink() and p.resolve().is_relative_to(repo),
             'unsafe_full_source_path')
        output.append(p.relative_to(repo).as_posix())
    return output


def build_corpus(repo: Path, *, include_resources: bool = False) -> dict:
    repo = repo.resolve()
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip()
    rows = []
    for path in source_paths(repo, include_resources=include_resources):
        raw = (repo / path).read_bytes()
        content = raw.decode('utf8')  # Preserve original newlines and trailing whitespace.
        role = ('skill_entry' if PurePosixPath(path).name == 'SKILL.md' else
                'methodology' if path.startswith('docs/methodologies/') else 'skill_resource')
        rows.append({'path': path, 'role': role, 'bytes': len(raw),
                     'sha256': sha(raw), 'content': content})
    manifest = {r['path']: {k: r[k] for k in ('role', 'bytes', 'sha256')} for r in rows}
    corpus = {'schema': SCHEMA, 'source_revision': revision,
              'scope': SCOPES[1 if include_resources else 0],
              'manifest': manifest, 'manifest_sha256': sha(canonical(manifest)), 'documents': rows,
              'pre_route_llm_calls': 0, 'summarized': False, 'truncated': False}
    validate_corpus(corpus, repo=repo)
    return corpus


def validate_corpus(corpus: dict, *, repo: Path | None = None) -> None:
    need(corpus.get('schema') == SCHEMA and corpus.get('scope') in SCOPES, 'corpus_schema_or_scope')
    need(corpus.get('pre_route_llm_calls') == 0 and corpus.get('summarized') is False
         and corpus.get('truncated') is False, 'full_input_semantics')
    manifest = corpus['manifest']; rows = corpus['documents']
    need(sha(canonical(manifest)) == corpus['manifest_sha256'], 'manifest_digest')
    need(len({r['path'] for r in rows}) == len(rows), 'duplicate_source')
    need({r['path'] for r in rows} == set(manifest), 'incomplete_full_source')
    for row in rows:
        p = PurePosixPath(row['path'])
        need(not p.is_absolute() and '..' not in p.parts, 'unsafe_full_source_path')
        raw = row['content'].encode('utf8')
        need(row['bytes'] == len(raw) and row['sha256'] == sha(raw), 'changed_source_content')
        need(manifest[row['path']] == {k: row[k] for k in ('role', 'bytes', 'sha256')}, 'source_manifest_mismatch')
    if repo is not None:
        repo = repo.resolve()
        need(set(manifest) == set(source_paths(repo, include_resources=corpus['scope'] == SCOPES[1])),
             'repository_source_coverage_changed')
        for row in rows:
            need((repo / row['path']).read_bytes() == row['content'].encode('utf8'), 'source_bytes_changed')


def make_state(corpus: dict, user_input: dict) -> dict:
    validate_corpus(corpus)
    need(set(user_input) == {'documents', 'conversation', 'authority'}, 'raw_input_fields')
    documents = user_input['documents']; conversation = user_input['conversation']
    need(isinstance(documents, list) and bool(documents), 'raw_documents_missing')
    docs = {}
    for d in documents:
        need(set(d) == {'id', 'revision', 'kind', 'text'} and isinstance(d['text'], str), 'raw_document_shape')
        need(d['id'] not in docs, 'duplicate_user_document'); docs[d['id']] = d
    need(isinstance(conversation, list) and bool(conversation), 'conversation_missing')
    orders = [m['order'] for m in conversation]
    need(orders == sorted(set(orders)), 'conversation_order')
    for item in conversation:
        need(item['document_id'] in docs and docs[item['document_id']]['kind'] == item['role'], 'conversation_binding')
    need(conversation[-1]['role'] == 'user', 'latest_request_not_user')
    state = {'user_input': json.loads(canonical(user_input)),
             'full_reference_documents': {r['path']: r['content'] for r in corpus['documents']},
             'reference_version': corpus['source_revision'], 'reference_manifest_sha256': corpus['manifest_sha256'],
             'source_roles': {r['path']: r['role'] for r in corpus['documents']},
             'interpretation': ('user_input is the actual task and evidence; full_reference_documents are method contracts, '
                 'not business facts or permission grants. Examples illustrate contracts, not the answer to this user. '
                 'A mentioned path is not proof that a referenced file was loaded.')}
    need(len(state['full_reference_documents']) == len(corpus['documents']), 'incomplete_state')
    return state


def statistics(corpus: dict, state: dict) -> dict:
    validate_corpus(corpus)
    return {'scope': corpus['scope'], 'source_revision': corpus['source_revision'],
            'document_count': len(corpus['documents']),
            'document_bytes': sum(r['bytes'] for r in corpus['documents']),
            'document_characters': sum(len(r['content']) for r in corpus['documents']),
            'state_wire_bytes': len(canonical(state)), 'manifest_sha256': corpus['manifest_sha256'],
            'official_token_count': None, 'old_transport_byte_limit': 262144,
            'exceeds_old_transport_byte_limit': len(canonical(state)) > 262144,
            'official_documented_state_plus_longest_question_tokens': 32000,
            'official_documented_total_tokens': 64000,
            'supplier_capacity_status': 'not_tested', 'pre_route_llm_calls': 0}
