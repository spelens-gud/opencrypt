# decisions（决策日志）

用于记录每一次策略切换、调仓、risk-off、参数变更建议。

## 文件命名

- 格式：`YYYY-MM-DD-<topic>.md`
- 示例：`2026-04-20-liquidity-stress-riskoff.md`
- 新记录建议从 `TEMPLATE.md` 复制生成，确保字段一致。

## 必填字段（最小集）

- `timestamp`
- `regime_before` / `regime_after`
- `action`（open | close | rebalance | reduce_only | hold）
- `strategy_mix_before` / `strategy_mix_after`
- `risk_budget_before` / `risk_budget_after`
- `reason`
- `expected_scenario`
- `abort_condition`
- `reviewer`
- `ops_required`（yes/no）
- `ops_review_ref`（`ops_required=yes` 时必填；no 时填 `n/a`）
- `decision_id`（建议与文件标题一致）

## L3 约束（硬规则）

- 涉及实盘不可逆动作时，只记录“建议 + 用户确认结果”。
- 不允许在同一条记录里既写“建议”又执行“未确认实盘动作”。

## 复盘字段（建议 T+1 / T+7 补齐）

- `pnl_24h`
- `pnl_7d`
- `slippage_vs_expected`
- `deviations`
- `lessons`

## 质量门槛

- 每条 `reason` 必须可被数据复核（阈值、指标或事件证据）。
- 每条 `abort_condition` 必须可执行（触发后能立即动作）。
- `ops_required: yes` 的记录，必须能追溯到 Ops 审核结果。

## 跨文档关联字段（统一口径）

- `decision_id`：决策记录唯一 ID（`cio/decisions`）
- `change_id`：变更审核记录 ID（`ops/live-change-review.md`）
- `incident_id`：事故记录 ID（`ops/incident-template.md`）
- `related_*`：用于跨文档引用（如 `related_change_id`）
- `*_ref`：用于保存消息/thread/ticket 链接（如 `ops_review_ref`）
