# Live Change Review Checklist (Futures)

## A. Change Meta
- change_id:
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
