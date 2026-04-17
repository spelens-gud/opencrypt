# Decision Log: DEC-2026-04-20-004

- decision_id: DEC-2026-04-20-004
- timestamp: 2026-04-20T22:05:00+08:00
- regime_before: R4
- regime_after: R5
- action: reduce_only
- strategy_mix_before: {event_defensive: 70%, low_leverage_momentum: 30%}
- strategy_mix_after: {risk_off_reduce_only: 100%}
- risk_budget_before: {gross_leverage_cap: 0.6x}
- risk_budget_after: {gross_leverage_cap: 0.3x}
- reason: depth_drop_pct_1h <= -40% 且 spread_widen_pct_1h >= 70%，流动性压力显著
- expected_scenario: 先控制尾部风险，等待流动性恢复
- abort_condition: 深度与点差恢复到常态区间并持续 3 个观察窗口
- reviewer: CIO
- ops_required: yes
- ops_review_ref: to_fill

## Outcome Review
- pnl_24h: to_fill
- pnl_7d: to_fill
- slippage_vs_expected: to_fill
- deviations: to_fill
- lessons: to_fill
