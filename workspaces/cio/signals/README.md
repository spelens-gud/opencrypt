# signals（逻辑变更信号）

定义哪些变化会触发“需要复盘/需要提醒”。

## Futures 量化默认模板（v1）

- `regime-routing.md`：行情状态识别 + 策略路由 + 风险联动
- `signal-trend-follow.md`：趋势策略信号规范
- `signal-mean-reversion.md`：均值回归信号规范
- `threshold-calibration.md`：第二周开始的阈值校准规则（防拍脑袋）
- `weekly-review-template.md`：每周 Regime 与阈值评审模板
- `metric-dictionary.md`：指标口径字典（统一计算定义）

## 维护原则

- 先定义 Regime，再定义策略，不反过来
- 所有阈值变更必须记录原因、观察窗口、回滚条件
- 任何实盘参数调整（杠杆/止损/风控开关）都需走 Ops 审核
