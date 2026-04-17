from __future__ import annotations

from ..domain.models import RiskLimits
from .interfaces import TargetAllocation


class FixedRiskPortfolioEngine:
    def __init__(self, risk_limits: RiskLimits) -> None:
        self._risk_limits = risk_limits

    def build_target(self, symbol: str, decision_weight: float, nav_usd: float) -> TargetAllocation:
        capped_weight = min(max(decision_weight, 0.0), self._risk_limits.max_gross_leverage)
        return TargetAllocation(
            symbol=symbol,
            target_notional_usd=round(nav_usd * capped_weight, 2),
            max_leverage=self._risk_limits.max_gross_leverage,
        )
