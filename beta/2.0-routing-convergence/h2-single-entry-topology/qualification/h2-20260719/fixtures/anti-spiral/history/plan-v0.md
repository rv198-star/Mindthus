# Checkout Latency Incident Plan

## Goal

Restore checkout p95 below 800 ms without increasing payment failures.

## Current response

1. Capture aggregate latency and payment outcomes.

## Open blocker

No trace currently identifies which downstream hop causes the regression. The incident
cannot choose a durable fix until representative traces or an equivalent causal signal
exist.
