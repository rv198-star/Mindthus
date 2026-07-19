# Current plan

On timeout, retry once and then place the payload in the fallback queue. The plan has no
schema contract, producer-side validation, or evidence about the remaining failure path.
