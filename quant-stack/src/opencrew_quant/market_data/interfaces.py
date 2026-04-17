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


class MarketDataSource(ABC):
    @abstractmethod
    def fetch_snapshot(self, symbol: str) -> MarketDataSnapshot:
        raise NotImplementedError
