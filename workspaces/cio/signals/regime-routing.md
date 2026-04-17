# Regime Routing v1 (Balanced Futures)

## Regime Definitions
- R1 TREND_UP
- R2 TREND_DOWN
- R3 RANGE
- R4 HIGH_VOL_EVENT
- R5 LIQUIDITY_STRESS

## Unified Inputs
- vol_percentile_30d
- adx_4h
- basis_zscore
- funding_rate_zscore
- depth_drop_pct_1h
- spread_widen_pct_1h

## Data Freshness Gate
- market_data_freshness_s <= 5
- account_data_freshness_s <= 10
- 任一关键数据超时时：禁止切换到高风险策略，默认降级为 `R5 -> risk_off_reduce_only`

## Regime Rules (default thresholds)
- R4 HIGH_VOL_EVENT if vol_percentile_30d >= 80
- R5 LIQUIDITY_STRESS if depth_drop_pct_1h <= -35% OR spread_widen_pct_1h >= 60%
- R1 TREND_UP if adx_4h >= 25 AND price_above_ma200_4h = true
- R2 TREND_DOWN if adx_4h >= 25 AND price_above_ma200_4h = false
- otherwise R3 RANGE

## Confidence Score
- score_range: [0, 100]
- 计算建议：
  - trend_strength_score: clamp((adx_4h - 18) * 3, 0, 30)
  - volatility_penalty: clamp((vol_percentile_30d - 60) * 1.2, 0, 20)
  - liquidity_penalty: clamp(abs(min(depth_drop_pct_1h, 0)) * 0.3 + max(spread_widen_pct_1h, 0) * 0.2, 0, 30)
  - confidence = 70 + trend_strength_score - volatility_penalty - liquidity_penalty
- 路由约束：
  - confidence < 45: 仅允许 `risk_off_reduce_only` 与低杠杆防御策略
  - 45 <= confidence < 60: 禁止高换手策略
  - confidence >= 60: 按正常矩阵执行

## Routing Matrix
- R1:
  - primary: [trend_follow, breakout]
  - secondary: [carry]
  - disabled: [mean_reversion_fast]
- R2:
  - primary: [trend_follow_short, breakdown]
  - secondary: [carry]
  - disabled: [mean_reversion_fast]
- R3:
  - primary: [mean_reversion, basis_neutral]
  - secondary: [low_freq_carry]
  - disabled: [breakout]
- R4:
  - primary: [event_defensive, low_leverage_momentum]
  - secondary: []
  - disabled: [short_vol, high_turnover_mr]
- R5:
  - primary: [risk_off_reduce_only]
  - secondary: []
  - disabled: [all_non_whitelist]

## Switch Controls
- confirm_bars: 3
- cooldown_hours: 6
- max_switch_per_day: 3
- emergency_override:
  - R4/R5 可跳过 confirm_bars 直接生效
  - 连续触发 R4/R5 达 2 次后，强制 12h 冷却且保持防御配置

## Risk Coupling
- leverage_cap:
  - R1: 1.2x
  - R2: 1.2x
  - R3: 0.9x
  - R4: 0.6x
  - R5: 0.3x
- per_trade_risk_cap:
  - R1: 0.45% NAV
  - R2: 0.45% NAV
  - R3: 0.35% NAV
  - R4: 0.25% NAV
  - R5: 0.10% NAV
- portfolio_daily_loss_cap: 1.8% NAV
- weekly_drawdown_cap: 4.5% NAV

## Platform Mapping (Implementation Hint)
- strategy_backtest_runtime: Freqtrade style research/backtest
- execution_connector: ccxt + native websocket
- optional_mm_extension: Hummingbot connector capability
