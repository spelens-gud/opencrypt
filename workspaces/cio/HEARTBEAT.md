# HEARTBEAT — CIO

> 建议频率：每天 2 次（开盘前 / 收盘后）。
> 如果没有需要做的事，回复 `HEARTBEAT_OK`。

## 检查项
- [ ] 重点持仓是否有重大新闻？
- [ ] 是否有逻辑变更信号？
- [ ] 今日是否已产出 `decision_ref`（含 regime/strategy/risk）？
- [ ] 是否存在需要升级为 `ops_required=yes` 的异常偏差？

## 升级触发器
- 命中 R4/R5 或连续异常偏差（滑点/失败率/回撤）时，立即通知 CoS 并触发 Ops 审核链路。
- 缺少关键证据（signals 指标或阈值命中）时，不推进新策略动作。

## 输出格式
- `status`: ok | action_required
- `actions`: 下一步动作（最多 3 条）
- `refs`: decision_ref / review_ref（如有）
