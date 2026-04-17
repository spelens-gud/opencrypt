from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .domain.models import RiskLimits, StrategyConfig, VenueConfig


@dataclass(slots=True)
class StackConfig:
    environment: str
    venue: str
    strategy: str
    risk_profile: str
    data_latency_budget_ms: int
    decision_ref_required: bool
    review_ref_required: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "environment": self.environment,
            "venue": self.venue,
            "strategy": self.strategy,
            "risk_profile": self.risk_profile,
            "data_latency_budget_ms": self.data_latency_budget_ms,
            "decision_ref_required": self.decision_ref_required,
            "review_ref_required": self.review_ref_required,
        }


def load_stack_config(path: str | Path) -> StackConfig:
    config_path = Path(path)
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    return StackConfig(
        environment=raw["environment"],
        venue=raw["venue"],
        strategy=raw["strategy"],
        risk_profile=raw["risk_profile"],
        data_latency_budget_ms=int(raw["data_latency_budget_ms"]),
        decision_ref_required=bool(raw["decision_ref_required"]),
        review_ref_required=bool(raw["review_ref_required"]),
    )


def _load_json(path: str | Path) -> dict[str, object]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_strategy_config(path: str | Path, venue: str) -> StrategyConfig:
    raw = _load_json(path)
    return StrategyConfig(
        name=str(raw["strategy_name"]),
        venue=venue,
        symbols=tuple(raw["symbols"]),
        regime_scope=tuple(raw["regime_scope"]),
    )


def load_risk_limits(path: str | Path) -> RiskLimits:
    raw = _load_json(path)
    return RiskLimits(
        max_gross_leverage=float(raw["max_gross_leverage"]),
        per_trade_risk_bps=int(raw["per_trade_risk_bps"]),
        daily_loss_limit_bps=int(raw["daily_loss_limit_bps"]),
        kill_switch_enabled=bool(raw["kill_switch_enabled"]),
    )


def load_venue_config(path: str | Path) -> VenueConfig:
    raw = _load_json(path)
    return VenueConfig(
        name=str(raw["venue"]),
        execution_mode=str(raw["execution_mode"]),
        account_type=str(raw["account_type"]),
        reconcile_interval_s=int(raw["reconcile_interval_s"]),
        max_order_retry=int(raw["max_order_retry"]),
        proxy_url=str(raw["proxy_url"]) if raw.get("proxy_url") else None,
    )
