# 首阶段真实调用前复核

证据评审在已知协议与实现的上下文中只读复核；不是盲审或人类真值。

- 要求绑定真正执行/计分的 contract 和 cases：run 现重新读取冻结输入，逐对象相等校验后才允许任何请求。测试覆盖标签被篡改时零请求拒绝。
- 要求恢复输入 token 定价上界检查：已恢复 64000 上界；即使 actual cost=null 也立即停止后续请求。专门的注入测试通过。
- 要求分开 raw action 与交接候选：逐行记录 raw_action、仅 route=rewrite_candidate 时非空的 rewrite_handoff_action，且 consumption=not_executed。
- 已确认：完整联合答案匹配、N01预先排除、N10 support免计、弃权单列、已知标签失败不刷题、Session未知调用/快照锁定/累计门限保留。

首阶段运行器只强制首阶段23次上限。协议中的额外2次生成后重检必须在进入第二阶段前单独核验累计预算和精确请求，不能把manifest声明本身当成执行保证。
