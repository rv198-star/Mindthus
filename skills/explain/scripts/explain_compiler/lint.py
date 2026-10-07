"""Advisory checks over explanatory prose only. They never rewrite or reject it."""
from __future__ import annotations
import re

_LIMITS = {'zh': (35, 45), 'en': (20, 25)}
_WORDS = {'进行优化': '优化', '进行检查': '检查', '加以说明': '说明', '予以保留': '保留'}
_EXCLUDE = re.compile(r'`+[^`]*`+|https?://\S+|\]\([^)]*\)')


def lint_document(doc: dict, *, mode: str | None = None, glossary: dict | None = None) -> list[dict]:
    if (mode or doc['meta']['style']) == 'off': return []
    warnings, seen = [], set()

    def warn(rule: str, line: int, message: str, suggestion: str = '') -> None:
        key = (rule, line, message)
        if key not in seen:
            seen.add(key)
            warnings.append({'rule': rule, 'line': line, 'severity': 'warning',
                             'message': message, 'suggestion': suggestion})

    for section in doc['sections']:
        for block in section['blocks']:
            if block['kind'] not in ('markdown', 'callout'): continue
            start = block['line'] + (1 if block['kind'] == 'callout' else 0)
            paragraph_sentences, paragraph_line = 0, start
            for offset, raw in enumerate(block['text'].splitlines() + ['']):
                line = start + offset
                if not raw.strip() or raw.lstrip().startswith(('#', '>')) or raw.startswith(('    ', '\t')):
                    if paragraph_sentences > 6:
                        warn('paragraph-length', paragraph_line, f'段落有 {paragraph_sentences} 句；可考虑分组。')
                    paragraph_sentences = 0
                    continue
                text = _EXCLUDE.sub('', raw)
                # Preserve URLs, literal code and raw markup; no heuristic substitution.
                if '<' in text and '>' in text: continue
                ordered = bool(re.match(r'\s*\d+[.)]\s+', text))
                text = re.sub(r'^\s*(?:\d+[.)]|[-*+])\s+', '', text)
                sentences = [s.strip() for s in re.split(r'[。！？!?;；]|\.(?=\s|$)', text) if s.strip()]
                if not paragraph_sentences: paragraph_line = line
                paragraph_sentences += len(sentences)
                for sentence in sentences:
                    han = len(re.findall(r'[\u3400-\u9fff]', sentence))
                    words = len(re.findall(r"[A-Za-z0-9]+(?:['’_-][A-Za-z0-9]+)*", sentence))
                    language = 'zh' if han else 'en'
                    count = han + words if han else words
                    limit = _LIMITS[language][0 if ordered else 1]
                    if count > limit:
                        warn('sentence-length', line, f'句子长度 {count}，提示阈值 {limit}。', '考虑拆分；保留条件、否定与因果。')
                for old, new in _WORDS.items():
                    if old in text: warn('wording', line, f'可简化“{old}”。', new)
                for old, new in (glossary or {}).items():
                    if old != new and re.search(r'(?<![A-Za-z0-9_])' + re.escape(old) + r'(?![A-Za-z0-9_])', text):
                        warn('terminology', line, f'与提供的词表核对：“{old}”。', new)
                if ordered and re.search(r'尽快|若干|多次', text):
                    warn('instruction-precision', line, '操作要求含未量化表述。', '仅在来源已有依据时澄清；未知则保留未知。')
    return warnings
