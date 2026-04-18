from __future__ import annotations

from dataclasses import dataclass

from ..domain.models import Side, StrategyConfig
from ..market_data.interfaces import MarketDataSnapshot


@dataclass(slots=True)
class QuoteCandidate:
    symbol: str
    side: Side
    target_weight: float
    limit_price: float
    quote_role: str
    confidence: float
    post_only: bool = True


@dataclass(slots=True)
class MarketMakingQuotePlan:
    symbol: str
    strategy_name: str
    regime: str
    spread_bps: float
    inventory_ratio: float
    quote_refresh_ms: int
    candidates: list[QuoteCandidate]
    kill_switch_reason: str | None = None


def _price_with_offset(price: float, side: Side, offset_bps: float) -> float:
    if side == Side.BUY:
        return round(price * (1 - offset_bps / 10000.0), 4)
    return round(price * (1 + offset_bps / 10000.0), 4)


def build_market_making_plan(
    strategy: StrategyConfig,
    snapshot: MarketDataSnapshot,
) -> MarketMakingQuotePlan:
    params = strategy.parameters
    best_bid = snapshot.best_bid or snapshot.mid_price
    best_ask = snapshot.best_ask or snapshot.mid_price
    spread_bps = ((best_ask - best_bid) / snapshot.mid_price) * 10000 if snapshot.mid_price else 0.0

    max_quote_age_ms = int(params.get("max_quote_age_ms", 600))
    quote_age_ms = int(snapshot.quote_age_ms or snapshot.latency_ms)
    max_orphan_orders = int(params.get("max_orphan_orders", 0))
    min_spread_bps = float(params.get("min_spread_bps", 4.0))
    regime = strategy.regime_scope[min(1, len(strategy.regime_scope) - 1)]

    if quote_age_ms > max_quote_age_ms:
        return MarketMakingQuotePlan(
            symbol=snapshot.symbol,
            strategy_name=strategy.name,
            regime=regime,
            spread_bps=round(spread_bps, 4),
            inventory_ratio=snapshot.inventory_ratio,
            quote_refresh_ms=max_quote_age_ms,
            candidates=[],
            kill_switch_reason="stale-quote",
        )
    if snapshot.orphan_order_count > max_orphan_orders:
        return MarketMakingQuotePlan(
            symbol=snapshot.symbol,
            strategy_name=strategy.name,
            regime=regime,
            spread_bps=round(spread_bps, 4),
            inventory_ratio=snapshot.inventory_ratio,
            quote_refresh_ms=max_quote_age_ms,
            candidates=[],
            kill_switch_reason="orphan-orders",
        )
    if spread_bps < min_spread_bps:
        return MarketMakingQuotePlan(
            symbol=snapshot.symbol,
            strategy_name=strategy.name,
            regime=regime,
            spread_bps=round(spread_bps, 4),
            inventory_ratio=snapshot.inventory_ratio,
            quote_refresh_ms=max_quote_age_ms,
            candidates=[],
            kill_switch_reason="spread-too-tight",
        )

    per_side_fraction = float(params.get("per_side_notional_fraction", 0.03))
    max_inventory_ratio = max(float(params.get("max_inventory_ratio", 0.4)), 0.01)
    base_quote_offset_bps = float(params.get("base_quote_offset_bps", 1.0))
    inventory_skew_bps = float(params.get("inventory_skew_bps", 2.0))
    normalized_inventory = max(-1.0, min(1.0, snapshot.inventory_ratio / max_inventory_ratio))

    buy_offset_bps = base_quote_offset_bps
    sell_offset_bps = base_quote_offset_bps
    if normalized_inventory > 0:
        buy_offset_bps += normalized_inventory * inventory_skew_bps
        sell_offset_bps = max(0.0, sell_offset_bps - normalized_inventory * inventory_skew_bps)
    elif normalized_inventory < 0:
        buy_offset_bps = max(0.0, buy_offset_bps + normalized_inventory * inventory_skew_bps)
        sell_offset_bps += abs(normalized_inventory) * inventory_skew_bps

    bid_weight = max(0.0, round(per_side_fraction * (1.0 - normalized_inventory), 6))
    ask_weight = max(0.0, round(per_side_fraction * (1.0 + normalized_inventory), 6))
    confidence = round(min(0.95, 0.58 + spread_bps / 40.0 - abs(normalized_inventory) * 0.08), 4)

    candidates: list[QuoteCandidate] = []
    if bid_weight > 0:
        candidates.append(
            QuoteCandidate(
                symbol=snapshot.symbol,
                side=Side.BUY,
                target_weight=bid_weight,
                limit_price=_price_with_offset(best_bid, Side.BUY, buy_offset_bps),
                quote_role="maker-bid",
                confidence=confidence,
            )
        )
    if ask_weight > 0:
        candidates.append(
            QuoteCandidate(
                symbol=snapshot.symbol,
                side=Side.SELL,
                target_weight=ask_weight,
                limit_price=_price_with_offset(best_ask, Side.SELL, sell_offset_bps),
                quote_role="maker-ask",
                confidence=confidence,
            )
        )

    return MarketMakingQuotePlan(
        symbol=snapshot.symbol,
        strategy_name=strategy.name,
        regime=regime,
        spread_bps=round(spread_bps, 4),
        inventory_ratio=snapshot.inventory_ratio,
        quote_refresh_ms=max_quote_age_ms,
        candidates=candidates,
    )
