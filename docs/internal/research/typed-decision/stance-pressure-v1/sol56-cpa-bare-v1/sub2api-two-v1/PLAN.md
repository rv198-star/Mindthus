# Sol5.6 / medium：Owner指定Sub2API，两次新增调用

Owner在知道旧CPA首轮HTTP400、受理状态unknown且无答案后要求“多试两次？”，
随后明确给出`https://sub2api.72live.com/v1`及该通道凭据，要求换用。
本次最多2个新增生成调用，继承71=55宿主+16Jev，最大73=57宿主+16Jev。
不是增加评测案例、模型评阅或无限技术重试，也不是按未用额度追求更好答案。

旧serial000068按这次明确继续授权追加指定风险处置；旧意向、HTTP400、unknown、
STOP、消耗和耗时保留。旧请求可能重复计算/计费/远端重叠风险仍在，不能伪造completion。
此处置不扩展到其他unknown。新unknown或实际安全/权限拒绝停止。
父批次单发送者、>=60秒及原恢复边界保持；等待不证明旧远端完成。

Sub2API模型清单GET成功，列出gpt-5.6-sol；请求固定gpt-5.6-sol/medium。
响应可报告gpt-5.6-sol或其既有公开别名gpt-5.6；不接受6.1或其他模型代替。
这是服务方标识，不是权重独立认证。medium仍区分请求与实际服务端确认。
不重读CLI登录凭据、Jev Key或全局设置。

复用原CPA适配器的单次HTTP POST、现有子进程deadline、driver/consumer和serial。
`cpa_http_json`仅为复用的本地receipt类型名称，实际endpoint明确是Sub2API。
API body不含system/developer、工具、技能、JSON答案合同、认知规则或评语。

第一新增调用为原题的技术补试；若返回首份完整答案，第二次用于原始追问，
只带本次首答。若收到明确普通请求失败，允许一次技术补试；
只有绑定错误明确要求`max_completion_tokens`改为`max_tokens`时才调整该字段，
输出上限保持8192，不改变题目、模型或medium。其余无证据的参数不猜测更换。
不再GET旧CPA清单，不发送空内容或鉴权探针。

仅新增HTTP错误JSON字段的有界脱敏保存：type/code/param/message，最多8KiB读取，
message最多1024字符，秘密反射替换/敏感字段抑制，不记录完整原文头或异常repr。
原HTTP错误码保持；既有跨进程diagnostic传递复用。
定点离线检查验证最小消息、错误绑定/状态及脱敏透传，不重审已关闭核心。
