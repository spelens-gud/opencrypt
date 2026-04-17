from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True)
class AuditEvent:
    event_type: str
    reference_id: str
    payload: dict[str, object]


class AuditLogSink(ABC):
    @abstractmethod
    def write(self, event: AuditEvent) -> None:
        raise NotImplementedError
