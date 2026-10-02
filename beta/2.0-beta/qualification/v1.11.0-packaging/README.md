# v1.11.0 packaging compatibility

Scope: deterministic assembly only, no model calls or Beta benefit qualification.

The prior ROI.2 correction and qualified SRA Thin Core stay frozen. Stable's slimmer
3L5S removed the former English anchor. The composition profile now binds the exact
shared-source SHA256 and replacement location; the builder still takes correction.after
from the historical qualification profile. Other shared text remains unchanged except
existing namespace and identity rewrites.

Four offline counterexamples pass: exact correction and other text preserved, old
unadapted path remains supported, wrong hash/path fail, missing/duplicate anchor fail.
`anchor-tests.txt` is the original log. Exact final Stable ref/tree, full composed-file
comparison and downloaded archive verification are recorded in the release verification.

The existing qualification_ref is historical, not a claim that v1.11.0 was part of that
old test. No new routing rules, questions, model budgets or publication exception.
