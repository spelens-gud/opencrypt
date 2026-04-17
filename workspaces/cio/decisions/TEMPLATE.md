# Decision Log: DEC-YYYY-MM-DD-XXX

- decision_id: DEC-YYYY-MM-DD-XXX
- related_change_id: (optional, from `ops/live-change-review.md`)
- related_incident_id: (optional, from `ops/incident-template.md`)
- timestamp:
- regime_before:
- regime_after:
- action: open | close | rebalance | reduce_only | hold
- strategy_mix_before:
- strategy_mix_after:
- risk_budget_before:
- risk_budget_after:
- reason:
- expected_scenario:
- abort_condition:
- reviewer: CIO
- ops_required: yes/no
- confidence_score: (0-100)
- execution_plan_ref: (from CTO task/closeout)

## Evidence
- key_metrics:
- threshold_hit:
- event_context:
- benchmark_alignment: (Freqtrade/Hummingbot/LEAN 哪类能力被采用或借鉴)

## Outcome Review (T+1 / T+7)
- pnl_24h:
- pnl_7d:
- slippage_vs_expected:
- deviations:
- lessons:

## Compliance Check
- L3_confirmation_needed: yes/no
- L3_confirmation_ref: (ticket/message link or note)
- ops_review_ref: (if ops_required=yes)
- reviewer_ref: (message/thread/ticket link)
- rollback_ref: (required if action != hold)
