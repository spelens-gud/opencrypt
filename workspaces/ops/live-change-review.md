# Live Change Review Checklist (Futures)

## A. Change Meta
- change_id:
- strategy_lane:
- related_decision_id: (from `cio/decisions`)
- related_incident_id: (optional)
- scope:
- risk_level: medium
- rollback_plan_present: yes
- kill_switch_verified: yes

## B. Backtest Gate (minimum)
- cost_included: yes
- max_drawdown_within_budget: yes (<= 4.5% weekly budget equivalent test)
- performance_stable_cross_periods: yes (至少 3 个非重叠窗口)
- baseline_compare_present: yes (相对当前生产参数)

## C. Paper Gate (minimum)
- paper_days_completed: >= 14
- order_failure_rate_ok: < 0.5%
- alert_pipeline_ok: yes
- execution_latency_p95_ok: < 800ms
- reconcile_gap_ok: < 0.1% NAV

## D. Security Gate
- api_permission_minimal: yes
- live/sim isolation: yes
- secret_rotation_checked: yes

## E. Verdict
- result:
- notes:
- approver:
- timestamp:
- review_ref: (message/thread/ticket link)

## F. Mandatory Attachments
- decision_ref: (required)
- validation_report_ref: (required)
- rollback_ref: (required)

## G. Lane-Specific Gate
- `directional_alpha`: lookahead_bias_checked / baseline_compare_present / parameter_freeze_window_defined
- `basis_carry`: hedge_mismatch_alarm_ok / borrow-funding-modeled / transfer_or_margin_failover_defined
- `microstructure_mm`: orderbook_replay_pass / stale_quote_kill_ok / orphan_order_reconcile_ok
- `signal_relay`: signal_auth_ok / idempotency_ok / stale_signal_reject_ok
- `grid_dca`: sleeve_limit_ok / ladder_healthcheck_ok / trapped_inventory_reviewed
