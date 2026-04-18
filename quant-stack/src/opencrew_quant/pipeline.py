from __future__ import annotations

WORKFLOW_STAGE_ORDER = [
    "research",
    "decision",
    "build",
    "validate",
    "ops_review",
    "rollout",
    "observe",
    "knowledge",
]

DELIVERY_STAGE_ORDER = ["backtest", "replay", "paper", "ops_review", "live"]


def describe_workflow_stage_gates() -> dict[str, list[str]]:
    return {
        "research": ["benchmark_ref", "evidence_ref", "confidence"],
        "decision": ["decision_ref", "risk_budget", "abort_condition"],
        "build": ["decision_ref", "execution_packet_ref", "rollback_ref"],
        "validate": ["validation_plan_ref", "validation_report_ref", "risk-assertions-pass"],
        "ops_review": ["review_ref", "kill-switch-verified", "rollback-drill-pass"],
        "rollout": ["rollout_ref", "owner-assigned", "observation-window-defined"],
        "observe": ["observe_ref", "reconcile-gap-ok", "alert-pipeline-ok"],
        "knowledge": ["knowledge_ref", "scar-or-pattern-captured"],
    }


def describe_delivery_stage_gates() -> dict[str, list[str]]:
    return {
        "backtest": ["cost-modeled", "baseline-compare", "drawdown-within-budget"],
        "replay": ["market-data-replay-available", "signal-consistency", "risk-assertions-pass"],
        "paper": ["order-failure-rate-ok", "reconcile-gap-ok", "alert-pipeline-ok"],
        "ops_review": ["decision_ref", "validation_report_ref", "rollback_ref"],
        "live": ["ops-approved", "kill-switch-verified", "observation-window-defined"],
    }
