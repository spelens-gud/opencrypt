from __future__ import annotations

STAGE_ORDER = ["backtest", "replay", "paper", "ops_review", "live"]


def describe_stage_gates() -> dict[str, list[str]]:
    return {
        "backtest": ["cost-modeled", "baseline-compare", "drawdown-within-budget"],
        "replay": ["market-data-replay-available", "signal-consistency", "risk-assertions-pass"],
        "paper": ["order-failure-rate-ok", "reconcile-gap-ok", "alert-pipeline-ok"],
        "ops_review": ["decision_ref", "validation_report_ref", "rollback_ref"],
        "live": ["ops-approved", "kill-switch-verified", "observation-window-defined"],
    }
