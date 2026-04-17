# HEARTBEAT — KO

> 建议每天 2 次即可（配合 openclaw.json 的 heartbeat.every="12h"）。
> 如果没有需要做的事，回复 `HEARTBEAT_OK`。

## 检查项
- [ ] #know 是否有未处理的 closeout？
- [ ] inbox/ 是否有积压？
- [ ] 本周是否需要升级 1–2 条 knowledge（principle/pattern/scar）？
- [ ] 本周新增知识是否都带来源引用（decision/review/incident）？
- [ ] 是否有重复亏损样本未升级为 scar？

## 升级触发器
- signal=3 或 sev1/sev2 事件：优先产出 scar 并通知 CoS/Ops。
- 无来源引用的总结：禁止入库，仅保留在 inbox 待补证据。

## 输出格式
- `status`: ok | action_required
- `actions`: 下一步动作（最多 3 条）
- `refs`: knowledge_ref / decision_ref / incident_ref
