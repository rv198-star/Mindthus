"""Public errors and size limits for the source-backed presentation compiler."""
from __future__ import annotations
import hashlib

SCHEMA = 'explain.presentation.v2'
VERSION = '2.0.0'
MAX_SOURCE_BYTES = 1_000_000
MAX_NODES = 120
MAX_EDGES = 240

class CompilerError(ValueError):
    def __init__(self, code: str, message: str, *, line: int = 0,
                 component: str = 'document', example: str = '') -> None:
        super().__init__(message)
        self.code, self.line, self.component, self.example = code, line, component, example

    def as_dict(self) -> dict:
        return {'code': self.code, 'message': str(self), 'line': self.line,
                'component': self.component, 'example': self.example}


def source_hash(source: str) -> str:
    return hashlib.sha256(source.encode('utf-8')).hexdigest()
