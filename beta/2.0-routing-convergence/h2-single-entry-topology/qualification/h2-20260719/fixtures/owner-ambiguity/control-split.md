# Deploy Approval Control Split

The LLM reviews semantic change risk and recommends `APPROVE`, `HOLD`, or `ESCALATE`.
The deterministic workflow owns production authority and blocks release when mandatory
evidence is absent. Candidate-bound test, security, rollout, and rollback evidence gates
the decision. The document is intentionally concise but already usable.
