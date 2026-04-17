# TASKS — CIO

> 状态枚举：`todo | in_progress | blocked | done`
> 引用字段约定：`decision_ref`（决策文件路径）

| id | cadence | type | objective | status | next_action | decision_ref | signal |
|----|---------|------|-----------|--------|-------------|--------------|--------|
| CIO-W1-001 | daily | P | 建立 Regime 日常判定与策略路由节奏（合约） | in_progress | 每日 09:00 输出 `regime + strategy mix + risk budget` 到 decisions | workspaces/cio/decisions/2026-04-17-routing-init.md | 2 |
| CIO-W1-002 | daily | A | 完成 trend_follow / mean_reversion 两策略周内观察记录 | todo | 连续 5 天补齐 pnl_24h、slippage、deviation 字段 | workspaces/cio/decisions/2026-04-18-range-shift.md | 2 |
| CIO-W1-003 | weekly | S | 完成阈值校准第一轮评估（仅评估，不改参） | todo | 第 7 天按 `threshold-calibration.md` 产出评估结论 | n/a | 3 |
| CIO-W1-004 | weekly | A | 建立 R4/R5 风险事件应对手册 | todo | 写入风险触发后的策略禁用/减仓动作清单 | workspaces/cio/decisions/2026-04-20-liquidity-stress-riskoff.md | 2 |
| CIO-QT-005 | weekly | P | 建立双策略组合稳定性评估（trend + mr） | in_progress | 每周输出组合层收益/回撤/相关性评估并给出权重建议 | workspaces/cio/decisions/2026-04-18-range-shift.md | 2 |
| CIO-QT-006 | weekly | S | 对齐行业标杆能力映射（Freqtrade/Hummingbot/LEAN） | todo | 在决策记录里补齐 benchmark_alignment 字段并说明借鉴点 | n/a | 1 |
