# D3 same-entry live integration and original-scenario development controls

Status: pre-results protocol; execution only with committed source and freeze.json.
Owner authorizes advancing D2 through real integration and bounded testing. This campaign
uses the actual entry.run(mode='relationship-frame.v1'), D2 runtime/journals and unchanged
D1 question contract v0.3.1. No surrogate assessment runner, new question semantics, or
replay of terminal six/eight-case batches. Default Skill and main remain unchanged.

## Scope and evidence ceiling

Four episodes, six input turns: Skills original two-turn challenge; display current-use
then purchase with changed purpose; a supported simple-Skills explanation (reverse control);
and a reply-relevance control starting with proposal=null to exercise the real organizer.
Skills/display turn 2 includes the ACTUAL previous returned candidate from the same episode.
The new turn's stressed candidate is still authored, not naturally generated. Prior user
messages and actual assistant outputs are immutable context, not independent fact evidence.

These are authored DEVELOPMENT CONTROLS, with synthetic supplied observations explicitly
marked as such. They are anchored to tests/bidirectional_steelman_cases.jsonl bsc-001/002 and
the historical display case; they are not new product facts or advice, holdout, natural
failure prevalence, native default Skill use or the independent 12-episode D4 comparison.
Five turns use author-provided structural proposals to isolate integration/detection. The
reply control uses a real CPA organizer; report structure quality/failures separately.
Frozen review criteria never enter model State. A model prediction is not a truth certificate.

## Fixed calls and identity

Detector: TypeSafe official jev-1.13.0, existing choice-rounding adapter. Host correction
and organizer: CPA deepseek-v4.1-flash, temperature 0, JSON response, at most 2000/3500
output tokens respectively. No fallback to another model or channel, automatic retry,
question tuning, changed labels or regenerated results. Existing source authority applies.

Each episode's admission pins implementation digest, D1 contract/sources, D2 profile,
provider and host configurations/template hashes, exact root and input templates. The only
future input interpolation allowed is a named previous assistant slot populated from its
immutable completed summary. Episode locks and turn/revision counts persist. Initial or
recheck request is deterministically compiled from a permitted input/validated revision;
its exact allowlist and host wire body are persisted BEFORE transmission. Revisions only
rebind existing target relations and preserve all original non-target fields.

4 episodes maximum; 12 judgment requests, 6 corrections, 1 organizer across the campaign.
Per episode D2 caps stay 4 judgments, 2 corrections, 1 organizer, 7 requests and 120 seconds;
one turn at most 2 judgments/1 correction. Actual caps in each admission are tighter where
possible. Jev reserve USD0.01/request (USD0.12 aggregate), NOT provider-enforced billing.
CPA actual currency is unknown unless returned. Report tokens, missing cost, elapsed request
time including failures, preparation and fallback separately. No inference beyond this
single campaign. Fixed 45s subprocess transport deadline; timeout does not cancel server work.

## Stopping, recovery, security

Same root only. Unknown intent blocks replay and all further inference. Completed receipts
are reused, including errors. Source/config/input drift, provider/runtime mismatch, secret
reflection, malformed host payload, timeout or technical failure stops the campaign; preserve
unfinished cases explicitly. Semantic misses, abstentions or safe return-to-owner are outcomes,
not permission to adjust questions. Same-model recheck is a local regression signal only.
Credentials come from authorized private notes in isolated environment; no credentials or
headers in Git/artifacts. Inspect actual output and ledger before removing temporary env.

## Evaluation and terminal decision

Record per turn: question count; all initial/consumed answers and uncertainty; scope acceptance;
named repairs; host revised text and semantic quote proposals; recheck disposition; original
input/permissions preservation; actual calls/tokens/time/cost; any remaining task obligation.
Review revised text against the frozen criterion list, distinguishing bad diagnosis, useful
correction, uncertain correction, and returned-to-owner. Safe rejection is not task completion.
Accept supported simple mechanisms; never use mandatory disagreement or a fixed 4K/5K winner.

Engineering acceptance: frozen identities respected; all completed calls have immutable
outcomes; no unauthorized call or retry; real requests passed through the same public entry;
reentry adds zero inference. Semantic result is case-by-case author review; report failures
and unknowns, do not manufacture a pass. This batch grants NO default adoption or D4 claim.

## Official interface verification (2026-09-23)

Official docs/typesafe models and API were rechecked: pinned jev-1.13.0 at /v1/systemone,
64k total tokens and 32k State plus longest question. D1 48KiB projected bytes is a local
engineering bound, not a token count. Only live provider responses establish acceptance
of these actual requests. Published input rate is not an observed invoice; batch/split
billing remains a different measurement. Source: https://docs.typesafe.ai/models and
https://docs.typesafe.ai/patterns/fan-out .
