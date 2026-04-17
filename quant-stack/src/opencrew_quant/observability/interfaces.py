from __future__ import annotations

from abc import ABC, abstractmethod


class MetricsSink(ABC):
    @abstractmethod
    def gauge(self, name: str, value: float) -> None:
        raise NotImplementedError


class AlertSink(ABC):
    @abstractmethod
    def notify(self, title: str, body: str) -> None:
        raise NotImplementedError
