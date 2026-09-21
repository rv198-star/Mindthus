# Typed Decision / System-One Decision Contract Principles

Status: **Normative design rule for the experimental typed-decision line**  
Scope: Jev and other fast typed semantic-decision providers  
Current first provider: Jev  
Related governance: #209, #210, #211, #212

## Core

> LLM / human compiles an open problem into a bounded decision contract; System-One executes fast typed semantic judgments; deterministic runtime owns composition, policy, permission, execution, evidence and recovery.

The reusable asset is the **Decision Contract**, not a Jev-specific prompt or API shape.

Four layers must remain distinct:

```text
Evidence / State
      ↓
Decision Contract
      ↓
System-One Judgment
      ↓
Policy & Runtime
```

- **State does not decide.**
- **Decision Contract does not execute.**
- **System-One does not invent policy or authority.**
- **Runtime does not invent semantic meaning.**

A typed answer proves only that the provider returned a value inside the declared answer space. It does not prove the state was sufficient, the contract was correct, the answer was true, or the resulting action is authorized.

### Portability invariant

```text
Decision Contract = standard
Decision Engine   = replaceable semantic capability
Provider/Transport = serving path
Resolved Runtime  = observed execution fact
```

A provider swap for the same engine must not require a Decision DAG rewrite. A different engine may implement the same `select / assess_proposition / rate` API, but behavioral qualification never transfers automatically across engines, versions, languages, distributions or consequence classes. Provider/transport details must stay in adapters and runtime evidence, not in the Decision Contract.

## 1. Start From Execution Consequence

Design from the concrete downstream decision:

- Which branch, gate, rank, handoff, or bounded action can change?
- Which part of that change actually needs semantic judgment?
- Which parts are already deterministic and belong in code?

Do not begin from “what can Jev answer?”

Deterministic lookup, arithmetic, schema validation, identity, permissions, counters, dependency existence and exact state transitions stay deterministic.

Open-ended problem definition, candidate creation, broad causal reasoning and artifact generation stay LLM/human-owned unless a bounded sub-judgment is explicitly compiled.

## 2. State = Sufficient Relevant Context, Not Context Dump

A DecisionProvider receives the context needed for the specific judgment, with irrelevant material excluded.

Do **not** optimize for the smallest possible token count when doing so destroys the relationship being judged. Keep mutually relevant facts together.

Prefer named structured state:

```yaml
claim: ...
evidence: ...
policy: ...
relevant_history: ...
```

Separate provenance classes where they matter:

- observed fact / runtime evidence;
- user goal, value or risk posture;
- policy / method contract;
- LLM inference or summary;
- unknown / missing input.

A summary cannot silently increase the evidence status of its sources.

System-One calls are stateless. Required context must be present in the current snapshot or explicit reference contract; do not assume memory from prior calls.

## 3. One Question = One Coherent Semantic Dimension

A question should be narrow enough that its answer has one meaning and one downstream use.

“Single dimension” does **not** mean “split semantics into the smallest possible atoms.” Preserve the relationship being judged.

Good pattern:

> Given the declared responsibility, dependencies and task state, is this candidate suitable to own this responsibility?

Bad pattern:

> Is this good, safe, complete and ready to ship?

Split independent dimensions when their answers have different meaning, downstream consequence or error policy.

## 4. Questions Must Be Self-Describing

Question IDs are runtime identifiers, not semantic instructions.

Every question must carry enough meaning in its instructions and criteria to be understood from the supplied State.

When useful, reference named State fields explicitly.

For close Choice options, prefer criteria that distinguish:

```text
what it is
what it is not for
representative examples / boundary cases
```

Do not rely on method names, short labels or option names to carry the full semantics.

## 5. Do Not Manufacture Meta-Judgments

Do not add a second-order question such as:

> “Do you have enough information to answer the previous question?”

unless that judgment has an independent downstream use that cannot be handled more directly.

Use deterministic checks for mechanically required fields.

If semantic option coverage may be incomplete, represent that explicitly with an admissible outcome such as:

```text
unclear
other
none_of_the_above
not_applicable
```

A low confidence answer, missing field, provider failure and genuine semantic no-match are different states and must not be collapsed.

## 6. Batch Independent Questions Sharing the Same State

Logical dependency and physical API batching are separate concerns.

Questions that:

- use the same State;
- do not require another model answer to construct their own input;
- have compatible access boundaries;

should normally be evaluated together.

Speculative questions may be evaluated before the runtime knows whether their answers will be consumed, when doing so stays inside the declared budget.

Start a later batch only when an upstream result materially changes:

- what evidence must be acquired;
- the State snapshot;
- the candidate set / rubric;
- the applicable contract or authority surface.

A Decision DAG is a **semantic dependency graph**, not an API-call graph.

## 7. Use Choice / Noul / Score According To Their Semantics

### Choice

Use for selecting among a declared set of qualitatively different alternatives.

If the alternatives may not cover reality, include an explicit no-match / other / unclear option or use another admissibility mechanism.

Do not force a wrong choice simply to keep the answer typed.

### Noul / Proposition Probability

Use for a clearly defined yes/no proposition.

Its numeric result is the provider's probability for the affirmative proposition.

Noul is not a general “degree” or “strength” scale. If the concept is ordinal, use a Score rubric instead.

### Score

Use for a genuinely ordered set of semantic levels.

Rubric levels should be meaningful descriptions, not bare arbitrary numbers.

The returned score is a position induced by the probability distribution across those levels; it is not automatically a real-world measurement unit.

## 8. Composition, Weights And Vetoes Belong To Policy

Multiple typed judgments may be combined when the policy is declared outside the provider.

Weighted composition is legitimate for compensatory preferences when:

- the component semantics are stable;
- normalization is explicit;
- weights are owned by policy / code;
- the composed result has a declared meaning.

Hard vetoes, safety limits, authority constraints and mandatory prerequisites must remain separate. They cannot be averaged away by favorable scores elsewhere.

Do not multiply provider probabilities and call the result “overall decision correctness” unless a separately justified statistical model actually supports that interpretation.

## 9. Probability And Confidence Are Signals, Not Authority

Provider probabilities / confidence describe the local answer distribution under the supplied State and Decision Contract.

They do **not** directly measure:

- correctness of the Decision Contract;
- completeness of State;
- correctness of the overall DAG;
- correctness of user goals or policy;
- authorization to execute;
- whole-task success probability.

Execution requires a separate qualification and policy decision:

```text
typed result
+ qualified node / graph version
+ validated language / input distribution
+ risk and consequence policy
+ authority boundary
→ advisory / bounded execution / escalate / stop
```

Thresholds are empirical properties of a particular provider, version, contract, language, task distribution and consequence class. They are not universal constants.

## 10. Runtime LLM Design = Bounded Dynamic Compilation

Default order:

1. reuse a qualified DecisionSpec / GraphSpec;
2. bind parameters within a qualified template;
3. compose existing qualified pieces when semantics remain unchanged;
4. only for a named coverage gap, allow LLM/human to design a bounded new question or subgraph;
5. otherwise let the LLM handle the open problem directly.

Dynamic design must:

- name the uncovered problem;
- preserve the existing goal, policy source, authority and acceptance floor;
- produce a declarative, versioned contract;
- freeze that version for the current run;
- have a design / execution budget and semantic-revision limit;
- avoid recursively launching unbounded new design chains;
- avoid changing the question because the current answer is undesirable;
- start with no inherited high-risk execution qualification unless separately validated;
- retain lineage to the predecessor contract / run.

A temporary dynamic graph remains scoped to the declared task until wider reuse is independently qualified.

## Design Review Checklist

Before adding or changing a System-One node, verify:

1. **Consequence** — Which real action or branch can this answer change?
2. **Owner** — Why is this semantic judgment not deterministic code or open-ended LLM work?
3. **State** — Are all relevant facts present and irrelevant material excluded?
4. **Provenance** — Are facts, inference, policy and user constraints distinguishable?
5. **Question** — Is one coherent semantic dimension being judged?
6. **Coverage** — Can reality fall outside the answer space? If yes, where is the no-match path?
7. **Batch** — Which same-state questions can execute together?
8. **Dependency** — Which later questions truly require changed State or candidate sets?
9. **Policy** — Where are weights, vetoes, thresholds and authority defined?
10. **Fallback** — What happens on missing context, no-match, abstention, unsupported capability and provider error?
11. **Recovery** — Which result can be reused after interruption and what invalidates it?
12. **Evidence** — How will local judgment quality and end-to-end value be evaluated independently?

## Mindthus Boundary

This rule does not require every Mindthus method to become a Decision DAG.

Use typed decisions only where a bounded semantic judgment can be stated and independently tested without destroying the parent method's meaning.

Method truth remains owned by the canonical Mindthus method contracts.

TPlan continues to own Mission/task lifecycle and mutation authority. Existing evidence, permission and release gates remain authoritative unless an explicit experiment delta says otherwise.

The experimental typed-decision line must not claim Stable promotion from schema validity, fast latency, low price or a few high-confidence examples.

## References

Current experimental governance and implementation:

- `docs/internal/research/typed-decision/standard.md`
- `docs/internal/research/typed-decision/portfolio.md`
- `docs/internal/research/typed-decision/implementation.md`
- `docs/internal/research/typed-decision/verification.json`

External model documentation is supporting evidence for provider semantics; Mindthus acceptance remains based on its own tests and task evidence.

Provider-design references checked during the 2026-09-22 consolidation:

- `https://github.com/typesafe-ai/skills/blob/main/skills/typesafe-ai/SKILL.md`
- `https://docs.typesafe.ai/concepts/state`
- `https://docs.typesafe.ai/primitives/choice`
- `https://docs.typesafe.ai/primitives/noul`
- `https://docs.typesafe.ai/primitives/score`
- `https://docs.typesafe.ai/confidence`
