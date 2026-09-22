# Internal independent design audit — bounded protocol

This admission covers design review only for original Skills/4K scenarios under #211. No Jev performance experiment, product deployment, source-code implementation, old trial replay or model fallback is authorized by this audit.

## Reviewers and isolation

- A: semantic architecture, fidelity to the original two scenarios, source hierarchy and failure counterexamples.
- B: implementability, graph dependencies, budgets, isolation, multi-turn recovery and validity of evaluation.
- Both must inspect the entire same frozen design, acceptance and source packet. Focus is not a permission to ignore other defects.
- Each is a new CPA chat-completions request to `deepseek-v4.1-flash`. This uses the already authorized primary model. There is no previous conversation, no writer's anticipated audit verdict and no other reviewer's answer in either request. Neither reviewer can use tools or edit files.
- These are independently prompted real model reviews, not the author's role-play. Shared model/provider/source inputs do NOT imply statistical independence, separate factual evidence or external human review. Report requested/reported model and this limit.

## Frozen request and bounded execution

Initial round: exactly two allowed requests. If a revised design is written in response to substantiated blockers, allow one focused second round with exactly two new frozen requests to the same two reviewer roles; fresh contexts see the revised design, authoritative sources and original findings, not each other's follow-up verdicts. Maximum four successful or attempted requests across this task, no automatic retries or model substitution.

Per request: HTTPS CPA `/v1/chat/completions`, TLS validation, no redirects carrying credentials, temperature 0, max_tokens 4500, request byte limit 196608, transport timeout 90 seconds. At most two concurrent requests. Actual monetary cost unknown unless returned under a verified currency contract. Record prompt/completion tokens, request elapsed time and provider-reported model. Do not record headers, secrets, hidden reasoning or raw error bodies.

Freeze design/acceptance/source-packet and exact request bodies/hashes before acquiring a credential. Save an immutable intent before sending and outcome after return. Completed reviews are read back, not resubmitted; an unresolved prior intent halts for reconciliation. Denial by platform security ends the attempt; no alternative credential route.

Temporary credential uses the already authorized isolated AgentDock Skill environment for the review command only, then env_unset and env_list verification. No Jev official key is needed. Original private note and secret values stay outside Git, issue and review packet.

## Required output

Return Chinese report with: Verdict PASS/REVISE/BLOCK; up to six concrete findings, each severity (P0/P1/P2), exact design section/source, a falsifiable counterexample, minimal repair and what would validate it; separate implementation admission for offline coding vs paid trial vs production. Do not ask for private reasoning or write an alternative giant framework. No numeric rating in place of findings. Unsupported alleged defects must be labeled uncertain.

## Disposition

The author verifies findings against the frozen sources; no majority vote. Record accept/reject/defer with reasons and revision location. Original review text and v0.1 remain immutable. P0/P1 unresolved means the affected implementation or test stage is not admitted. Final task completion is distinct from design acceptance and future semantic qualification.

This audit tests design coherence, not whether Jev solves the two examples. The actual implementation and end-to-end comparison require their own source/request freeze, offline controls and explicit readout of all costs/fallbacks.
