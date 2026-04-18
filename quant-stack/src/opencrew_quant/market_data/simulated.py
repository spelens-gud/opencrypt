from __future__ import annotations

from dataclasses import dataclass

from .interfaces import MarketDataSnapshot, MarketDataSource


@dataclass(slots=True)
class SnapshotSeed:
    symbol: str
    mid_price: float
    reference_price: float
    funding_rate: float | None
    latency_ms: int
    best_bid: float | None = None
    best_ask: float | None = None
    inventory_ratio: float = 0.0
    orphan_order_count: int = 0
    quote_age_ms: int | None = None


class SimulatedMarketDataSource(MarketDataSource):
    def __init__(self, snapshots: dict[str, MarketDataSnapshot]) -> None:
        self._snapshots = snapshots

    @classmethod
    def from_seeds(cls, seeds: list[SnapshotSeed]) -> "SimulatedMarketDataSource":
        snapshots = {
            seed.symbol: MarketDataSnapshot(
                symbol=seed.symbol,
                mid_price=seed.mid_price,
                reference_price=seed.reference_price,
                funding_rate=seed.funding_rate,
                latency_ms=seed.latency_ms,
                best_bid=seed.best_bid,
                best_ask=seed.best_ask,
                inventory_ratio=seed.inventory_ratio,
                orphan_order_count=seed.orphan_order_count,
                quote_age_ms=seed.quote_age_ms,
            )
            for seed in seeds
        }
        return cls(snapshots)

    def fetch_snapshot(self, symbol: str) -> MarketDataSnapshot:
        return self._snapshots[symbol]
