from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from ..domain.models import Side


@dataclass(slots=True)
class OrderIntent:
    symbol: str
    side: Side
    quantity: float
    notional_usd: float
    reduce_only: bool = False


@dataclass(slots=True)
class OrderAck:
    order_id: str
    accepted: bool
    reason: str = ""


class ExecutionGateway(ABC):
    @abstractmethod
    def submit(self, intent: OrderIntent) -> OrderAck:
        raise NotImplementedError
