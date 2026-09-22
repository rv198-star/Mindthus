# C01 completion technical recovery 2 — OCI carrier

## Authority and new facts

Owner supplied a CPA credential for `https://cpa.72live.com/v1` and explicitly authorized
`deepseek-v4.1-flash` as primary with `glm-5.3-flash` as backup.

This is a new recovery identity. It does not modify or overwrite the terminal
`trial-user-agent-recovery-1` records.

Before this recovery was admitted, OCI read-only diagnostics observed:

- DNS resolution for `cpa.72live.com` succeeded;
- TLS 1.3 negotiation and certificate validation succeeded;
- Python's default urllib User-Agent reached Cloudflare 403 / code 1010;
- `Mindthus-C01-integration/1` reached the CPA authentication layer and returned
  HTTP 401 JSON `Missing API key`.

These observations do not prove the old N03 request was never processed and do not
retroactively change its recorded `transport_failure`.

## Scope

Only two gaps are admitted:

1. **N03 host recovery** — reuse the repository-preserved N03 handoff prompt and obtain
   one downstream host answer. No Jev call.
2. **E01 fresh full path** — run the already-frozen synthetic E01 context through the
   current official TypeSafe Jev C01 graph, verified handoff, then CPA host answer.

No L27/L28/L22 replay, no semantic prompt revision, no label change, no C02 work.

## Model/fallback rule

Primary host model: `deepseek-v4.1-flash`.

Backup host model: `glm-5.3-flash`, allowed **only** when the primary host attempt has
no complete valid response because of a technical/provider/transport/response-contract
failure. A complete primary answer is terminal even if later task-quality review is poor.
The backup must consume the identical handoff/prompt and is not a semantic retry.

E01 routing uses official TypeSafe `jev-1.13.0` with the existing choice-rounding adapter.
Routing has no provider/model fallback and no automatic retry.

## Ceilings

- N03 CPA: 1 primary + at most 1 technical-fallback call.
- E01 TypeSafe Jev: at most 3 calls, 60 inference seconds, USD 0.008064 reserve.
- E01 CPA: 1 primary + at most 1 technical-fallback call.
- Total new calls: at most 7.
- CPA output ceiling: 1600 tokens/call; request body <= 49152 bytes.
- No semantic revisions, no automatic retries.

CPA prices/currency and failed-request charges remain unknown unless the service returns
a documented value. TypeSafe reserve is not an actual-cost claim.

## Stop and evidence rules

All offline checks, source/freeze validation and full regression must pass before any
live call. Source is committed before live execution.

If N03 primary and backup both fail technically, stop before E01.
If E01 routing fails, record it and stop; do not replace the engine or alter the graph.
If E01 primary host fails technically, one GLM backup is allowed against the same handoff.
No further calls after that backup.

Persist request hashes, allowed model/usage fields, bounded error codes and answers.
Never persist headers, credentials, hidden reasoning or full provider error bodies.
Exact-key scans must pass after execution.

Success in this recovery is evidence for the missing integration chain only. It is not
an independent holdout, formal A/B/C, native skill-load proof or #211 qualification.
