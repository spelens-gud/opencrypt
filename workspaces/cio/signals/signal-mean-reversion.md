# Signal Spec: mean_reversion

## Thesis
- hypothesis: 在震荡区间，偏离均值后回归概率更高
- market_regime_fit: [R3]

## Universe
- exchange: <your-main-exchange>
- symbols: [BTCUSDT-PERP, ETHUSDT-PERP]
- contract_type: perpetual only

## Entry / Exit
- entry_rule: zscore(price-vwap_1d) >= +2.0 做空，<= -2.0 做多
- exit_rule: zscore 回到 |0.5| 内
- invalid_condition: adx_4h >= 25（转趋势）

## Filters
- liquidity_filter: depth >= median * 0.8
- spread_filter: spread <= median * 1.3
- funding_filter: |funding_rate_zscore| <= 1.5
- event_filter: 高波事件窗口禁用

## Risk
- max_leverage: 0.9x
- position_sizing_rule: equal-risk bucket
- per_trade_risk_cap: 0.35% NAV
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
