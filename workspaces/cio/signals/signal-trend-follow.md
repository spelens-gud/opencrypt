# Signal Spec: trend_follow

## Thesis
- hypothesis: 在趋势清晰阶段，顺势持仓优于频繁反转交易
- market_regime_fit: [R1, R2]

## Universe
- exchange: <your-main-exchange>
- symbols: [BTCUSDT-PERP, ETHUSDT-PERP]
- contract_type: perpetual only

## Entry / Exit
- entry_rule: 4h 级别 MA50 上穿 MA200 且 ADX>=25（做多）；反向做空
- exit_rule: MA50 与 MA200 反向交叉 OR trailing stop hit
- invalid_condition: adx_4h < 18 持续 3 根 4h bar

## Filters
- liquidity_filter: top-of-book depth >= 30-day median * 0.7
- spread_filter: spread <= 30-day median * 1.5
- funding_filter: |funding_rate_zscore| <= 2.0
- event_filter: 重大宏观事件前后 30 分钟禁止新开仓

## Risk
- max_leverage: 1.2x
- position_sizing_rule: volatility-targeted, target daily vol = 0.9%
- per_trade_risk_cap: 0.45% NAV
- daily_loss_cap_link: global 1.8% NAV

## Validation Snapshot
- backtest_window: rolling 18 months
- net_pnl: to_fill
- max_drawdown: to_fill
- sharpe_or_sortino: to_fill
- turnover: to_fill
- fee_slippage_assumption: taker 4bps + slippage 2bps per side

## Ops
- owner: CIO
- last_reviewed_at: 2026-04-17
- status: active
