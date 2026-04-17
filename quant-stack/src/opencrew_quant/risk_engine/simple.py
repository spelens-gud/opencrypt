from __future__ import annotations

from ..domain.models import RiskLimits
from ..execution_gateway.interfaces import OrderIntent


class PaperRiskEngine:
    def __init__(self, risk_limits: RiskLimits, current_daily_loss_bps: int = 0) -> None:
        self._risk_limits = risk_limits
        self._current_daily_loss_bps = current_daily_loss_bps

    def approve(self, intent: OrderIntent, min_notional_usd: float | None = None) -> tuple[bool, str]:
        if not self._risk_limits.kill_switch_enabled:
            return False, "kill-switch-disabled"
        if intent.notional_usd <= 0 or intent.quantity <= 0:
            return False, "non-positive-order"
        if min_notional_usd is not None and intent.notional_usd < min_notional_usd:
            return False, "min-notional-breach"
        if self._current_daily_loss_bps >= self._risk_limits.daily_loss_limit_bps:
            return False, "daily-loss-limit-breached"
        return True, "approved"
