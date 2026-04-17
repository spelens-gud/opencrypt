# Decision Log: DEC-2026-04-17-001

- decision_id: DEC-2026-04-17-001
- timestamp: 2026-04-17T10:00:00+08:00
- regime_before: R3
- regime_after: R1
- action: rebalance
- strategy_mix_before: {mean_reversion: 70%, trend_follow: 30%}
- strategy_mix_after: {trend_follow: 70%, breakout: 20%, carry: 10%}
- risk_budget_before: {gross_leverage_cap: 0.9x}
- risk_budget_after: {gross_leverage_cap: 1.2x}
- reason: adx_4h 连续 3 根 >25 且价格站上 MA200
- expected_scenario: 趋势延续 2-5 天
- abort_condition: adx_4h 回落到 <18 且收盘跌回 MA200 下方
- reviewer: CIO
- ops_required: no
- ops_review_ref: n/a

## Outcome Review
- pnl_24h: to_fill
- pnl_7d: to_fill
- slippage_vs_expected: to_fill
- deviations: to_fill
- lessons: to_fill
