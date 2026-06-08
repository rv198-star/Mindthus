# SELA Judge Rubric

Use this rubric after shape validation. shape validation is not semantic judgment.

Score each dimension `0-2`:

- `0`: the move is absent or materially wrong.
- `1`: the move is mentioned but thin, generic, or not action-bearing.
- `2`: the move is concretely executed and constrains the recommendation.

do not score by preferred conclusion. The judge should reward faithful SELA execution
even when the recommendation differs from the maintainer's expectation.
form compliance is not enough: a filled field can still score `0` or `1` if the judgment
did not happen.

## Dimensions

### D1 对比公平性审查

Does the output challenge unfair comparison such as `best-A vs average-B` and rebuild a
fair comparison surface?

### D2 局部优势可规模化

Does the output distinguish real local excellence from scalable advantage?

### D3 系统效率趋势

Does the output analyze whether system-level efficiency improves over time through
cost, speed, feedback, coverage, or compounding scale?

### D4 边界豁免检查

Does the output identify hard boundaries such as irreversible harm, dignity, safety,
legal/medical authority, or other cases where SELA cannot dominate?

### D5 时机动作分级

Does the output separate long-term direction from action posture, such as `commit`,
`trial`, `hold`, `wait`, `stage`, `dual_track`, `reject`, or `transfer`?

### D6 反驳题目预设

Does the output identify when the user's framing misuses SELA, overstates the trend,
or turns a direction judgment into premature action?

## Judge Notes

- Prefer concrete reasoning over method vocabulary.
- Penalize vague "combine both" answers unless they name an action posture and trigger.
- Penalize hidden hard-boundary bypass even when the trend analysis is strong.
- Keep the final score separate from outcome correctness.
