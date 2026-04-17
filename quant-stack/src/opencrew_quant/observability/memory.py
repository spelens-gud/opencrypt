from __future__ import annotations

from dataclasses import dataclass, field

from .interfaces import AlertSink, MetricsSink


@dataclass(slots=True)
class InMemoryMetricsSink(MetricsSink):
    gauges: dict[str, float] = field(default_factory=dict)

    def gauge(self, name: str, value: float) -> None:
        self.gauges[name] = value


@dataclass(slots=True)
class InMemoryAlertSink(AlertSink):
    alerts: list[dict[str, str]] = field(default_factory=list)

    def notify(self, title: str, body: str) -> None:
        self.alerts.append({"title": title, "body": body})
