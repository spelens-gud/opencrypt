from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True)
class TargetAllocation:
    symbol: str
    target_notional_usd: float
    max_leverage: float


class PortfolioEngine(ABC):
    @abstractmethod
    def build_target(self, symbol: str, decision_weight: float, nav_usd: float) -> TargetAllocation:
        raise NotImplementedError
