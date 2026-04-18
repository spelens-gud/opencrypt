from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from .audit_log.interfaces import AuditEvent
from .audit_log.memory import InMemoryAuditLogSink
from .config import load_risk_limits, load_stack_config, load_strategy_config, load_venue_config
from .execution_gateway.interfaces import OrderIntent
from .execution_gateway.paper import PaperExecutionGateway
from .market_data.interfaces import MarketDataSnapshot
from .observability.memory import InMemoryAlertSink, InMemoryMetricsSink
from .portfolio_engine.simple import FixedRiskPortfolioEngine
from .quote_engine.simple import QuoteCandidate, build_market_making_plan
from .risk_engine.simple import PaperRiskEngine


@dataclass(slots=True)
class ReplayStepSummary:
    step: int
    label: str
    actions: list[dict[str, object]]
    open_orders: list[dict[str, object]]
    alerts: list[dict[str, str]]
    metrics: dict[str, float]


@dataclass(slots=True)
class PaperReplaySummary:
    decision_ref: str
    environment: str
    venue: str
    strategy: str
    scenario: str
    steps: list[ReplayStepSummary]
    final_open_orders: list[dict[str, object]]
    audit_events: list[dict[str, object]]
    alerts: list[dict[str, str]]
    metrics: dict[str, float]

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["steps"] = [asdict(step) for step in self.steps]
        return payload


def _snapshot(
    *,
    symbol: str,
    mid_price: float,
    reference_price: float,
    latency_ms: int,
    best_bid: float,
    best_ask: float,
    inventory_ratio: float,
    quote_age_ms: int,
    orphan_order_count: int = 0,
    funding_rate: float | None = 0.0,
) -> MarketDataSnapshot:
    return MarketDataSnapshot(
        symbol=symbol,
        mid_price=mid_price,
        reference_price=reference_price,
        funding_rate=funding_rate,
        latency_ms=latency_ms,
        best_bid=best_bid,
        best_ask=best_ask,
        inventory_ratio=inventory_ratio,
        quote_age_ms=quote_age_ms,
        orphan_order_count=orphan_order_count,
    )


def build_market_making_replay_scenario(
    scenario: str,
    symbol: str = "BTC/USDT:USDT",
) -> list[tuple[str, MarketDataSnapshot]]:
    if scenario == "inventory_refresh":
        return [
            (
                "seed-quotes",
                _snapshot(
                    symbol=symbol,
                    mid_price=68000.0,
                    reference_price=68000.0,
                    latency_ms=120,
                    best_bid=67986.0,
                    best_ask=68014.0,
                    inventory_ratio=0.02,
                    quote_age_ms=120,
                ),
            ),
            (
                "inventory-shift",
                _snapshot(
                    symbol=symbol,
                    mid_price=68005.0,
                    reference_price=68000.0,
                    latency_ms=140,
                    best_bid=67982.0,
                    best_ask=68028.0,
                    inventory_ratio=0.28,
                    quote_age_ms=140,
                ),
            ),
        ]
    if scenario == "stale_riskoff":
        return [
            (
                "seed-quotes",
                _snapshot(
                    symbol=symbol,
                    mid_price=68000.0,
                    reference_price=68000.0,
                    latency_ms=120,
                    best_bid=67986.0,
                    best_ask=68014.0,
                    inventory_ratio=0.0,
                    quote_age_ms=120,
                ),
            ),
            (
                "stale-riskoff",
                _snapshot(
                    symbol=symbol,
                    mid_price=68020.0,
                    reference_price=68000.0,
                    latency_ms=180,
                    best_bid=67990.0,
                    best_ask=68050.0,
                    inventory_ratio=0.0,
                    quote_age_ms=950,
                    orphan_order_count=1,
                ),
            ),
        ]
    raise ValueError("scenario must be inventory_refresh or stale_riskoff")


def _price_distance_bps(lhs: float | None, rhs: float | None) -> float:
    if lhs is None or rhs is None or lhs <= 0:
        return 9999.0
    return abs(lhs - rhs) / lhs * 10000.0


def _build_order_summary(
    *,
    ack_order_id: str,
    symbol: str,
    strategy_name: str,
    regime: str,
    quote_role: str,
    target_weight: float,
    confidence: float,
    intent: OrderIntent,
) -> dict[str, object]:
    return {
        "order_id": ack_order_id,
        "symbol": symbol,
        "accepted": True,
        "quantity": intent.quantity,
        "notional_usd": intent.notional_usd,
        "target_weight": target_weight,
        "side": intent.side.value,
        "regime": regime,
        "strategy": strategy_name,
        "order_type": intent.order_type,
        "limit_price": intent.limit_price,
        "post_only": intent.post_only,
        "client_tag": quote_role,
        "confidence": confidence,
    }


def _build_quote_intent(
    *,
    symbol: str,
    candidate: QuoteCandidate,
    portfolio: FixedRiskPortfolioEngine,
    nav_usd: float,
) -> OrderIntent:
    allocation = portfolio.build_target(symbol, candidate.target_weight, nav_usd)
    quantity = round(allocation.target_notional_usd / candidate.limit_price, 6)
    return OrderIntent(
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


def _replace_required(
    existing: dict[str, object],
    intent: OrderIntent,
    *,
    max_replace_distance_bps: float,
    max_quantity_drift_ratio: float,
) -> bool:
    if str(existing.get("side")) != intent.side.value:
        return True
    if str(existing.get("order_type")) != intent.order_type:
        return True
    if bool(existing.get("post_only")) != intent.post_only:
        return True
    if _price_distance_bps(existing.get("limit_price"), intent.limit_price) > max_replace_distance_bps:
        return True
    existing_quantity = float(existing.get("quantity") or 0.0)
    if existing_quantity <= 0:
        return True
    quantity_drift = abs(existing_quantity - intent.quantity) / existing_quantity
    return quantity_drift > max_quantity_drift_ratio


def _write_audit(audit: InMemoryAuditLogSink, event_type: str, reference_id: str, payload: dict[str, object]) -> None:
    audit.write(AuditEvent(event_type=event_type, reference_id=reference_id, payload=payload))


def run_market_making_replay(
    root: str | Path,
    decision_ref: str,
    strategy_file: str = "market_making.paper.json",
    nav_usd: float = 100000.0,
    scenario: str = "inventory_refresh",
    snapshots: list[tuple[str, MarketDataSnapshot]] | None = None,
) -> PaperReplaySummary:
    base = Path(root)
    stack = load_stack_config(base / "configs" / "paper" / "core-stack.json")
    venue = load_venue_config(base / "configs" / "venues" / "binance.paper.json")
    strategy = load_strategy_config(base / "configs" / "strategies" / strategy_file, venue.name)
    risk_limits = load_risk_limits(base / "configs" / "risk" / "default.paper.json")

    if strategy.name != "market_making":
        raise ValueError("run_market_making_replay currently only supports market_making.paper.json")
    if snapshots is None:
        snapshots = build_market_making_replay_scenario(scenario)

    portfolio = FixedRiskPortfolioEngine(risk_limits)
    risk_engine = PaperRiskEngine(risk_limits)
    execution = PaperExecutionGateway()
    audit = InMemoryAuditLogSink()
    metrics = InMemoryMetricsSink()
    alerts = InMemoryAlertSink()
    current_orders: list[dict[str, object]] = []
    step_summaries: list[ReplayStepSummary] = []

    max_replace_distance_bps = float(strategy.parameters.get("max_replace_distance_bps", 2.0))
    max_quantity_drift_ratio = float(strategy.parameters.get("max_quantity_drift_ratio", 0.15))

    for index, (label, snapshot) in enumerate(snapshots, start=1):
        step_alerts_start = len(alerts.alerts)
        actions: list[dict[str, object]] = []
        step_metrics: dict[str, float] = {
            "latency_ms": float(snapshot.latency_ms),
            "inventory_ratio": snapshot.inventory_ratio,
        }
        if snapshot.latency_ms > stack.data_latency_budget_ms:
            for order in current_orders:
                execution.cancel(str(order["order_id"]))
                actions.append(
                    {
                        "action": "cancel",
                        "reason": "latency-budget-breach",
                        "order_id": order["order_id"],
                        "client_tag": order["client_tag"],
                    }
                )
                _write_audit(
                    audit,
                    "quote_cancel",
                    str(order["order_id"]),
                    {
                        "decision_ref": decision_ref,
                        "symbol": snapshot.symbol,
                        "client_tag": order["client_tag"],
                        "reason": "latency-budget-breach",
                    },
                )
            current_orders = []
            alerts.notify("latency-budget-breach", f"{snapshot.symbol} replay step {index} exceeded latency budget")
            step_summaries.append(
                ReplayStepSummary(
                    step=index,
                    label=label,
                    actions=actions,
                    open_orders=current_orders.copy(),
                    alerts=alerts.alerts[step_alerts_start:],
                    metrics=step_metrics,
                )
            )
            continue

        plan = build_market_making_plan(strategy, snapshot)
        step_metrics["spread_bps"] = plan.spread_bps
        step_metrics["quote_refresh_ms"] = float(plan.quote_refresh_ms)
        if plan.kill_switch_reason:
            for order in current_orders:
                execution.cancel(str(order["order_id"]))
                actions.append(
                    {
                        "action": "cancel",
                        "reason": plan.kill_switch_reason,
                        "order_id": order["order_id"],
                        "client_tag": order["client_tag"],
                    }
                )
                _write_audit(
                    audit,
                    "quote_cancel",
                    str(order["order_id"]),
                    {
                        "decision_ref": decision_ref,
                        "symbol": snapshot.symbol,
                        "client_tag": order["client_tag"],
                        "reason": plan.kill_switch_reason,
                    },
                )
            current_orders = []
            alerts.notify(plan.kill_switch_reason, f"{snapshot.symbol} replay step {index} entered risk-off")
            step_summaries.append(
                ReplayStepSummary(
                    step=index,
                    label=label,
                    actions=actions,
                    open_orders=current_orders.copy(),
                    alerts=alerts.alerts[step_alerts_start:],
                    metrics=step_metrics,
                )
            )
            continue

        current_by_tag = {str(order["client_tag"]): order for order in current_orders}
        next_orders: list[dict[str, object]] = []
        desired_tags: set[str] = set()
        for candidate in plan.candidates:
            desired_tags.add(candidate.quote_role)
            intent = _build_quote_intent(
                symbol=snapshot.symbol,
                candidate=candidate,
                portfolio=portfolio,
                nav_usd=nav_usd,
            )
            approved, reason = risk_engine.approve(intent)
            step_metrics[f"target_weight.{candidate.quote_role}"] = candidate.target_weight
            if not approved:
                alerts.notify("risk-rejected", f"{snapshot.symbol} {candidate.quote_role}: {reason}")
                existing = current_by_tag.get(candidate.quote_role)
                if existing is not None:
                    execution.cancel(str(existing["order_id"]))
                    actions.append(
                        {
                            "action": "cancel",
                            "reason": reason,
                            "order_id": existing["order_id"],
                            "client_tag": existing["client_tag"],
                        }
                    )
                continue

            existing = current_by_tag.get(candidate.quote_role)
            if existing is None:
                ack = execution.submit(intent)
                summary = _build_order_summary(
                    ack_order_id=ack.order_id,
                    symbol=snapshot.symbol,
                    strategy_name=plan.strategy_name,
                    regime=plan.regime,
                    quote_role=candidate.quote_role,
                    target_weight=candidate.target_weight,
                    confidence=candidate.confidence,
                    intent=intent,
                )
                actions.append(
                    {
                        "action": "place",
                        "order_id": ack.order_id,
                        "client_tag": candidate.quote_role,
                        "side": intent.side.value,
                        "limit_price": intent.limit_price,
                    }
                )
                _write_audit(
                    audit,
                    "quote_place",
                    ack.order_id,
                    {
                        "decision_ref": decision_ref,
                        "symbol": snapshot.symbol,
                        "client_tag": candidate.quote_role,
                        "side": intent.side.value,
                        "limit_price": intent.limit_price,
                        "quantity": intent.quantity,
                    },
                )
                next_orders.append(summary)
                continue

            if _replace_required(
                existing,
                intent,
                max_replace_distance_bps=max_replace_distance_bps,
                max_quantity_drift_ratio=max_quantity_drift_ratio,
            ):
                execution.cancel(str(existing["order_id"]))
                ack = execution.submit(intent)
                summary = _build_order_summary(
                    ack_order_id=ack.order_id,
                    symbol=snapshot.symbol,
                    strategy_name=plan.strategy_name,
                    regime=plan.regime,
                    quote_role=candidate.quote_role,
                    target_weight=candidate.target_weight,
                    confidence=candidate.confidence,
                    intent=intent,
                )
                actions.append(
                    {
                        "action": "replace",
                        "replaced_order_id": existing["order_id"],
                        "order_id": ack.order_id,
                        "client_tag": candidate.quote_role,
                        "side": intent.side.value,
                        "limit_price": intent.limit_price,
                    }
                )
                _write_audit(
                    audit,
                    "quote_replace",
                    ack.order_id,
                    {
                        "decision_ref": decision_ref,
                        "symbol": snapshot.symbol,
                        "client_tag": candidate.quote_role,
                        "replaced_order_id": existing["order_id"],
                        "side": intent.side.value,
                        "limit_price": intent.limit_price,
                        "quantity": intent.quantity,
                    },
                )
                next_orders.append(summary)
                continue

            actions.append(
                {
                    "action": "keep",
                    "order_id": existing["order_id"],
                    "client_tag": candidate.quote_role,
                    "side": existing["side"],
                    "limit_price": existing["limit_price"],
                }
            )
            _write_audit(
                audit,
                "quote_keep",
                str(existing["order_id"]),
                {
                    "decision_ref": decision_ref,
                    "symbol": snapshot.symbol,
                    "client_tag": candidate.quote_role,
                },
            )
            next_orders.append(existing)

        for order in current_orders:
            if str(order["client_tag"]) in desired_tags:
                continue
            execution.cancel(str(order["order_id"]))
            actions.append(
                {
                    "action": "cancel",
                    "reason": "not-in-plan",
                    "order_id": order["order_id"],
                    "client_tag": order["client_tag"],
                }
            )
            _write_audit(
                audit,
                "quote_cancel",
                str(order["order_id"]),
                {
                    "decision_ref": decision_ref,
                    "symbol": snapshot.symbol,
                    "client_tag": order["client_tag"],
                    "reason": "not-in-plan",
                },
            )

        current_orders = next_orders
        step_metrics["open_order_count"] = float(len(current_orders))
        step_metrics["action_count"] = float(len(actions))
        step_summaries.append(
            ReplayStepSummary(
                step=index,
                label=label,
                actions=actions,
                open_orders=current_orders.copy(),
                alerts=alerts.alerts[step_alerts_start:],
                metrics=step_metrics,
            )
        )

    for idx, step in enumerate(step_summaries, start=1):
        metrics.gauge(f"replay.step_{idx}.action_count", float(len(step.actions)))
        metrics.gauge(f"replay.step_{idx}.open_order_count", float(len(step.open_orders)))

    return PaperReplaySummary(
        decision_ref=decision_ref,
        environment=stack.environment,
        venue=venue.name,
        strategy=strategy.name,
        scenario=scenario,
        steps=step_summaries,
        final_open_orders=current_orders,
        audit_events=[
            {
                "event_type": event.event_type,
                "reference_id": event.reference_id,
                "payload": event.payload,
            }
            for event in audit.events
        ],
        alerts=alerts.alerts,
        metrics=metrics.gauges,
    )
