from __future__ import annotations

from ..domain.models import StrategyConfig
from ..market_data.interfaces import MarketDataSnapshot
from .interfaces import SignalDecision


def generate_signal(strategy: StrategyConfig, snapshot: MarketDataSnapshot) -> SignalDecision:
    move_ratio = (snapshot.mid_price - snapshot.reference_price) / snapshot.reference_price

    if strategy.name == "trend_follow":
        target_weight = 0.3 if move_ratio > 0 else 0.0
        regime = strategy.regime_scope[0]
        confidence = min(0.95, 0.55 + abs(move_ratio) * 8)
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
