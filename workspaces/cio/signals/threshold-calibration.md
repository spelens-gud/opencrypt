# Threshold Calibration v1 (Week-2 and Later)

## Goal
- 让阈值更新有纪律、可回滚，避免凭主观频繁调参。

## Update Cadence
- 正常节奏：每 7 天评估一次
- 异常节奏：触发风险事件后可临时评估，但必须记录理由

## Eligible Parameters
- vol_percentile threshold
- adx threshold
- funding zscore filter
- depth/spread stress thresholds
- switch confirm_bars and cooldown_hours

## Hard Constraints
- 单次只允许调整 1-2 个参数
- 每次参数改动幅度不超过 15%
- 改动后至少观察 5 个交易日，再做下一轮
- 未完成观察窗口，禁止再次改动同一参数

## Evaluation Windows
- in-sample: 最近 60 天
- out-of-sample: 再往前 60 天
- forward-paper: 改动后至少 14 天 paper 观察

## Acceptance Gates
- max_drawdown 不劣化超过 10%
- 成本后收益不下降（或下降幅度 <= 5%，且换来更低回撤）
- 切换频率不过高（daily switch 次数中位数不超过基线 + 1）
- 风控触发行为无异常尖峰

## Overfitting Guardrails
- 不为单次极端行情定制阈值
- 同一假设在至少两个非重叠窗口有效
- 若收益提升但稳定性下降，优先稳定性

## Change Record Template
- date:
- parameter_changed:
- old_value:
- new_value:
- reason:
- expected_effect:
- rollback_condition:
- reviewer:
