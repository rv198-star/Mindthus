# Mindthus Versioning Policy

## Core Rule

Mindthus uses an issue-first, release-later workflow.

Do not start by promising a version scope. Start by capturing real defects, design
questions, research needs, and improvement opportunities as issues. After a coherent
set of issues has been completed and verified, decide whether the work deserves a
release and which version number fits the actual change boundary.

## Why

Mindthus is still refining a judgment philosophy / method kernel. Many important
changes begin as unclear concerns and become sharper through discussion, pressure tests,
and implementation.

If a version target is fixed too early, the project can become version-driven instead of
problem-driven. This is especially risky for method work, where the best solution may be
smaller, more elegant, or differently shaped than the initial plan.

## Issue First

Use issues to capture work before assigning a release target.

Suggested issue kinds:

- `bug`: existing behavior, documentation, or contract is wrong.
- `feature`: a new capability or method surface may be needed.
- `design`: the right shape is not clear yet.
- `research`: A/B testing, threshold cases, or evidence are needed.
- `refactor`: structure should improve without necessarily changing capability.
- `docs`: explanation, README, methodology, or release text needs improvement.
- `architecture`: cross-cutting concerns, shared primitives, method boundaries, or
  maintenance rules need design attention.

Issues do not need a milestone at creation time. Add a milestone only after the issue is
clear enough and its release relevance is understood.

## Release Later

After a group of issues is completed, ask:

- Do the completed changes form a coherent release theme?
- Did they change behavior, method contracts, public docs, or only internal notes?
- Are tests, pressure cases, or reviews sufficient for the claim?
- Is a tag useful for users, or should the work remain unreleased until more issues
  accumulate?
- What version number matches the completed boundary?

## Version Number Guidance

- `patch`, for example `v0.5.3`: documentation fixes, small tests, wording changes,
  packaging fixes, or narrow behavior fixes that do not reshape method usage.
- `minor`, for example `v0.6.0`: new method structure, shared primitive extraction,
  entry discipline, routing changes, or other changes that affect how users understand
  or call Mindthus.
- `major`, for example `v1.0.0`: stable external method surfaces, installation behavior,
  and long-term compatibility expectations.

The version number should describe what was completed, not what was originally imagined.

## Boundary

Version names such as `v0.6` may be used as direction labels, but they should not freeze
scope before the underlying issues are understood.

Do not create large release plans that force unrelated issues into a version. Prefer
small, coherent releases with honest claim boundaries.
