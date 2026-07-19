# Benchmark Run Artifact Retention Policy

Status: active for new benchmark campaigns

## Core Rule

Commit the smallest evidence package that supports the decision. Full per-call runtime
directories stay outside Git by default.

## Keep In Git

- the campaign report and decision boundary;
- run and contamination manifests;
- aggregate scores and pre-registered gate results;
- compact human-review or disagreement records;
- decisive fail-closed or redline evidence; and
- fingerprints needed to identify runner, fixture, prompt, model, and code lineage.

## Keep Outside Git By Default

- per-call prompts and full answers;
- event streams, stderr, and last-message files;
- generator, triage, action, and judge intermediate records;
- duplicated schemas and telemetry; and
- disposable or independently owned shadow fixtures.

Raw output may be retained in sealed external storage or a temporary audit branch when
required. The committed report must say where it can be recovered and whether that
location is expected to remain available.

## Exception Test

A raw artifact belongs in Git only when the report cannot support a material claim
without it. The exception must name the claim, the exact artifact, and why a compact
extract is insufficient. Convenience and possible future interest are not sufficient.

Existing historical campaigns are not automatically rewritten by this policy. Their
cleanup requires a separate scoped inventory so decision-bearing evidence is not
deleted accidentally.
