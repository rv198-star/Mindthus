# HTML V2 compiler provenance

The compiler borrows the short-draft/renderer separation from
`QingYunA/answer-me-with-html` at commit
`3f1e3ade9146e5ab385d3ae1d80bb3c89cc71f72`. Its Skill, CLI, parser, themes and product
services are not copied or installed as dependencies.

The implementation uses pinned upstream code distributed with the Skill:

- Mistune 3.1.3: Markdown parsing; MIT. Two packaging-only changes: the Python <3.11
  Self annotation uses stdlib TypeVar, and built-in plugin imports resolve relative
  to the vendored namespace rather than a global mistune installation.
- @dagrejs/dagre 3.1.1, including @dagrejs/graphlib 4.0.5: Node graph layout; MIT.
  The upstream self-contained browser bundle has only an ES-module export appended.

Exact package URLs, archive checksums, installed-file SHA-256 values and modifications
are in [the vendor manifest](../scripts/explain_compiler/_vendor/manifest.json).
Licenses are in the same directory: `MISTUNE-LICENSE`, `DAGRE-LICENSE`,
`DAGRE-LEGAL.txt` and `GRAPHLIB-LICENSE`.

These are prepackaged developer inputs, not runtime downloads. Explain's draft grammar,
source recovery, shared safe serializer, Python fallback layout and writing hints are
Mindthus code. The Node process receives only the graphs needed for layout, not prose,
conversation history or credentials. Generated HTML contains neither the Python parser
nor the Node layout library; diagrams are already rendered SVG.
