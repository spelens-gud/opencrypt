from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from .audit_log.interfaces import AuditEvent
from .audit_log.memory import InMemoryAuditLogSink
from .config import (
    load_risk_limits,
    load_stack_config,
    load_strategy_config,
    load_venue_config,
)
from .domain.models import Side
from .execution_gateway.interfaces import OrderIntent
from .execution_gateway.paper import PaperExecutionGateway
from .market_data.simulated import SimulatedMarketDataSource, SnapshotSeed
from .observability.memory import InMemoryAlertSink, InMemoryMetricsSink
from .portfolio_engine.simple import FixedRiskPortfolioEngine
from .risk_engine.simple import PaperRiskEngine
from .signal_engine.simple import generate_signal


@dataclass(slots=True)
class PaperCycleSummary:
    decision_ref: str
    environment: str
    venue: str
    strategy: str
    orders: list[dict[str, object]]
    audit_events: list[dict[str, object]]
    metrics: dict[str, float]
    alerts: list[dict[str, str]]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_default_market_data() -> SimulatedMarketDataSource:
    return SimulatedMarketDataSource.from_seeds(
        [
            SnapshotSeed(
                symbol="BTC/USDT:USDT",
                mid_price=68000.0,
                reference_price=66500.0,
                funding_rate=0.0001,
                latency_ms=180,
            ),
            SnapshotSeed(
                symbol="ETH/USDT:USDT",
                mid_price=3450.0,
                reference_price=3490.0,
                funding_rate=0.0002,
                latency_ms=220,
            ),
        ]
    )


def run_paper_cycle(
    root: str | Path,
    decision_ref: str,
    strategy_file: str = "trend_follow.paper.json",
    nav_usd: float = 100000.0,
) -> PaperCycleSummary:
    base = Path(root)
    stack = load_stack_config(base / "configs" / "paper" / "core-stack.json")
    venue = load_venue_config(base / "configs" / "venues" / "binance.paper.json")
    strategy = load_strategy_config(base / "configs" / "strategies" / strategy_file, venue.name)
    risk_limits = load_risk_limits(base / "configs" / "risk" / "default.paper.json")

    data_source = build_default_market_data()
    portfolio = FixedRiskPortfolioEngine(risk_limits)
    risk_engine = PaperRiskEngine(risk_limits)
    execution = PaperExecutionGateway()
    audit = InMemoryAuditLogSink()
    metrics = InMemoryMetricsSink()
    alerts = InMemoryAlertSink()

    order_summaries: list[dict[str, object]] = []
    for symbol in strategy.symbols:
        snapshot = data_source.fetch_snapshot(symbol)
        decision = generate_signal(strategy, snapshot)
        metrics.gauge(f"latency_ms.{symbol}", float(snapshot.latency_ms))
        metrics.gauge(f"signal_confidence.{symbol}", decision.confidence)

        if snapshot.latency_ms > stack.data_latency_budget_ms:
            alerts.notify("latency-budget-breach", f"{symbol} latency {snapshot.latency_ms}ms")
            continue
        if decision.target_weight <= 0:
            continue

        allocation = portfolio.build_target(symbol, decision.target_weight, nav_usd)
        quantity = round(allocation.target_notional_usd / snapshot.mid_price, 6)
        intent = OrderIntent(
            symbol=symbol,
            side=Side.BUY,
            quantity=quantity,
            notional_usd=allocation.target_notional_usd,
            reduce_only=False,
        )
        approved, reason = risk_engine.approve(intent)
        audit.write(
            AuditEvent(
                event_type="risk_check",
                reference_id=decision_ref,
                payload={
                    "symbol": symbol,
                    "approved": approved,
                    "reason": reason,
                    "target_weight": decision.target_weight,
                },
            )
        )
        if not approved:
            alerts.notify("risk-rejected", f"{symbol}: {reason}")
            continue

        ack = execution.submit(intent)
        audit.write(
            AuditEvent(
                event_type="paper_order",
                reference_id=ack.order_id,
                payload={
                    "decision_ref": decision_ref,
                    "symbol": symbol,
                    "strategy": decision.strategy_name,
                    "regime": decision.regime,
                    "confidence": decision.confidence,
                    "quantity": quantity,
                    "notional_usd": allocation.target_notional_usd,
                },
            )
        )
        order_summaries.append(
            {
                "order_id": ack.order_id,
                "symbol": symbol,
                "accepted": ack.accepted,
                "quantity": quantity,
                "notional_usd": allocation.target_notional_usd,
                "regime": decision.regime,
                "strategy": decision.strategy_name,
            }
        )

    return PaperCycleSummary(
        decision_ref=decision_ref,
        environment=stack.environment,
        venue=venue.name,
        strategy=strategy.name,
        orders=order_summaries,
        audit_events=[
            {
                "event_type": event.event_type,
                "reference_id": event.reference_id,
                "payload": event.payload,
            }
            for event in audit.events
        ],
        metrics=metrics.gauges,
        alerts=alerts.alerts,
    )
