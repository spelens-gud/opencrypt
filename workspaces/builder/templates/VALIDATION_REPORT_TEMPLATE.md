# VALIDATION REPORT TEMPLATE

## Meta
- task_id:
- decision_ref:
- strategy_name:
- environment: backtest | replay | paper

## Config Snapshot
- strategy_config_ref:
- execution_config_ref:
- risk_config_ref:

## Results
- pnl:
- sharpe_or_alt_metric:
- max_drawdown:
- win_rate:
- slippage:
- failure_rate:

## Risk Assertions
- leverage_cap_ok:
- position_limit_ok:
- daily_loss_cap_ok:
- kill_switch_tested:

## Exceptions
- abnormal_samples:
- known_gaps:

## Recommendation
- ready_for_next_stage: yes/no
- next_stage: replay | paper | ops-review
- notes:
