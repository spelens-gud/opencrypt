# Decision Log: DEC-YYYY-MM-DD-XXX

- decision_id: DEC-YYYY-MM-DD-XXX
- strategy_lane: directional_alpha | basis_carry | microstructure_mm | signal_relay | grid_dca
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
- external_system_refs:
- lane_rationale: (为什么这个任务属于该 lane，而不是其他 lane)

## Lane-Specific Requirements

### directional_alpha
- alpha_hypothesis:
- invalidation_signal:
- max_concurrent_positions:

### basis_carry
- hedge_definition:
- leg_mismatch_tolerance:
- borrow_or_funding_assumption:

### microstructure_mm
- quoting_style:
- inventory_cap:
- stale_quote_abort_condition:

### signal_relay
- signal_source:
- idempotency_rule:
- reduce_only_rule:

### grid_dca
- bot_template:
- capital_sleeve_limit:
- stop_new_entries_condition:

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
