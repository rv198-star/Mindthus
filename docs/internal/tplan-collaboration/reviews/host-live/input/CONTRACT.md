# Bounded host acceptance artifact / contract host-normalizer-v1

Implement `normalize_record(value)` using only the Python standard library.
- Accept a dict with exactly id, label, enabled, weight. Reject missing/extra keys and non-dict input with ValueError.
- id and label: strings whose stripped content is nonempty. Preserve the original strings in the output.
- enabled: exact bool, including False. Reject numbers and strings in this field.
- weight: exact int in [0, 100], including 0; reject bool, float, strings, negative and >100.
- Return a fresh dict in the field order id, label, enabled, weight. Preserve all values; do not mutate the input.
- Each invalid input raises ValueError. No I/O, network, packages or TPlan dependencies.

Round 1 is an explicitly fault-injected canary: B packages the provided legacy source unchanged with a smoke test and a clear canary label. C independently judges the artifact against this full contract and reports reproducible findings. Round 2 is B's autonomous complete repair against the full contract, followed by a new independent C review.
The canary is an experimental artifact; it is not a proposed change to the Mindthus product.
