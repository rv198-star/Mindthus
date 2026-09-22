# Named OpenRouter recovery — pre-inference amendment

Owner's original instructions explicitly authorize OpenRouter as backup. Official native
trial stopped on a transport failure; local Python/curl TLS probes also failed. GitHub push
failed similarly. In contrast, unauthenticated OpenRouter GET /api/v1/models returned200.
This new connectivity evidence supports a separate, declared backup stage; no blind
resubmission of the native failed request and no semantic prompt/case/label revision.

Native trial remains terminal, with its failure and unknown remote processing preserved.
Exclude L01 from BOTH backup views before inference, because its source request was attempted
with unknown processing. Run only L02–L32 once per view:31pairs,29semantic+2D0. L01 remains
in the original32-case population as technically unavailable, never recoded wrong or dropped
from the study history. Any language comparison is within this backup stage only.

Both views use existing OpenRouterJevProvider, requested typesafe/jev-1.13; this is the same
logical Jev family with a potentially different resolved snapshot. Bind first observed model
AND provider in a shared immutable record at batch validation, before another node can run;
reject any subsequent change across either view. Do not transfer native behavioral qualification.

Native1attempt plus at most95calls per backup view =191, within original192calls/USD0.55.
Combined conservative reserve USD0.513408. OpenRouter listing checked2026-09-22:
https://openrouter.ai/typesafe/jev-1.13 shows USD0.042/M input, zero output;32K context.
The64000-token reserve is conservative, not a claim OpenRouter accepts64K inputs.
Budget/time per view remains at most300inference seconds. No inference retry, no further
serving fallback. Any technical/authority failure ends this recovery without another stage.

Technical carrier delta only: freeze-specified exclusions and remaining limits; mandatory
shared snapshot lock before accepting each batch. C01, engine/provider/session, criteria,
canonical/translated contracts and bilingual case file remain byte-identical. Full source
hashes bind the new carrier; original freeze remains historical at83ff3a625, not rewritten.

Report native failure separately from31matched backup pairs. Technical failures do not
provide semantic answers; incomplete pairs are not filled or cherry-picked. This stage is
still development diagnosis, not holdout/A-B-C or production admission. No cost-saving claim
without translation/review/fallback/host accounting. External Mission resumes under the
already-authorized backup scope; no new user approval is required for that original scope.
