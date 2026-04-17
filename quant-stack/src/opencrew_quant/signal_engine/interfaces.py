from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True)
class SignalDecision:
    symbol: str
    regime: str
    strategy_name: str
    target_weight: float
    confidence: float


class SignalEngine(ABC):
    @abstractmethod
    def evaluate(self, symbol: str) -> SignalDecision:
        raise NotImplementedError
