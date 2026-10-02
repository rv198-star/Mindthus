# RC01 preparation — 2026-10-03

Owner明确要求先推送当前版本作为RC01，再考虑进一步取舍。本轮发布`v1.11.0-rc.1` prerelease，沿用当前候选分支，不合并main、不改本机已安装Skill、不继续精简、不追加模型调用。

- 被测方法：`7fcaad8028bcf37156b9aea30e07f72d90bbb20d`。
- 完整测评：`d9171c7c871f323276651cd6dc018dbf4ac30ac3`。
- `skills/`、`docs/methodologies/`、`scripts/primitives/`相对被测方法没有差异。
- 发行改动：builder/logger版本号、README/CHANGELOG/RC说明、版本断言；TPlan runtime generation保持1.5.4。
- 16项针对性版本/打包/安装诊断检查通过。保留最初系统Python选错的日志；固定PATH后暴露两项旧诊断夹具依赖已删除的词面marker，现同步到既有的四个稳定身份/合同marker。缺marker、hash不符、缺文件仍失败，未改诊断运行逻辑或放宽检查。
- 不重复全仓审计及真实测评；没有新模型请求。
- 仅提供plugins/skills RC归档、源码身份说明和校验和。此RC不是Stable发行，不追加尚未适配验证的ROI Beta RC；正式Stable同步ROI Beta默认规则和既有资产保持。
- 公开发布后核对远端tag剥离提交、prerelease/latest标记及下载归档摘要，再追加发布验证记录；不移动RC01 tag。
