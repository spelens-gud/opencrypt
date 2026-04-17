# Ops Runbook (Futures)

## 目标
- 为值班与异常处理提供统一步骤，减少主观操作差异。

## 每日巡检（建议 3 次：开盘前 / 中段 / 收盘后）

1. 检查风险暴露
   - 当前杠杆是否在 Regime 限制内
   - 当日亏损是否接近 `portfolio_daily_loss_cap`
2. 检查执行健康
   - 下单失败率
   - 平均执行延迟
   - 撤单异常率
3. 检查市场微结构
   - 点差是否异常扩大
   - 深度是否快速下降
4. 检查监控链路
   - 告警是否可达
   - 关键指标是否有断流

## 关键 SLO/SLA（默认值，可由 CIO/CTO 联合提案调整）

- `order_failure_rate < 0.5%`（5 分钟窗口）
- `execution_latency_ms p95 < 800ms`
- `market_data_freshness_s < 5s`
- `risk_snapshot_freshness_s < 10s`
- `position_reconcile_gap < 0.1% NAV`

## 异常分级

- sev1：存在失控风险（无法止损/无法执行风控），立即停机或 reduce-only
- sev2：风险可控但显著偏离（失败率/延迟异常），限制新开仓并修复
- sev3：轻微异常（短时指标偏离），记录并持续观察

## 标准应急动作

1. 触发保护
   - 优先 `reduce_only`
   - 必要时触发 kill-switch
2. 冻结变更
   - 暂停非必要参数调整与新策略发布
3. 状态广播
   - 在 Ops 渠道记录异常摘要与当前动作
4. 执行回滚
   - 若异常源于近期变更，按既定回滚方案恢复
5. 复核恢复
   - 确认失败率、延迟、风险暴露回归阈值内

## 触发器（自动进入保护）

- 5 分钟内 `order_failure_rate >= 2%`
- 5 分钟内 `execution_latency_ms p95 >= 2000ms`
- 连续 2 个窗口行情数据断流
- `position_reconcile_gap >= 0.3% NAV`

满足任一条件：
1. 立即切换 `reduce_only=true`
2. 通知 CTO 暂停策略切换与新参数发布
3. 启动 incident 记录（sev1/sev2）

## 解除保护前检查

- 风险暴露回到预算范围
- 核心告警链路恢复
- 关键指标连续 3 个观察窗口稳定
- Ops 审核通过（高风险场景需 L3 确认）

## 事故记录

- 每次 sev1/sev2 事件必须使用 `incident-template.md` 留档。
- 事件结束后 24h 内补齐根因与长期修复项。
- 若事件由既有决策/变更触发，必须回填 `related_decision_id`/`related_change_id`。
