# Decision Log: DEC-2026-04-18-002

- decision_id: DEC-2026-04-18-002
- timestamp: 2026-04-18T09:20:00+08:00
- regime_before: R1
- regime_after: R3
- action: rebalance
- strategy_mix_before: {trend_follow: 70%, breakout: 20%, carry: 10%}
- strategy_mix_after: {mean_reversion: 65%, basis_neutral: 25%, low_freq_carry: 10%}
- risk_budget_before: {gross_leverage_cap: 1.2x}
- risk_budget_after: {gross_leverage_cap: 0.9x}
- reason: adx_4h 下降至 19 且价格回到 MA200 附近，趋势延续性减弱
- expected_scenario: 震荡主导，短周期反转机会增加
- abort_condition: adx_4h 重回 >=25 且方向明确
- reviewer: CIO
- ops_required: no
- ops_review_ref: n/a

## Outcome Review
- pnl_24h: to_fill
- pnl_7d: to_fill
- slippage_vs_expected: to_fill
- deviations: to_fill
- lessons: to_fill
