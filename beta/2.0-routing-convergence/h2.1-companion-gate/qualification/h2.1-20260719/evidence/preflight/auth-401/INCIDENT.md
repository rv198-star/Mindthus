# Zero-sampling Authentication Incident

The first empty `CODEX_HOME` had the candidate plugin but no Codex authentication
material. The Responses API returned HTTP 401 before authenticated sampling.

Evidence properties:

- `thread.started` and `turn.failed` exist;
- no agent output exists;
- no `turn.completed` event exists;
- no usage exists;
- no candidate command or Skill read executed.

Classification: infrastructure preflight event, `0 Generator / 0 counted tokens`.

Resolution: create a new isolated home and copy only the existing Codex `auth.json`
with mode 0600 before installing the same frozen candidate. The failed thread/home was
not resumed or reused. No candidate, prompt, fixture, or acceptance rule changed.
