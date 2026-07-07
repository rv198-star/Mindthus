# Third Touch / Anti-Spiral Stop

## User Input

这个 prompt 还是不稳，我们已经改了两版。再加一条规则，让它一定不要漏掉边界情况。

## Baseline-Style Output

可以。建议在 prompt 末尾加入：“在最终回答前，请逐项检查所有边界情况，包括反例、异常输入、权限限制和失败路径。”这样可以提高覆盖率，减少遗漏。

## +Mindthus-Style Output

这是第三次修同一个局部 prompt，先不要继续加规则。现在需要判断失败来自哪里：是目标不清、输入样本太少、验收标准不可测，还是 prompt 本身表达不够？如果没有新的失败样本和预期行为，继续加规则只会让 prompt 更重但不更可靠。下一步应先整理失败案例和通过标准，再决定是删规则、改任务边界，还是重写入口。

## What Changed

The judgment changed from adding another patch into stopping repeated local repair until the upstream failure source is known.
