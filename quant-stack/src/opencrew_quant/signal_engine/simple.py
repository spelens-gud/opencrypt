from __future__ import annotations

from ..domain.models import StrategyConfig
from ..market_data.interfaces import MarketDataSnapshot
from .interfaces import SignalDecision


def generate_signal(strategy: StrategyConfig, snapshot: MarketDataSnapshot) -> SignalDecision:
    move_ratio = (snapshot.mid_price - snapshot.reference_price) / snapshot.reference_price
    funding_rate = snapshot.funding_rate or 0.0

    if strategy.name == "trend_follow":
        target_weight = 0.3 if move_ratio > 0 else 0.0
        regime = strategy.regime_scope[0]
        confidence = min(0.95, 0.55 + abs(move_ratio) * 8)
    elif strategy.name == "market_making":
        target_weight = 0.0
        regime = strategy.regime_scope[min(1, len(strategy.regime_scope) - 1)]
        confidence = min(0.95, 0.6 + abs(move_ratio) * 3)
    elif strategy.name == "basis_carry":
        if move_ratio > 0.01 and funding_rate > 0:
            target_weight = -0.18
        elif move_ratio < -0.005:
            target_weight = 0.18
        else:
            target_weight = 0.0
        regime = strategy.regime_scope[min(1, len(strategy.regime_scope) - 1)]
        confidence = min(0.95, 0.58 + abs(move_ratio) * 7 + abs(funding_rate) * 40)
    else:
        target_weight = 0.25 if move_ratio < 0 else 0.0
        regime = strategy.regime_scope[0]
        confidence = min(0.95, 0.5 + abs(move_ratio) * 6)

    return SignalDecision(
        symbol=snapshot.symbol,
        regime=regime,
        strategy_name=strategy.name,
        target_weight=target_weight,
        confidence=round(confidence, 4),
    )
