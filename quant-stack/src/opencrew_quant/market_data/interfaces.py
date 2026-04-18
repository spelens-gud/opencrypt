from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True)
class MarketDataSnapshot:
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


class MarketDataSource(ABC):
    @abstractmethod
    def fetch_snapshot(self, symbol: str) -> MarketDataSnapshot:
        raise NotImplementedError
