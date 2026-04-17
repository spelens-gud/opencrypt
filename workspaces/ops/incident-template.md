# Incident Report Template (Futures)

## 1) Incident Meta
- incident_id:
- related_decision_id: (optional, from `cio/decisions`)
- related_change_id: (optional, from `live-change-review.md`)
- severity: sev1 | sev2 | sev3
- detected_at:
- detected_by:
- status: open | mitigated | closed

## 2) Impact
- impacted_scope: strategy | execution | risk-control | infra
- affected_symbols:
- estimated_pnl_impact:
- user_impact:

## 3) Timeline
- t0 (first signal):
- t1 (confirmed):
- t2 (mitigation started):
- t3 (stabilized):
- t4 (closed):

## 4) Symptoms and Root Cause
- symptoms:
- immediate_trigger:
- root_cause:
- contributing_factors:

## 5) Mitigation
- actions_taken:
- kill_switch_used: yes/no
- reduce_only_enabled: yes/no
- rollback_executed: yes/no
- verification_after_mitigation:

## 6) Recovery and Follow-ups
- permanent_fix_items:
- owners:
- due_dates:
- validation_plan:

## 7) Knowledge Upgrade
- promote_to_pattern: yes/no
- promote_to_scar: yes/no
- ko_inbox_ref:

## 8) Approvals
- incident_commander:
- ops_reviewer:
- closed_at:
- review_ref: (message/thread/ticket link)
