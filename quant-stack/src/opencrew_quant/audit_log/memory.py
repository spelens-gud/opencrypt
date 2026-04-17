from __future__ import annotations

from dataclasses import dataclass, field

from .interfaces import AuditEvent, AuditLogSink


@dataclass(slots=True)
class InMemoryAuditLogSink(AuditLogSink):
    events: list[AuditEvent] = field(default_factory=list)

    def write(self, event: AuditEvent) -> None:
        self.events.append(event)
