from __future__ import annotations

from dataclasses import dataclass, field

from .interfaces import ExecutionGateway, OrderAck, OrderIntent


@dataclass(slots=True)
class PaperExecutionGateway(ExecutionGateway):
    order_counter: int = 0
    intents: list[OrderIntent] = field(default_factory=list)

    def submit(self, intent: OrderIntent) -> OrderAck:
        self.order_counter += 1
        self.intents.append(intent)
        return OrderAck(
            order_id=f"paper-{self.order_counter:04d}",
            accepted=True,
            reason="paper-accepted",
        )
