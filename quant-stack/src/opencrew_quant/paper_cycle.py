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
from .market_data.interfaces import MarketDataSource
from .market_data.simulated import SimulatedMarketDataSource, SnapshotSeed
from .observability.memory import InMemoryAlertSink, InMemoryMetricsSink
from .portfolio_engine.simple import FixedRiskPortfolioEngine
from .quote_engine.simple import build_market_making_plan
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


def _side_from_weight(target_weight: float) -> Side:
    return Side.BUY if target_weight >= 0 else Side.SELL


def build_default_market_data() -> SimulatedMarketDataSource:
    return SimulatedMarketDataSource.from_seeds(
        [
            SnapshotSeed(
                symbol="BTC/USDT:USDT",
                mid_price=68000.0,
                reference_price=66500.0,
                funding_rate=0.0001,
                latency_ms=180,
                best_bid=67980.0,
                best_ask=68020.0,
                inventory_ratio=0.08,
                quote_age_ms=180,
            ),
            SnapshotSeed(
                symbol="ETH/USDT:USDT",
                mid_price=3450.0,
                reference_price=3490.0,
                funding_rate=0.0002,
                latency_ms=220,
                best_bid=3448.5,
                best_ask=3451.5,
                inventory_ratio=-0.04,
                quote_age_ms=220,
            ),
        ]
    )


def _record_paper_order(
    *,
    decision_ref: str,
    strategy_name: str,
    regime: str,
    confidence: float,
    symbol: str,
    target_weight: float,
    intent: OrderIntent,
    risk_engine: PaperRiskEngine,
    execution: PaperExecutionGateway,
    audit: InMemoryAuditLogSink,
    alerts: InMemoryAlertSink,
    order_summaries: list[dict[str, object]],
) -> None:
    approved, reason = risk_engine.approve(intent)
    audit.write(
        AuditEvent(
            event_type="risk_check",
            reference_id=decision_ref,
            payload={
                "symbol": symbol,
                "approved": approved,
                "reason": reason,
                "target_weight": target_weight,
                "side": intent.side.value,
                "order_type": intent.order_type,
                "limit_price": intent.limit_price,
                "post_only": intent.post_only,
                "client_tag": intent.client_tag,
            },
        )
    )
    if not approved:
        alerts.notify("risk-rejected", f"{symbol}: {reason}")
        return

    ack = execution.submit(intent)
    audit.write(
        AuditEvent(
            event_type="paper_order",
            reference_id=ack.order_id,
            payload={
                "decision_ref": decision_ref,
                "symbol": symbol,
                "strategy": strategy_name,
                "regime": regime,
                "confidence": confidence,
                "side": intent.side.value,
                "quantity": intent.quantity,
                "notional_usd": intent.notional_usd,
                "order_type": intent.order_type,
                "limit_price": intent.limit_price,
                "post_only": intent.post_only,
                "client_tag": intent.client_tag,
            },
        )
    )
    order_summaries.append(
        {
            "order_id": ack.order_id,
            "symbol": symbol,
            "accepted": ack.accepted,
            "quantity": intent.quantity,
            "notional_usd": intent.notional_usd,
            "target_weight": target_weight,
            "side": intent.side.value,
            "regime": regime,
            "strategy": strategy_name,
            "order_type": intent.order_type,
            "limit_price": intent.limit_price,
            "post_only": intent.post_only,
            "client_tag": intent.client_tag,
        }
    )


def run_paper_cycle(
    root: str | Path,
    decision_ref: str,
    strategy_file: str = "trend_follow.paper.json",
    nav_usd: float = 100000.0,
    data_source: MarketDataSource | None = None,
) -> PaperCycleSummary:
    base = Path(root)
    stack = load_stack_config(base / "configs" / "paper" / "core-stack.json")
    venue = load_venue_config(base / "configs" / "venues" / "binance.paper.json")
    strategy = load_strategy_config(base / "configs" / "strategies" / strategy_file, venue.name)
    risk_limits = load_risk_limits(base / "configs" / "risk" / "default.paper.json")

    if data_source is None:
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
        metrics.gauge(f"latency_ms.{symbol}", float(snapshot.latency_ms))
        if snapshot.latency_ms > stack.data_latency_budget_ms:
            alerts.notify("latency-budget-breach", f"{symbol} latency {snapshot.latency_ms}ms")
            continue
        if strategy.name == "market_making":
            plan = build_market_making_plan(strategy, snapshot)
            metrics.gauge(f"spread_bps.{symbol}", plan.spread_bps)
            metrics.gauge(f"inventory_ratio.{symbol}", snapshot.inventory_ratio)
            metrics.gauge(f"quote_refresh_ms.{symbol}", float(plan.quote_refresh_ms))
            if plan.kill_switch_reason:
                alerts.notify(plan.kill_switch_reason, f"{symbol} quote plan stopped")
                continue
            for candidate in plan.candidates:
                metrics.gauge(f"signal_confidence.{symbol}.{candidate.quote_role}", candidate.confidence)
                metrics.gauge(f"target_weight.{symbol}.{candidate.quote_role}", candidate.target_weight)
                allocation = portfolio.build_target(symbol, candidate.target_weight, nav_usd)
                quantity = round(allocation.target_notional_usd / candidate.limit_price, 6)
                intent = OrderIntent(
                    symbol=symbol,
                    side=candidate.side,
                    quantity=quantity,
                    notional_usd=allocation.target_notional_usd,
                    order_type="limit",
                    limit_price=candidate.limit_price,
                    post_only=candidate.post_only,
                    reduce_only=False,
                    client_tag=candidate.quote_role,
                )
                _record_paper_order(
                    decision_ref=decision_ref,
                    strategy_name=plan.strategy_name,
                    regime=plan.regime,
                    confidence=candidate.confidence,
                    symbol=symbol,
                    target_weight=candidate.target_weight,
                    intent=intent,
                    risk_engine=risk_engine,
                    execution=execution,
                    audit=audit,
                    alerts=alerts,
                    order_summaries=order_summaries,
                )
            continue

        decision = generate_signal(strategy, snapshot)
        metrics.gauge(f"signal_confidence.{symbol}", decision.confidence)
        metrics.gauge(f"target_weight.{symbol}", decision.target_weight)
        if decision.target_weight == 0:
            continue

        allocation = portfolio.build_target(symbol, decision.target_weight, nav_usd)
        quantity = round(allocation.target_notional_usd / snapshot.mid_price, 6)
        side = _side_from_weight(decision.target_weight)
        intent = OrderIntent(
            symbol=symbol,
            side=side,
            quantity=quantity,
            notional_usd=allocation.target_notional_usd,
            reduce_only=False,
        )
        _record_paper_order(
            decision_ref=decision_ref,
            strategy_name=decision.strategy_name,
            regime=decision.regime,
            confidence=decision.confidence,
            symbol=symbol,
            target_weight=decision.target_weight,
            intent=intent,
            risk_engine=risk_engine,
            execution=execution,
            audit=audit,
            alerts=alerts,
            order_summaries=order_summaries,
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
