# ROLLBACK RUNBOOK TEMPLATE

## Meta
- change_id:
- strategy_lane:
- decision_ref:
- review_ref:
- owner:

## Trigger Conditions
- risk_limit_breach:
- reconcile_gap:
- abnormal_order_reject_rate:
- manual_abort:

## Rollback Steps
1. freeze new orders
2. set reduce-only if needed
3. cancel outstanding orders
4. restore previous config
5. verify positions and risk snapshot
6. post incident / review note

## Verification
- orders_frozen_ok:
- previous_config_restored:
- risk_snapshot_normal:
- incident_ref:

## Closeout
- completed_at:
- operator:
- followups:
