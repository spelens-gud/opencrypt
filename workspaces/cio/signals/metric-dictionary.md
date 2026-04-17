# Metric Dictionary (Futures v1)

## 目的
- 统一指标定义与计算口径，避免不同角色/脚本出现解释偏差。

## Regime 相关指标

- `vol_percentile_30d`
  - 定义：当前实现波动率在过去 30 天分布中的分位值
  - 口径：使用同一频率（建议 1h）计算滚动波动率
- `adx_4h`
  - 定义：4h 周期 ADX 趋势强度指标
  - 用途：判断趋势 vs 震荡
- `price_above_ma200_4h`
  - 定义：4h 收盘价是否高于 4h MA200
  - 用途：判定趋势方向

## 衍生品微结构指标

- `basis_zscore`
  - 定义：永续/现货基差相对历史均值的标准分
  - 用途：识别异常溢价/贴水
- `funding_rate_zscore`
  - 定义：资金费率相对历史均值的标准分
  - 用途：过滤拥挤交易风险
- `depth_drop_pct_1h`
  - 定义：1 小时内盘口深度变化百分比
  - 计算：`(depth_now - depth_1h_ago) / depth_1h_ago`
- `spread_widen_pct_1h`
  - 定义：1 小时内买卖价差扩大量
  - 计算：`(spread_now - spread_1h_ago) / spread_1h_ago`

## 交易与风险指标

- `order_failure_rate`
  - 定义：失败订单数 / 订单总数（观察窗口内）
- `execution_latency_ms`
  - 定义：从下单请求到确认回执的延迟
- `slippage_vs_expected`
  - 定义：实际成交价格与预估成交价格偏差
- `portfolio_daily_loss_cap`
  - 定义：组合日内允许最大损失阈值（NAV 百分比）
- `weekly_drawdown_cap`
  - 定义：周度允许最大回撤阈值（NAV 百分比）

## 统计与对齐要求

- 同一指标在所有报表中使用同一时间窗口与采样频率。
- 指标变更必须在 `threshold-calibration.md` 中记录。
- 任何新指标进入实盘决策前，先进入至少 14 天 paper 观察。
