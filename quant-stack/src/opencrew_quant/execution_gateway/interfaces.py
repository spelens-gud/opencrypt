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
    order_type: str = "market"
    limit_price: float | None = None
    post_only: bool = False
    reduce_only: bool = False
    client_tag: str | None = None


@dataclass(slots=True)
class OrderAck:
    order_id: str
    accepted: bool
    reason: str = ""


class ExecutionGateway(ABC):
    @abstractmethod
    def submit(self, intent: OrderIntent) -> OrderAck:
        raise NotImplementedError
