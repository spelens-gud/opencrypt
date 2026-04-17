from __future__ import annotations

from abc import ABC, abstractmethod

from ..execution_gateway.interfaces import OrderIntent


class RiskEngine(ABC):
    @abstractmethod
    def approve(self, intent: OrderIntent) -> tuple[bool, str]:
        raise NotImplementedError
