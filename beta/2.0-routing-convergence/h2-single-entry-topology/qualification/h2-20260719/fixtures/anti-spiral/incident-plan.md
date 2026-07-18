# Checkout Latency Incident Plan

## Goal

Restore checkout p95 below 800 ms without increasing payment failures.

## Current response

1. Keep the existing 10% traffic cap.
2. Capture per-hop latency and payment outcome for the affected cohort.
3. Roll back the new pricing call if p95 exceeds 1.5 s for five minutes.
4. Name an incident owner and review the evidence at 16:00 UTC.

## Open blocker

No trace currently identifies which downstream hop causes the regression. The incident
cannot choose a durable fix until representative traces or an equivalent causal signal
exist.
