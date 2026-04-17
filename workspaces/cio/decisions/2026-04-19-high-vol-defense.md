# Decision Log: DEC-2026-04-19-003

- decision_id: DEC-2026-04-19-003
- timestamp: 2026-04-19T14:10:00+08:00
- regime_before: R3
- regime_after: R4
- action: rebalance
- strategy_mix_before: {mean_reversion: 65%, basis_neutral: 25%, low_freq_carry: 10%}
- strategy_mix_after: {event_defensive: 70%, low_leverage_momentum: 30%}
- risk_budget_before: {gross_leverage_cap: 0.9x}
- risk_budget_after: {gross_leverage_cap: 0.6x}
- reason: vol_percentile_30d 升至 86，且事件窗口内点差波动明显扩大
- expected_scenario: 高波动阶段以防守优先，降低回撤
- abort_condition: vol_percentile_30d 回落 <70 且点差恢复常态
- reviewer: CIO
- ops_required: no
- ops_review_ref: n/a

## Outcome Review
- pnl_24h: to_fill
- pnl_7d: to_fill
- slippage_vs_expected: to_fill
- deviations: to_fill
- lessons: to_fill
