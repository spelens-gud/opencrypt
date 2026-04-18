from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from .audit_log.interfaces import AuditEvent
from .audit_log.jsonl import append_jsonl_record, read_latest_jsonl_record
from .audit_log.memory import InMemoryAuditLogSink
from .config import (
    load_risk_limits,
    load_stack_config,
    load_strategy_config,
    load_venue_config,
)
from .domain.models import Side
from .execution_gateway.interfaces import OrderAck, OrderIntent
from .market_data.interfaces import MarketDataSnapshot, MarketDataSource
from .observability.memory import InMemoryAlertSink, InMemoryMetricsSink
from .portfolio_engine.simple import FixedRiskPortfolioEngine
from .quote_engine.simple import QuoteCandidate, build_market_making_plan
from .risk_engine.simple import PaperRiskEngine
from .signal_engine.simple import generate_signal

try:
    import ccxt  # type: ignore
except ImportError:  # pragma: no cover - exercised in runtime environments without ccxt
    ccxt = None


LIVE_BASE_URL = "https://fapi.binance.com"
TESTNET_BASE_URL = "https://testnet.binancefuture.com"


class BinanceApiError(RuntimeError):
    """Raised when the Binance adapter cannot complete a request."""


class CcxtExchangeLike(Protocol):
    verify: bool
    urls: dict[str, Any]
    options: dict[str, Any]

    def set_sandbox_mode(self, enabled: bool) -> None: ...
    def enable_demo_trading(self, enabled: bool) -> None: ...
    def load_markets(self) -> Any: ...
    def market(self, symbol: str) -> dict[str, Any]: ...
    def amount_to_precision(self, symbol: str, amount: float) -> str: ...
    def fetch_ticker(self, symbol: str) -> dict[str, Any]: ...
    def fetch_funding_rate(self, symbol: str) -> dict[str, Any]: ...
    def fetch_balance(self, params: dict[str, Any] | None = None) -> dict[str, Any]: ...
    def fetch_positions(
        self,
        symbols: list[str] | None = None,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]: ...
    def fetch_open_orders(
        self,
        symbol: str | None = None,
        since: int | None = None,
        limit: int | None = None,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]: ...
    def fetch_my_trades(
        self,
        symbol: str | None = None,
        since: int | None = None,
        limit: int | None = None,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]: ...
    def fetch_orders(
        self,
        symbol: str | None = None,
        since: int | None = None,
        limit: int | None = None,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]: ...
    def create_order(
        self,
        symbol: str,
        order_type: str,
        side: str,
        amount: float,
        price: float | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]: ...
    def cancel_order(self, id: str, symbol: str | None = None, params: dict[str, Any] | None = None) -> dict[str, Any]: ...


def _ensure_ccxt_available() -> None:
    if ccxt is None:
        raise RuntimeError(
            "ccxt 未安装。请先在 quant-stack 环境中安装依赖，例如 `python3 -m pip install ccxt`。"
        )


def build_ccxt_config(
    *,
    api_key: str | None,
    api_secret: str | None,
    timeout_ms: int = 10000,
) -> dict[str, Any]:
    config: dict[str, Any] = {
        "enableRateLimit": True,
        "timeout": timeout_ms,
        "options": {
            "defaultType": "future",
            # We only trade USDⓈ-M futures here, so avoid loading spot/demo spot markets.
            "fetchMarkets": {
                "types": ["linear"],
            },
        },
    }
    if api_key:
        config["apiKey"] = api_key
    if api_secret:
        config["secret"] = api_secret
    return config


def _configure_ssl_hints() -> None:
    ca_bundle = os.getenv("BINANCE_CA_BUNDLE")
    if ca_bundle:
        os.environ.setdefault("REQUESTS_CA_BUNDLE", ca_bundle)
        os.environ.setdefault("SSL_CERT_FILE", ca_bundle)


def _resolve_proxy_url(explicit_proxy: str | None = None) -> str | None:
    return explicit_proxy or (
        os.getenv("BINANCE_HTTPS_PROXY")
        or os.getenv("HTTPS_PROXY")
        or os.getenv("https_proxy")
        or os.getenv("BINANCE_PROXY")
        or os.getenv("ALL_PROXY")
        or os.getenv("all_proxy")
    )


def _configure_exchange_proxy(exchange: CcxtExchangeLike, explicit_proxy: str | None = None) -> None:
    proxy = _resolve_proxy_url(explicit_proxy)
    if not proxy:
        return
    if proxy.startswith("socks"):
        setattr(exchange, "socksProxy", proxy)
        return
    setattr(exchange, "httpsProxy", proxy)


def create_ccxt_binance_exchange(
    *,
    order_mode: str,
    api_key: str | None,
    api_secret: str | None,
    proxy_url: str | None = None,
    timeout_ms: int = 10000,
) -> CcxtExchangeLike:
    _ensure_ccxt_available()
    _configure_ssl_hints()
    exchange = ccxt.binance(build_ccxt_config(api_key=api_key, api_secret=api_secret, timeout_ms=timeout_ms))

    if os.getenv("BINANCE_SKIP_SSL_VERIFY") == "1":
        exchange.verify = False

    _configure_exchange_proxy(exchange, proxy_url)

    if order_mode == "test":
        exchange.enable_demo_trading(True)

    return exchange


def to_binance_symbol(symbol: str) -> str:
    market_symbol = symbol.replace(":USDT", "")
    return market_symbol.replace("/", "")


@dataclass(slots=True)
class CcxtBinanceUsdmClient:
    exchange: CcxtExchangeLike
    order_mode: str
    _markets_loaded: bool = False

    @classmethod
    def from_env(cls, order_mode: str, proxy_url: str | None = None) -> "CcxtBinanceUsdmClient":
        if order_mode == "test":
            api_key = os.getenv("BINANCE_DEMO_API_KEY") or os.getenv("BINANCE_API_KEY")
            api_secret = os.getenv("BINANCE_DEMO_API_SECRET") or os.getenv("BINANCE_API_SECRET")
        else:
            api_key = os.getenv("BINANCE_API_KEY")
            api_secret = os.getenv("BINANCE_API_SECRET")
        exchange = create_ccxt_binance_exchange(
            order_mode=order_mode,
            api_key=api_key,
            api_secret=api_secret,
            proxy_url=proxy_url,
        )
        return cls(exchange=exchange, order_mode=order_mode)

    def ensure_markets_loaded(self) -> None:
        if not self._markets_loaded:
            try:
                self.exchange.load_markets()
            except Exception as exc:  # pragma: no cover - depends on runtime/network
                raise BinanceApiError(f"ccxt load_markets 失败: {exc}") from exc
            self._markets_loaded = True

    def quantize_amount(self, symbol: str, amount: float) -> float:
        self.ensure_markets_loaded()
        try:
            return float(self.exchange.amount_to_precision(symbol, amount))
        except Exception as exc:
            raise BinanceApiError(f"ccxt amount_to_precision 失败: {exc}") from exc

    def min_notional_usd(self, symbol: str) -> float | None:
        self.ensure_markets_loaded()
        try:
            market = self.exchange.market(symbol)
        except Exception as exc:
            raise BinanceApiError(f"ccxt market 查询失败: {exc}") from exc

        limits = market.get("limits", {}) if isinstance(market, dict) else {}
        cost_limits = limits.get("cost", {}) if isinstance(limits, dict) else {}
        min_cost = cost_limits.get("min") if isinstance(cost_limits, dict) else None
        if min_cost is not None:
            try:
                min_cost_value = float(min_cost)
            except (TypeError, ValueError):
                min_cost_value = 0.0
            if min_cost_value > 0:
                return min_cost_value

        info = market.get("info", {}) if isinstance(market, dict) else {}
        filters = info.get("filters", []) if isinstance(info, dict) else []
        if isinstance(filters, list):
            for item in filters:
                if not isinstance(item, dict):
                    continue
                filter_type = item.get("filterType")
                if filter_type not in {"MIN_NOTIONAL", "NOTIONAL"}:
                    continue
                raw_min = item.get("notional") or item.get("minNotional")
                if raw_min is None:
                    continue
                try:
                    min_notional = float(raw_min)
                except (TypeError, ValueError):
                    continue
                if min_notional > 0:
                    return min_notional
        return None

    def fetch_snapshot(self, symbol: str) -> MarketDataSnapshot:
        self.ensure_markets_loaded()
        try:
            ticker = self.exchange.fetch_ticker(symbol)
        except Exception as exc:
            raise BinanceApiError(f"ccxt fetch_ticker 失败: {exc}") from exc

        try:
            funding = self.exchange.fetch_funding_rate(symbol)
            funding_rate = float(funding.get("fundingRate")) if funding.get("fundingRate") is not None else None
            reference_price = float(
                funding.get("markPrice")
                or funding.get("indexPrice")
                or ticker.get("last")
                or ticker.get("close")
                or 0.0
            )
        except Exception:
            # Inference: if unified funding-rate data is unavailable, fall back to ticker last/close.
            funding_rate = None
            reference_price = float(ticker.get("last") or ticker.get("close") or 0.0)

        bid = ticker.get("bid")
        ask = ticker.get("ask")
        if bid is not None and ask is not None:
            mid_price = (float(bid) + float(ask)) / 2.0
        else:
            mid_price = float(ticker.get("last") or ticker.get("close") or 0.0)

        info = ticker.get("info", {}) or {}
        latency_ms = int(info.get("latency") or 0)
        return MarketDataSnapshot(
            symbol=symbol,
            mid_price=mid_price,
            reference_price=reference_price,
            funding_rate=funding_rate,
            latency_ms=latency_ms,
            best_bid=float(bid) if bid is not None else None,
            best_ask=float(ask) if ask is not None else None,
            quote_age_ms=latency_ms,
        )

    def fetch_open_orders(self, symbol: str | None = None) -> list[dict[str, Any]]:
        self.ensure_markets_loaded()
        try:
            return self.exchange.fetch_open_orders(symbol=symbol)
        except Exception as exc:
            raise BinanceApiError(f"ccxt fetch_open_orders 失败: {exc}") from exc

    def submit_order(self, intent: OrderIntent) -> OrderAck:
        if intent.order_type == "limit":
            return self.submit_limit_order(intent)
        return self.submit_market_order(intent)

    def submit_market_order(self, intent: OrderIntent) -> OrderAck:
        self.ensure_markets_loaded()
        params = {"reduceOnly": intent.reduce_only}
        try:
            response = self.exchange.create_order(
                intent.symbol,
                "market",
                intent.side.value,
                intent.quantity,
                None,
                params,
            )
        except Exception as exc:
            raise BinanceApiError(
                f"ccxt create_order 失败: {exc}. "
                "如果当前是 test 模式，请确认使用的是 Binance demo trading 专用 API key，"
                "并已为该 key 配置允许的 IP 与期货交易权限。"
            ) from exc
        order_id = str(response.get("id") or response.get("orderId") or f"{self.order_mode}-order")
        return OrderAck(order_id=order_id, accepted=True, reason=self.order_mode)

    def submit_limit_order(self, intent: OrderIntent) -> OrderAck:
        self.ensure_markets_loaded()
        params: dict[str, Any] = {"reduceOnly": intent.reduce_only}
        if intent.post_only:
            params["postOnly"] = True
            params["timeInForce"] = "GTX"
        if intent.client_tag:
            params["newClientOrderId"] = intent.client_tag
        try:
            response = self.exchange.create_order(
                intent.symbol,
                "limit",
                intent.side.value,
                intent.quantity,
                intent.limit_price,
                params,
            )
        except Exception as exc:
            raise BinanceApiError(
                f"ccxt create_limit_order 失败: {exc}. "
                "如果当前是 test 模式，请确认使用的是 Binance demo trading 专用 API key，"
                "并已为该 key 配置允许的 IP 与期货交易权限。"
            ) from exc
        order_id = str(response.get("id") or response.get("orderId") or f"{self.order_mode}-order")
        return OrderAck(order_id=order_id, accepted=True, reason=self.order_mode)

    def cancel_order(self, symbol: str, order_id: str) -> OrderAck:
        self.ensure_markets_loaded()
        try:
            response = self.exchange.cancel_order(order_id, symbol)
        except Exception as exc:
            raise BinanceApiError(f"ccxt cancel_order 失败: {exc}") from exc
        resolved_id = str(response.get("id") or response.get("orderId") or order_id)
        return OrderAck(order_id=resolved_id, accepted=True, reason=f"{self.order_mode}-cancelled")


class BinanceUsdmMarketDataSource(MarketDataSource):
    def __init__(self, client: CcxtBinanceUsdmClient) -> None:
        self._client = client

    def fetch_snapshot(self, symbol: str) -> MarketDataSnapshot:
        return self._client.fetch_snapshot(symbol)


@dataclass(slots=True)
class BinanceCycleSummary:
    decision_ref: str
    environment: str
    venue: str
    strategy: str
    order_mode: str
    market_base_url: str
    trade_base_url: str
    orders: list[dict[str, object]]
    audit_events: list[dict[str, object]]
    metrics: dict[str, float]
    alerts: list[dict[str, str]]

    def to_dict(self) -> dict[str, object]:
        return {
            "decision_ref": self.decision_ref,
            "environment": self.environment,
            "venue": self.venue,
            "strategy": self.strategy,
            "order_mode": self.order_mode,
            "market_base_url": self.market_base_url,
            "trade_base_url": self.trade_base_url,
            "orders": self.orders,
            "audit_events": self.audit_events,
            "metrics": self.metrics,
            "alerts": self.alerts,
        }


@dataclass(slots=True)
class BinanceOrderSubmissionSummary:
    decision_ref: str
    environment: str
    venue: str
    order_mode: str
    market_base_url: str
    trade_base_url: str
    order: dict[str, object] | None
    audit_events: list[dict[str, object]]
    metrics: dict[str, float]
    alerts: list[dict[str, str]]

    def to_dict(self) -> dict[str, object]:
        return {
            "decision_ref": self.decision_ref,
            "environment": self.environment,
            "venue": self.venue,
            "order_mode": self.order_mode,
            "market_base_url": self.market_base_url,
            "trade_base_url": self.trade_base_url,
            "order": self.order,
            "audit_events": self.audit_events,
            "metrics": self.metrics,
            "alerts": self.alerts,
        }


@dataclass(slots=True)
class BinanceAccountSyncSummary:
    decision_ref: str
    environment: str
    venue: str
    order_mode: str
    market_base_url: str
    trade_base_url: str
    balances: list[dict[str, object]]
    positions: list[dict[str, object]]
    open_orders: list[dict[str, object]]
    reconcile: dict[str, object]
    audit_events: list[dict[str, object]]
    metrics: dict[str, float]
    alerts: list[dict[str, str]]

    def to_dict(self) -> dict[str, object]:
        return {
            "decision_ref": self.decision_ref,
            "environment": self.environment,
            "venue": self.venue,
            "order_mode": self.order_mode,
            "market_base_url": self.market_base_url,
            "trade_base_url": self.trade_base_url,
            "balances": self.balances,
            "positions": self.positions,
            "open_orders": self.open_orders,
            "reconcile": self.reconcile,
            "audit_events": self.audit_events,
            "metrics": self.metrics,
            "alerts": self.alerts,
        }


@dataclass(slots=True)
class BinanceActivitySyncSummary:
    decision_ref: str
    environment: str
    venue: str
    order_mode: str
    market_base_url: str
    trade_base_url: str
    symbols: list[str]
    trades: list[dict[str, object]]
    orders: list[dict[str, object]]
    reconcile: dict[str, object]
    audit_events: list[dict[str, object]]
    metrics: dict[str, float]
    alerts: list[dict[str, str]]

    def to_dict(self) -> dict[str, object]:
        return {
            "decision_ref": self.decision_ref,
            "environment": self.environment,
            "venue": self.venue,
            "order_mode": self.order_mode,
            "market_base_url": self.market_base_url,
            "trade_base_url": self.trade_base_url,
            "symbols": self.symbols,
            "trades": self.trades,
            "orders": self.orders,
            "reconcile": self.reconcile,
            "audit_events": self.audit_events,
            "metrics": self.metrics,
            "alerts": self.alerts,
        }


@dataclass(slots=True)
class BinanceReconcileLoopSummary:
    decision_ref: str
    environment: str
    venue: str
    order_mode: str
    interval_s: int
    iterations: int
    cycles: list[dict[str, object]]
    metrics: dict[str, float]
    alerts: list[dict[str, str]]

    def to_dict(self) -> dict[str, object]:
        return {
            "decision_ref": self.decision_ref,
            "environment": self.environment,
            "venue": self.venue,
            "order_mode": self.order_mode,
            "interval_s": self.interval_s,
            "iterations": self.iterations,
            "cycles": self.cycles,
            "metrics": self.metrics,
            "alerts": self.alerts,
        }


@dataclass(slots=True)
class BinanceQuoteLoopSummary:
    decision_ref: str
    environment: str
    venue: str
    strategy: str
    order_mode: str
    interval_s: int
    iterations: int
    cycles: list[dict[str, object]]
    metrics: dict[str, float]
    alerts: list[dict[str, str]]

    def to_dict(self) -> dict[str, object]:
        return {
            "decision_ref": self.decision_ref,
            "environment": self.environment,
            "venue": self.venue,
            "strategy": self.strategy,
            "order_mode": self.order_mode,
            "interval_s": self.interval_s,
            "iterations": self.iterations,
            "cycles": self.cycles,
            "metrics": self.metrics,
            "alerts": self.alerts,
        }


@dataclass(slots=True)
class BinanceHealthReport:
    status: str
    decision_ref: str | None
    recorded_at: str | None
    age_minutes: float | None
    venue: str | None
    order_mode: str | None
    summary: str
    actions: list[str]
    refs: list[str]
    metrics: dict[str, float]
    alerts: list[dict[str, str]]

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "decision_ref": self.decision_ref,
            "recorded_at": self.recorded_at,
            "age_minutes": self.age_minutes,
            "venue": self.venue,
            "order_mode": self.order_mode,
            "summary": self.summary,
            "actions": self.actions,
            "refs": self.refs,
            "metrics": self.metrics,
            "alerts": self.alerts,
        }


@dataclass(slots=True)
class PreviewExecutionGateway:
    order_counter: int = 0
    cancelled_order_ids: list[str] = field(default_factory=list)
    open_orders: list[dict[str, object]] = field(default_factory=list)

    def submit(self, intent: OrderIntent) -> OrderAck:
        self.order_counter += 1
        order_id = f"preview-{self.order_counter:04d}"
        self.open_orders.append(
            {
                "order_id": order_id,
                "client_order_id": intent.client_tag or order_id,
                "symbol": intent.symbol,
                "side": intent.side.value,
                "type": intent.order_type,
                "status": "open",
                "amount": intent.quantity,
                "remaining": intent.quantity,
                "price": intent.limit_price or 0.0,
                "reduce_only": intent.reduce_only,
                "post_only": intent.post_only,
                "timestamp": None,
            }
        )
        return OrderAck(order_id=order_id, accepted=True, reason="preview-only")

    def cancel(self, symbol: str, order_id: str) -> OrderAck:
        self.cancelled_order_ids.append(order_id)
        self.open_orders = [
            item
            for item in self.open_orders
            if not (str(item.get("order_id")) == order_id and str(item.get("symbol")) == symbol)
        ]
        return OrderAck(order_id=order_id, accepted=True, reason="preview-cancelled")

    def list_open_orders(self, symbol: str | None = None) -> list[dict[str, object]]:
        if symbol is None:
            return [dict(item) for item in self.open_orders]
        return [dict(item) for item in self.open_orders if str(item.get("symbol")) == symbol]


def _exchange_urls(exchange: CcxtExchangeLike) -> tuple[str, str]:
    api_urls = exchange.urls.get("api", {}) if isinstance(exchange.urls, dict) else {}
    fapi_public = ""
    fapi_private = ""
    if isinstance(api_urls, dict):
        fapi = api_urls.get("fapiPublic") or api_urls.get("fapi")
        sapi = api_urls.get("fapiPrivate") or api_urls.get("private")
        if isinstance(fapi, str):
            fapi_public = fapi
        if isinstance(sapi, str):
            fapi_private = sapi
    return fapi_public or LIVE_BASE_URL, fapi_private or LIVE_BASE_URL


def _to_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _normalize_balance_entries(balance: dict[str, Any]) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    for asset, payload in balance.items():
        if asset in {"info", "free", "used", "total", "timestamp", "datetime"}:
            continue
        if not isinstance(payload, dict):
            continue
        free = _to_float(payload.get("free"))
        used = _to_float(payload.get("used"))
        total = _to_float(payload.get("total"))
        if max(abs(free), abs(used), abs(total)) <= 0:
            continue
        entries.append(
            {
                "asset": asset,
                "free": free,
                "used": used,
                "total": total,
            }
        )
    entries.sort(key=lambda item: abs(_to_float(item["total"])), reverse=True)
    return entries


def _normalize_positions(positions: list[dict[str, Any]]) -> list[dict[str, object]]:
    normalized: list[dict[str, object]] = []
    for position in positions:
        contracts = _to_float(position.get("contracts"))
        notional = _to_float(position.get("notional"))
        if max(abs(contracts), abs(notional)) <= 0:
            continue
        normalized.append(
            {
                "symbol": str(position.get("symbol") or ""),
                "side": str(position.get("side") or ""),
                "contracts": contracts,
                "entry_price": _to_float(position.get("entryPrice")),
                "mark_price": _to_float(position.get("markPrice")),
                "notional_usd": notional,
                "unrealized_pnl": _to_float(position.get("unrealizedPnl")),
                "margin_mode": str(position.get("marginMode") or position.get("marginType") or ""),
                "percentage": _to_float(position.get("percentage")),
                "timestamp": position.get("timestamp"),
            }
        )
    normalized.sort(key=lambda item: abs(_to_float(item["notional_usd"])), reverse=True)
    return normalized


def _normalize_open_orders(open_orders: list[dict[str, Any]]) -> list[dict[str, object]]:
    normalized: list[dict[str, object]] = []
    for order in open_orders:
        info = order.get("info") if isinstance(order.get("info"), dict) else {}
        normalized.append(
            {
                "order_id": str(order.get("id") or order.get("clientOrderId") or ""),
                "client_order_id": str(order.get("clientOrderId") or (info.get("clientOrderId") if isinstance(info, dict) else "") or ""),
                "symbol": str(order.get("symbol") or ""),
                "side": str(order.get("side") or ""),
                "type": str(order.get("type") or ""),
                "status": str(order.get("status") or ""),
                "amount": _to_float(order.get("amount")),
                "remaining": _to_float(order.get("remaining")),
                "price": _to_float(order.get("price")),
                "reduce_only": bool(info.get("reduceOnly", False)) if isinstance(info, dict) else False,
                "post_only": bool(info.get("postOnly", False) or info.get("timeInForce") == "GTX")
                if isinstance(info, dict)
                else False,
                "timestamp": order.get("timestamp"),
            }
        )
    return normalized


def _normalize_trade_entries(trades: list[dict[str, Any]]) -> list[dict[str, object]]:
    normalized: list[dict[str, object]] = []
    for trade in trades:
        fee = trade.get("fee") if isinstance(trade.get("fee"), dict) else {}
        normalized.append(
            {
                "trade_id": str(trade.get("id") or ""),
                "order_id": str(trade.get("order") or ""),
                "symbol": str(trade.get("symbol") or ""),
                "side": str(trade.get("side") or ""),
                "taker_or_maker": str(trade.get("takerOrMaker") or ""),
                "price": _to_float(trade.get("price")),
                "amount": _to_float(trade.get("amount")),
                "cost": _to_float(trade.get("cost")),
                "fee_cost": _to_float(fee.get("cost")) if isinstance(fee, dict) else 0.0,
                "fee_currency": str(fee.get("currency") or "") if isinstance(fee, dict) else "",
                "timestamp": trade.get("timestamp"),
            }
        )
    return normalized


def _normalize_order_entries(orders: list[dict[str, Any]]) -> list[dict[str, object]]:
    normalized: list[dict[str, object]] = []
    for order in orders:
        normalized.append(
            {
                "order_id": str(order.get("id") or ""),
                "client_order_id": str(order.get("clientOrderId") or ""),
                "symbol": str(order.get("symbol") or ""),
                "side": str(order.get("side") or ""),
                "type": str(order.get("type") or ""),
                "status": str(order.get("status") or ""),
                "price": _to_float(order.get("price") or order.get("average")),
                "amount": _to_float(order.get("amount")),
                "filled": _to_float(order.get("filled")),
                "remaining": _to_float(order.get("remaining")),
                "cost": _to_float(order.get("cost")),
                "average": _to_float(order.get("average")),
                "reduce_only": bool(order.get("reduceOnly", False)),
                "timestamp": order.get("timestamp"),
            }
        )
    return normalized


def _price_distance_bps(lhs: float | None, rhs: float | None) -> float:
    if lhs is None or rhs is None or lhs <= 0:
        return 9999.0
    return abs(lhs - rhs) / lhs * 10000.0


def _quote_replace_required(
    existing: dict[str, object],
    candidate: QuoteCandidate,
    quantity: float,
    *,
    max_replace_distance_bps: float,
    max_quantity_drift_ratio: float,
) -> bool:
    if str(existing.get("side")) != candidate.side.value:
        return True
    if str(existing.get("type")) != "limit":
        return True
    if bool(existing.get("post_only")) != candidate.post_only:
        return True
    if _price_distance_bps(_to_float(existing.get("price")), candidate.limit_price) > max_replace_distance_bps:
        return True
    existing_quantity = _to_float(existing.get("amount"))
    if existing_quantity <= 0:
        return True
    quantity_drift = abs(existing_quantity - quantity) / existing_quantity
    return quantity_drift > max_quantity_drift_ratio


def _execute_market_making_binance_cycle(
    *,
    decision_ref: str,
    strategy: Any,
    stack: Any,
    nav_usd: float,
    order_mode: str,
    binance_client: CcxtBinanceUsdmClient,
    portfolio: FixedRiskPortfolioEngine,
    risk_engine: PaperRiskEngine,
    audit: InMemoryAuditLogSink,
    metrics: InMemoryMetricsSink,
    alerts: InMemoryAlertSink,
    preview_execution: PreviewExecutionGateway | None = None,
) -> list[dict[str, object]]:
    order_summaries: list[dict[str, object]] = []
    max_replace_distance_bps = float(strategy.parameters.get("max_replace_distance_bps", 2.0))
    max_quantity_drift_ratio = float(strategy.parameters.get("max_quantity_drift_ratio", 0.15))

    for symbol in strategy.symbols:
        snapshot = binance_client.fetch_snapshot(symbol)
        metrics.gauge(f"latency_ms.{symbol}", float(snapshot.latency_ms))
        metrics.gauge(f"inventory_ratio.{symbol}", snapshot.inventory_ratio)

        if preview_execution is not None:
            existing_orders = preview_execution.list_open_orders(symbol)
        else:
            existing_orders = [
                item for item in _normalize_open_orders(binance_client.fetch_open_orders(symbol)) if item["symbol"] == symbol
            ]
        metrics.gauge(f"open_order_count.{symbol}", float(len(existing_orders)))
        current_by_tag = {
            str(item.get("client_order_id") or item.get("order_id")): item
            for item in existing_orders
        }

        if snapshot.latency_ms > stack.data_latency_budget_ms:
            for existing in existing_orders:
                cancel_ack = (
                    preview_execution.cancel(symbol, str(existing["order_id"]))
                    if preview_execution is not None
                    else binance_client.cancel_order(symbol, str(existing["order_id"]))
                )
                audit.write(
                    AuditEvent(
                        event_type=f"binance_{order_mode}_quote_cancel",
                        reference_id=cancel_ack.order_id,
                        payload={
                            "decision_ref": decision_ref,
                            "symbol": symbol,
                            "client_tag": existing.get("client_order_id") or existing.get("order_id"),
                            "reason": "latency-budget-breach",
                        },
                    )
                )
            alerts.notify("latency-budget-breach", f"{symbol} latency {snapshot.latency_ms}ms")
            continue

        plan = build_market_making_plan(strategy, snapshot)
        metrics.gauge(f"spread_bps.{symbol}", plan.spread_bps)
        metrics.gauge(f"quote_refresh_ms.{symbol}", float(plan.quote_refresh_ms))

        if plan.kill_switch_reason:
            for existing in existing_orders:
                cancel_ack = (
                    preview_execution.cancel(symbol, str(existing["order_id"]))
                    if preview_execution is not None
                    else binance_client.cancel_order(symbol, str(existing["order_id"]))
                )
                audit.write(
                    AuditEvent(
                        event_type=f"binance_{order_mode}_quote_cancel",
                        reference_id=cancel_ack.order_id,
                        payload={
                            "decision_ref": decision_ref,
                            "symbol": symbol,
                            "client_tag": existing.get("client_order_id") or existing.get("order_id"),
                            "reason": plan.kill_switch_reason,
                        },
                    )
                )
            alerts.notify(plan.kill_switch_reason, f"{symbol} quote plan stopped")
            continue

        desired_tags: set[str] = set()
        for candidate in plan.candidates:
            desired_tags.add(candidate.quote_role)
            allocation = portfolio.build_target(symbol, candidate.target_weight, nav_usd)
            quantity = binance_client.quantize_amount(symbol, allocation.target_notional_usd / candidate.limit_price)
            min_notional_usd = binance_client.min_notional_usd(symbol)
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
            approved, reason = risk_engine.approve(intent, min_notional_usd=min_notional_usd)
            audit.write(
                AuditEvent(
                    event_type="risk_check",
                    reference_id=decision_ref,
                    payload={
                        "symbol": symbol,
                        "approved": approved,
                        "reason": reason,
                        "target_weight": candidate.target_weight,
                        "reference_price": snapshot.reference_price,
                        "mid_price": snapshot.mid_price,
                        "min_notional_usd": min_notional_usd,
                        "side": candidate.side.value,
                        "client_tag": candidate.quote_role,
                        "order_type": intent.order_type,
                        "limit_price": intent.limit_price,
                        "post_only": intent.post_only,
                    },
                )
            )
            if not approved:
                alerts.notify("risk-rejected", f"{symbol} {candidate.quote_role}: {reason}")
                continue

            existing = current_by_tag.get(candidate.quote_role)
            replaced_existing = False
            if existing is not None and _quote_replace_required(
                existing,
                candidate,
                quantity,
                max_replace_distance_bps=max_replace_distance_bps,
                max_quantity_drift_ratio=max_quantity_drift_ratio,
            ):
                cancel_ack = (
                    preview_execution.cancel(symbol, str(existing["order_id"]))
                    if preview_execution is not None
                    else binance_client.cancel_order(symbol, str(existing["order_id"]))
                )
                audit.write(
                    AuditEvent(
                        event_type=f"binance_{order_mode}_quote_cancel",
                        reference_id=cancel_ack.order_id,
                        payload={
                            "decision_ref": decision_ref,
                            "symbol": symbol,
                            "client_tag": candidate.quote_role,
                            "reason": "replace",
                        },
                    )
                )
                existing = None
                replaced_existing = True
            elif existing is not None:
                audit.write(
                    AuditEvent(
                        event_type=f"binance_{order_mode}_quote_keep",
                        reference_id=str(existing["order_id"]),
                        payload={
                            "decision_ref": decision_ref,
                            "symbol": symbol,
                            "client_tag": candidate.quote_role,
                            "price": existing.get("price"),
                            "amount": existing.get("amount"),
                        },
                    )
                )
                order_summaries.append(
                    {
                        "order_id": existing["order_id"],
                        "symbol": symbol,
                        "venue_symbol": to_binance_symbol(symbol),
                        "accepted": True,
                        "quantity": existing.get("amount"),
                        "notional_usd": allocation.target_notional_usd,
                        "target_weight": candidate.target_weight,
                        "side": candidate.side.value,
                        "regime": plan.regime,
                        "strategy": plan.strategy_name,
                        "order_mode": order_mode,
                        "order_type": "limit",
                        "limit_price": existing.get("price"),
                        "post_only": bool(existing.get("post_only")),
                        "client_tag": candidate.quote_role,
                        "action": "keep",
                    }
                )
                continue

            ack = preview_execution.submit(intent) if preview_execution is not None else binance_client.submit_order(intent)
            audit.write(
                AuditEvent(
                    event_type=f"binance_{order_mode}_quote_order",
                    reference_id=ack.order_id,
                    payload={
                        "decision_ref": decision_ref,
                        "symbol": symbol,
                        "venue_symbol": to_binance_symbol(symbol),
                        "strategy": plan.strategy_name,
                        "regime": plan.regime,
                        "confidence": candidate.confidence,
                        "side": candidate.side.value,
                        "quantity": quantity,
                        "notional_usd": allocation.target_notional_usd,
                        "client_tag": candidate.quote_role,
                        "order_type": intent.order_type,
                        "limit_price": intent.limit_price,
                        "post_only": intent.post_only,
                    },
                )
            )
            order_summaries.append(
                {
                    "order_id": ack.order_id,
                    "symbol": symbol,
                    "venue_symbol": to_binance_symbol(symbol),
                    "accepted": ack.accepted,
                    "quantity": quantity,
                    "notional_usd": allocation.target_notional_usd,
                    "target_weight": candidate.target_weight,
                    "side": candidate.side.value,
                    "regime": plan.regime,
                    "strategy": plan.strategy_name,
                    "order_mode": order_mode,
                    "order_type": intent.order_type,
                    "limit_price": intent.limit_price,
                    "post_only": intent.post_only,
                    "client_tag": candidate.quote_role,
                    "action": "replace" if replaced_existing else "place",
                }
            )

        for existing in existing_orders:
            tag = str(existing.get("client_order_id") or existing.get("order_id"))
            if tag in desired_tags:
                continue
            cancel_ack = (
                preview_execution.cancel(symbol, str(existing["order_id"]))
                if preview_execution is not None
                else binance_client.cancel_order(symbol, str(existing["order_id"]))
            )
            audit.write(
                AuditEvent(
                    event_type=f"binance_{order_mode}_quote_cancel",
                    reference_id=cancel_ack.order_id,
                    payload={
                        "decision_ref": decision_ref,
                        "symbol": symbol,
                        "client_tag": tag,
                        "reason": "not-in-plan",
                    },
                )
            )

    return order_summaries


def _extract_balance_position_symbols(balance: dict[str, Any]) -> set[str]:
    info = balance.get("info", {}) if isinstance(balance, dict) else {}
    positions = info.get("positions", []) if isinstance(info, dict) else []
    symbols: set[str] = set()
    if not isinstance(positions, list):
        return symbols
    for item in positions:
        if not isinstance(item, dict):
            continue
        position_amt = _to_float(item.get("positionAmt"))
        notional = _to_float(item.get("notional"))
        if max(abs(position_amt), abs(notional)) <= 0:
            continue
        symbol = item.get("symbol")
        if isinstance(symbol, str) and symbol:
            symbols.add(symbol)
    return symbols


def run_binance_cycle(
    root: str | Path,
    decision_ref: str,
    strategy_file: str = "trend_follow.paper.json",
    nav_usd: float = 100000.0,
    order_mode: str = "preview",
    client: CcxtBinanceUsdmClient | None = None,
) -> BinanceCycleSummary:
    if order_mode not in {"preview", "test", "live"}:
        raise ValueError("order_mode must be preview, test, or live")

    base = Path(root)
    stack = load_stack_config(base / "configs" / "paper" / "core-stack.json")
    venue = load_venue_config(base / "configs" / "venues" / "binance.paper.json")
    strategy = load_strategy_config(base / "configs" / "strategies" / strategy_file, venue.name)
    risk_limits = load_risk_limits(base / "configs" / "risk" / "default.paper.json")

    binance_client = client or CcxtBinanceUsdmClient.from_env(
        order_mode=order_mode,
        proxy_url=venue.proxy_url,
    )
    data_source = BinanceUsdmMarketDataSource(binance_client)
    portfolio = FixedRiskPortfolioEngine(risk_limits)
    risk_engine = PaperRiskEngine(risk_limits)
    audit = InMemoryAuditLogSink()
    metrics = InMemoryMetricsSink()
    alerts = InMemoryAlertSink()
    preview_execution = PreviewExecutionGateway() if order_mode == "preview" else None

    if strategy.name == "market_making":
        order_summaries = _execute_market_making_binance_cycle(
            decision_ref=decision_ref,
            strategy=strategy,
            stack=stack,
            nav_usd=nav_usd,
            order_mode=order_mode,
            binance_client=binance_client,
            portfolio=portfolio,
            risk_engine=risk_engine,
            audit=audit,
            metrics=metrics,
            alerts=alerts,
            preview_execution=preview_execution,
        )
        market_base_url, trade_base_url = _exchange_urls(binance_client.exchange)
        return BinanceCycleSummary(
            decision_ref=decision_ref,
            environment=stack.environment,
            venue=venue.name,
            strategy=strategy.name,
            order_mode=order_mode,
            market_base_url=market_base_url,
            trade_base_url=trade_base_url,
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

    order_summaries: list[dict[str, object]] = []
    for symbol in strategy.symbols:
        snapshot = data_source.fetch_snapshot(symbol)
        decision = generate_signal(strategy, snapshot)
        metrics.gauge(f"latency_ms.{symbol}", float(snapshot.latency_ms))
        metrics.gauge(f"signal_confidence.{symbol}", decision.confidence)
        metrics.gauge(f"funding_rate.{symbol}", float(snapshot.funding_rate or 0.0))
        metrics.gauge(f"target_weight.{symbol}", decision.target_weight)

        if snapshot.latency_ms > stack.data_latency_budget_ms:
            alerts.notify("latency-budget-breach", f"{symbol} latency {snapshot.latency_ms}ms")
            continue
        if decision.target_weight == 0:
            continue

        allocation = portfolio.build_target(symbol, decision.target_weight, nav_usd)
        quantity = binance_client.quantize_amount(symbol, allocation.target_notional_usd / snapshot.mid_price)
        min_notional_usd = binance_client.min_notional_usd(symbol)
        side = Side.BUY if decision.target_weight >= 0 else Side.SELL
        intent = OrderIntent(
            symbol=symbol,
            side=side,
            quantity=quantity,
            notional_usd=allocation.target_notional_usd,
            reduce_only=False,
        )
        approved, reason = risk_engine.approve(intent, min_notional_usd=min_notional_usd)
        audit.write(
            AuditEvent(
                event_type="risk_check",
                reference_id=decision_ref,
                payload={
                    "symbol": symbol,
                    "approved": approved,
                    "reason": reason,
                    "target_weight": decision.target_weight,
                    "reference_price": snapshot.reference_price,
                    "mid_price": snapshot.mid_price,
                    "min_notional_usd": min_notional_usd,
                    "side": side.value,
                },
            )
        )
        if not approved:
            alerts.notify("risk-rejected", f"{symbol}: {reason}")
            continue

        ack = preview_execution.submit(intent) if preview_execution is not None else binance_client.submit_market_order(intent)
        audit.write(
            AuditEvent(
                event_type=f"binance_{order_mode}_order",
                reference_id=ack.order_id,
                payload={
                    "decision_ref": decision_ref,
                    "symbol": symbol,
                    "venue_symbol": to_binance_symbol(symbol),
                    "strategy": decision.strategy_name,
                    "regime": decision.regime,
                    "confidence": decision.confidence,
                    "side": side.value,
                    "quantity": quantity,
                    "notional_usd": allocation.target_notional_usd,
                },
            )
        )
        order_summaries.append(
            {
                "order_id": ack.order_id,
                "symbol": symbol,
                "venue_symbol": to_binance_symbol(symbol),
                "accepted": ack.accepted,
                "quantity": quantity,
                "notional_usd": allocation.target_notional_usd,
                "target_weight": decision.target_weight,
                "side": side.value,
                "regime": decision.regime,
                "strategy": decision.strategy_name,
                "order_mode": order_mode,
            }
        )

    market_base_url, trade_base_url = _exchange_urls(binance_client.exchange)
    return BinanceCycleSummary(
        decision_ref=decision_ref,
        environment=stack.environment,
        venue=venue.name,
        strategy=strategy.name,
        order_mode=order_mode,
        market_base_url=market_base_url,
        trade_base_url=trade_base_url,
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


def submit_binance_order(
    root: str | Path,
    decision_ref: str,
    symbol: str,
    side: Side = Side.BUY,
    notional_usd: float = 25.0,
    order_mode: str = "test",
    client: CcxtBinanceUsdmClient | None = None,
) -> BinanceOrderSubmissionSummary:
    if order_mode not in {"preview", "test", "live"}:
        raise ValueError("order_mode must be preview, test, or live")

    base = Path(root)
    stack = load_stack_config(base / "configs" / "paper" / "core-stack.json")
    venue = load_venue_config(base / "configs" / "venues" / "binance.paper.json")
    risk_limits = load_risk_limits(base / "configs" / "risk" / "default.paper.json")

    if notional_usd <= 0:
        raise ValueError("notional_usd must be positive")

    binance_client = client or CcxtBinanceUsdmClient.from_env(
        order_mode=order_mode,
        proxy_url=venue.proxy_url,
    )
    risk_engine = PaperRiskEngine(risk_limits)
    audit = InMemoryAuditLogSink()
    metrics = InMemoryMetricsSink()
    alerts = InMemoryAlertSink()

    snapshot = binance_client.fetch_snapshot(symbol)
    metrics.gauge(f"latency_ms.{symbol}", float(snapshot.latency_ms))
    metrics.gauge(f"funding_rate.{symbol}", float(snapshot.funding_rate or 0.0))
    metrics.gauge(f"mid_price.{symbol}", snapshot.mid_price)

    quantity = binance_client.quantize_amount(symbol, notional_usd / snapshot.mid_price)
    min_notional_usd = binance_client.min_notional_usd(symbol)
    intent = OrderIntent(
        symbol=symbol,
        side=side,
        quantity=quantity,
        notional_usd=notional_usd,
        reduce_only=False,
    )
    approved, reason = risk_engine.approve(intent, min_notional_usd=min_notional_usd)
    audit.write(
        AuditEvent(
            event_type="risk_check",
            reference_id=decision_ref,
            payload={
                "symbol": symbol,
                "side": side.value,
                "approved": approved,
                "reason": reason,
                "mid_price": snapshot.mid_price,
                "reference_price": snapshot.reference_price,
                "requested_notional_usd": notional_usd,
                "quantity": quantity,
                "min_notional_usd": min_notional_usd,
            },
        )
    )

    order_summary: dict[str, object] | None = None
    if not approved:
        alerts.notify("risk-rejected", f"{symbol}: {reason}")
    else:
        preview_execution = PreviewExecutionGateway() if order_mode == "preview" else None
        ack = preview_execution.submit(intent) if preview_execution is not None else binance_client.submit_market_order(intent)
        audit.write(
            AuditEvent(
                event_type=f"binance_{order_mode}_order",
                reference_id=ack.order_id,
                payload={
                    "decision_ref": decision_ref,
                    "symbol": symbol,
                    "venue_symbol": to_binance_symbol(symbol),
                    "side": side.value,
                    "quantity": quantity,
                    "notional_usd": notional_usd,
                },
            )
        )
        order_summary = {
            "order_id": ack.order_id,
            "symbol": symbol,
            "venue_symbol": to_binance_symbol(symbol),
            "side": side.value,
            "accepted": ack.accepted,
            "quantity": quantity,
            "notional_usd": notional_usd,
            "order_mode": order_mode,
        }

    market_base_url, trade_base_url = _exchange_urls(binance_client.exchange)
    return BinanceOrderSubmissionSummary(
        decision_ref=decision_ref,
        environment=stack.environment,
        venue=venue.name,
        order_mode=order_mode,
        market_base_url=market_base_url,
        trade_base_url=trade_base_url,
        order=order_summary,
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


def sync_binance_account(
    root: str | Path,
    decision_ref: str,
    order_mode: str = "test",
    audit_dir: str | Path | None = None,
    client: CcxtBinanceUsdmClient | None = None,
) -> BinanceAccountSyncSummary:
    if order_mode not in {"test", "live"}:
        raise ValueError("order_mode must be test or live")

    base = Path(root)
    stack = load_stack_config(base / "configs" / "paper" / "core-stack.json")
    venue_config_name = "binance.paper.json" if order_mode == "test" else "binance.live.json"
    venue = load_venue_config(base / "configs" / "venues" / venue_config_name)

    binance_client = client or CcxtBinanceUsdmClient.from_env(
        order_mode=order_mode,
        proxy_url=venue.proxy_url,
    )
    exchange = binance_client.exchange
    audit = InMemoryAuditLogSink()
    metrics = InMemoryMetricsSink()
    alerts = InMemoryAlertSink()

    try:
        balance = exchange.fetch_balance({"type": "future"})
    except Exception as exc:
        raise BinanceApiError(f"ccxt fetch_balance 失败: {exc}") from exc

    try:
        positions = exchange.fetch_positions()
    except Exception as exc:
        raise BinanceApiError(f"ccxt fetch_positions 失败: {exc}") from exc

    exchange.options["warnOnFetchOpenOrdersWithoutSymbol"] = False
    try:
        open_orders = exchange.fetch_open_orders()
    except Exception as exc:
        raise BinanceApiError(f"ccxt fetch_open_orders 失败: {exc}") from exc

    balances = _normalize_balance_entries(balance)
    normalized_positions = _normalize_positions(positions)
    normalized_open_orders = _normalize_open_orders(open_orders)

    total_equity_usd = sum(
        _to_float(item.get("total"))
        for item in balances
        if str(item.get("asset")) in {"USDT", "USDC", "FDUSD"}
    )
    available_usdt = 0.0
    for item in balances:
        if str(item.get("asset")) == "USDT":
            available_usdt = _to_float(item.get("free"))
            break

    balance_symbols = _extract_balance_position_symbols(balance)
    fetched_symbols = {
        to_binance_symbol(str(item.get("symbol")))
        for item in normalized_positions
        if str(item.get("symbol"))
    }
    reconcile_ok = balance_symbols == fetched_symbols
    missing_in_positions = sorted(balance_symbols - fetched_symbols)
    missing_in_balance = sorted(fetched_symbols - balance_symbols)

    metrics.gauge("account.total_equity_usd", total_equity_usd)
    metrics.gauge("account.available_usdt", available_usdt)
    metrics.gauge("account.position_count", float(len(normalized_positions)))
    metrics.gauge("account.open_order_count", float(len(normalized_open_orders)))

    if not reconcile_ok:
        alerts.notify(
            "reconcile-gap",
            f"balance_positions={missing_in_positions} fetched_positions={missing_in_balance}",
        )

    audit.write(
        AuditEvent(
            event_type="account_snapshot",
            reference_id=decision_ref,
            payload={
                "balance_count": len(balances),
                "position_count": len(normalized_positions),
                "open_order_count": len(normalized_open_orders),
                "total_equity_usd": total_equity_usd,
                "available_usdt": available_usdt,
                "reconcile_ok": reconcile_ok,
            },
        )
    )

    market_base_url, trade_base_url = _exchange_urls(exchange)
    summary = BinanceAccountSyncSummary(
        decision_ref=decision_ref,
        environment=stack.environment,
        venue=venue.name,
        order_mode=order_mode,
        market_base_url=market_base_url,
        trade_base_url=trade_base_url,
        balances=balances,
        positions=normalized_positions,
        open_orders=normalized_open_orders,
        reconcile={
            "ok": reconcile_ok,
            "balance_position_symbols": sorted(balance_symbols),
            "fetched_position_symbols": sorted(fetched_symbols),
            "missing_in_positions": missing_in_positions,
            "missing_in_balance": missing_in_balance,
        },
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
    append_jsonl_record(
        root=base,
        audit_dir=audit_dir,
        stream_name="account_snapshots",
        payload=summary.to_dict(),
    )
    return summary


def sync_binance_activity(
    root: str | Path,
    decision_ref: str,
    order_mode: str = "test",
    strategy_file: str = "trend_follow.paper.json",
    symbol: str | None = None,
    limit: int = 20,
    audit_dir: str | Path | None = None,
    client: CcxtBinanceUsdmClient | None = None,
) -> BinanceActivitySyncSummary:
    if order_mode not in {"test", "live"}:
        raise ValueError("order_mode must be test or live")
    if limit <= 0:
        raise ValueError("limit must be positive")

    base = Path(root)
    stack = load_stack_config(base / "configs" / "paper" / "core-stack.json")
    venue_config_name = "binance.paper.json" if order_mode == "test" else "binance.live.json"
    venue = load_venue_config(base / "configs" / "venues" / venue_config_name)
    strategy = load_strategy_config(base / "configs" / "strategies" / strategy_file, venue.name)

    binance_client = client or CcxtBinanceUsdmClient.from_env(
        order_mode=order_mode,
        proxy_url=venue.proxy_url,
    )
    exchange = binance_client.exchange
    audit = InMemoryAuditLogSink()
    metrics = InMemoryMetricsSink()
    alerts = InMemoryAlertSink()

    symbols = [symbol] if symbol else list(strategy.symbols)
    all_trades: list[dict[str, object]] = []
    all_orders: list[dict[str, object]] = []
    missing_order_ids: set[str] = set()

    for item in symbols:
        try:
            trades = exchange.fetch_my_trades(item, limit=limit)
        except Exception as exc:
            raise BinanceApiError(f"ccxt fetch_my_trades 失败: {exc}") from exc
        try:
            orders = exchange.fetch_orders(item, limit=limit)
        except Exception as exc:
            raise BinanceApiError(f"ccxt fetch_orders 失败: {exc}") from exc

        normalized_trades = _normalize_trade_entries(trades)
        normalized_orders = _normalize_order_entries(orders)
        all_trades.extend(normalized_trades)
        all_orders.extend(normalized_orders)

        order_ids = {str(entry["order_id"]) for entry in normalized_orders if str(entry["order_id"])}
        trade_order_ids = {str(entry["order_id"]) for entry in normalized_trades if str(entry["order_id"])}
        unresolved_ids = {value for value in trade_order_ids - order_ids if value}
        missing_order_ids.update(unresolved_ids)

        metrics.gauge(f"activity.trade_count.{item}", float(len(normalized_trades)))
        metrics.gauge(f"activity.order_count.{item}", float(len(normalized_orders)))
        metrics.gauge(
            f"activity.fee_cost_usdt.{item}",
            sum(_to_float(entry["fee_cost"]) for entry in normalized_trades if entry["fee_currency"] == "USDT"),
        )
        audit.write(
            AuditEvent(
                event_type="activity_snapshot",
                reference_id=f"{decision_ref}:{item}",
                payload={
                    "symbol": item,
                    "trade_count": len(normalized_trades),
                    "order_count": len(normalized_orders),
                    "missing_order_ids": sorted(unresolved_ids),
                },
            )
        )

    if missing_order_ids:
        alerts.notify("activity-reconcile-gap", f"missing_order_ids={sorted(missing_order_ids)}")

    all_trades.sort(key=lambda entry: int(entry["timestamp"] or 0), reverse=True)
    all_orders.sort(key=lambda entry: int(entry["timestamp"] or 0), reverse=True)
    total_fee_usdt = sum(_to_float(entry["fee_cost"]) for entry in all_trades if entry["fee_currency"] == "USDT")
    metrics.gauge("activity.total_trade_count", float(len(all_trades)))
    metrics.gauge("activity.total_order_count", float(len(all_orders)))
    metrics.gauge("activity.total_fee_cost_usdt", total_fee_usdt)

    market_base_url, trade_base_url = _exchange_urls(exchange)
    summary = BinanceActivitySyncSummary(
        decision_ref=decision_ref,
        environment=stack.environment,
        venue=venue.name,
        order_mode=order_mode,
        market_base_url=market_base_url,
        trade_base_url=trade_base_url,
        symbols=symbols,
        trades=all_trades,
        orders=all_orders,
        reconcile={
            "ok": not missing_order_ids,
            "missing_order_ids": sorted(missing_order_ids),
        },
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
    append_jsonl_record(
        root=base,
        audit_dir=audit_dir,
        stream_name="activity_snapshots",
        payload=summary.to_dict(),
    )
    return summary


def run_binance_reconcile_loop(
    root: str | Path,
    decision_ref: str,
    order_mode: str = "test",
    strategy_file: str = "trend_follow.paper.json",
    symbol: str | None = None,
    limit: int = 20,
    iterations: int = 1,
    interval_s: int | None = None,
    max_consecutive_failures: int = 3,
    audit_dir: str | Path | None = None,
    client: CcxtBinanceUsdmClient | None = None,
    sleeper: Any | None = None,
) -> BinanceReconcileLoopSummary:
    if order_mode not in {"test", "live"}:
        raise ValueError("order_mode must be test or live")
    if iterations <= 0:
        raise ValueError("iterations must be positive")
    if limit <= 0:
        raise ValueError("limit must be positive")
    if max_consecutive_failures <= 0:
        raise ValueError("max_consecutive_failures must be positive")

    base = Path(root)
    stack = load_stack_config(base / "configs" / "paper" / "core-stack.json")
    venue_config_name = "binance.paper.json" if order_mode == "test" else "binance.live.json"
    venue = load_venue_config(base / "configs" / "venues" / venue_config_name)
    resolved_interval_s = venue.reconcile_interval_s if interval_s is None else interval_s
    if resolved_interval_s < 0:
        raise ValueError("interval_s must be non-negative")

    binance_client = client or CcxtBinanceUsdmClient.from_env(
        order_mode=order_mode,
        proxy_url=venue.proxy_url,
    )
    sleep_fn = sleeper or time.sleep
    loop_metrics = InMemoryMetricsSink()
    loop_alerts = InMemoryAlertSink()
    cycles: list[dict[str, object]] = []
    consecutive_failures = 0

    for index in range(iterations):
        cycle_ref = f"{decision_ref}:cycle-{index + 1}"
        try:
            account_summary = sync_binance_account(
                root=base,
                decision_ref=cycle_ref,
                order_mode=order_mode,
                audit_dir=audit_dir,
                client=binance_client,
            )
            activity_summary = sync_binance_activity(
                root=base,
                decision_ref=cycle_ref,
                order_mode=order_mode,
                strategy_file=strategy_file,
                symbol=symbol,
                limit=limit,
                audit_dir=audit_dir,
                client=binance_client,
            )
            cycle_ok = bool(account_summary.reconcile["ok"]) and bool(activity_summary.reconcile["ok"])
            cycle_alerts = account_summary.alerts + activity_summary.alerts
            if not cycle_ok:
                loop_alerts.notify(
                    "reconcile-cycle-alert",
                    f"{cycle_ref}: account_ok={account_summary.reconcile['ok']} activity_ok={activity_summary.reconcile['ok']}",
                )
            cycles.append(
                {
                    "iteration": index + 1,
                    "decision_ref": cycle_ref,
                    "ok": cycle_ok,
                    "account": account_summary.to_dict(),
                    "activity": activity_summary.to_dict(),
                    "alerts": cycle_alerts,
                }
            )
            loop_metrics.gauge(f"reconcile_loop.cycle_ok.{index + 1}", 1.0 if cycle_ok else 0.0)
            loop_metrics.gauge(
                f"reconcile_loop.open_order_count.{index + 1}",
                float(len(account_summary.open_orders)),
            )
            loop_metrics.gauge(
                f"reconcile_loop.trade_count.{index + 1}",
                float(len(activity_summary.trades)),
            )
            consecutive_failures = 0
        except Exception as exc:
            consecutive_failures += 1
            loop_alerts.notify("reconcile-cycle-error", f"{cycle_ref}: {exc}")
            cycles.append(
                {
                    "iteration": index + 1,
                    "decision_ref": cycle_ref,
                    "ok": False,
                    "error": str(exc),
                    "alerts": [{"title": "reconcile-cycle-error", "body": str(exc)}],
                }
            )
            loop_metrics.gauge(f"reconcile_loop.cycle_ok.{index + 1}", 0.0)
            loop_metrics.gauge(
                f"reconcile_loop.consecutive_failures.{index + 1}",
                float(consecutive_failures),
            )
            if consecutive_failures >= max_consecutive_failures:
                loop_alerts.notify(
                    "reconcile-loop-stopped",
                    f"stopped after {consecutive_failures} consecutive failures at {cycle_ref}",
                )
                break
        if index < iterations - 1 and resolved_interval_s > 0:
            sleep_fn(resolved_interval_s)

    loop_metrics.gauge("reconcile_loop.total_cycles", float(iterations))
    loop_metrics.gauge(
        "reconcile_loop.ok_cycles",
        float(sum(1 for cycle in cycles if bool(cycle["ok"]))),
    )
    loop_metrics.gauge("reconcile_loop.completed_cycles", float(len(cycles)))
    summary = BinanceReconcileLoopSummary(
        decision_ref=decision_ref,
        environment=stack.environment,
        venue=venue.name,
        order_mode=order_mode,
        interval_s=resolved_interval_s,
        iterations=iterations,
        cycles=cycles,
        metrics=loop_metrics.gauges,
        alerts=loop_alerts.alerts,
    )
    append_jsonl_record(
        root=base,
        audit_dir=audit_dir,
        stream_name="reconcile_loops",
        payload=summary.to_dict(),
    )
    return summary


def run_binance_quote_loop(
    root: str | Path,
    decision_ref: str,
    order_mode: str = "preview",
    strategy_file: str = "market_making.paper.json",
    nav_usd: float = 100000.0,
    iterations: int = 1,
    interval_s: int | None = None,
    max_consecutive_failures: int = 3,
    audit_dir: str | Path | None = None,
    client: CcxtBinanceUsdmClient | None = None,
    sleeper: Any | None = None,
) -> BinanceQuoteLoopSummary:
    if order_mode not in {"preview", "test", "live"}:
        raise ValueError("order_mode must be preview, test, or live")
    if iterations <= 0:
        raise ValueError("iterations must be positive")
    if max_consecutive_failures <= 0:
        raise ValueError("max_consecutive_failures must be positive")

    base = Path(root)
    stack = load_stack_config(base / "configs" / "paper" / "core-stack.json")
    venue = load_venue_config(base / "configs" / "venues" / "binance.paper.json")
    strategy = load_strategy_config(base / "configs" / "strategies" / strategy_file, venue.name)
    risk_limits = load_risk_limits(base / "configs" / "risk" / "default.paper.json")
    if strategy.name != "market_making":
        raise ValueError("run_binance_quote_loop currently only supports market_making.paper.json")

    resolved_interval_s = venue.reconcile_interval_s if interval_s is None else interval_s
    if resolved_interval_s < 0:
        raise ValueError("interval_s must be non-negative")

    binance_client = client or CcxtBinanceUsdmClient.from_env(
        order_mode=order_mode,
        proxy_url=venue.proxy_url,
    )
    portfolio = FixedRiskPortfolioEngine(risk_limits)
    risk_engine = PaperRiskEngine(risk_limits)
    loop_metrics = InMemoryMetricsSink()
    loop_alerts = InMemoryAlertSink()
    sleep_fn = sleeper or time.sleep
    cycles: list[dict[str, object]] = []
    consecutive_failures = 0
    preview_execution = PreviewExecutionGateway() if order_mode == "preview" else None

    for index in range(iterations):
        cycle_ref = f"{decision_ref}:cycle-{index + 1}"
        cycle_audit = InMemoryAuditLogSink()
        cycle_metrics = InMemoryMetricsSink()
        cycle_alerts = InMemoryAlertSink()
        try:
            order_summaries = _execute_market_making_binance_cycle(
                decision_ref=cycle_ref,
                strategy=strategy,
                stack=stack,
                nav_usd=nav_usd,
                order_mode=order_mode,
                binance_client=binance_client,
                portfolio=portfolio,
                risk_engine=risk_engine,
                audit=cycle_audit,
                metrics=cycle_metrics,
                alerts=cycle_alerts,
                preview_execution=preview_execution,
            )
            cycle_ok = not any(
                alert["title"] in {"latency-budget-breach", "stale-quote", "orphan-orders", "risk-rejected"}
                for alert in cycle_alerts.alerts
            )
            if not cycle_ok:
                loop_alerts.notify("quote-loop-alert", f"{cycle_ref}: alerts={cycle_alerts.alerts}")
            open_order_count = (
                len(preview_execution.list_open_orders()) if preview_execution is not None else float("nan")
            )
            if preview_execution is None and strategy.symbols:
                open_order_count = float(len(binance_client.fetch_open_orders(strategy.symbols[0])))
            cycles.append(
                {
                    "iteration": index + 1,
                    "decision_ref": cycle_ref,
                    "ok": cycle_ok,
                    "orders": order_summaries,
                    "audit_events": [
                        {
                            "event_type": event.event_type,
                            "reference_id": event.reference_id,
                            "payload": event.payload,
                        }
                        for event in cycle_audit.events
                    ],
                    "metrics": cycle_metrics.gauges,
                    "alerts": cycle_alerts.alerts,
                    "open_order_count": open_order_count,
                }
            )
            loop_metrics.gauge(f"quote_loop.cycle_ok.{index + 1}", 1.0 if cycle_ok else 0.0)
            loop_metrics.gauge(
                f"quote_loop.order_count.{index + 1}",
                float(len(order_summaries)),
            )
            loop_metrics.gauge(
                f"quote_loop.open_order_count.{index + 1}",
                float(open_order_count if open_order_count == open_order_count else 0.0),
            )
            consecutive_failures = 0
        except Exception as exc:
            consecutive_failures += 1
            loop_alerts.notify("quote-loop-error", f"{cycle_ref}: {exc}")
            cycles.append(
                {
                    "iteration": index + 1,
                    "decision_ref": cycle_ref,
                    "ok": False,
                    "error": str(exc),
                    "alerts": [{"title": "quote-loop-error", "body": str(exc)}],
                }
            )
            loop_metrics.gauge(f"quote_loop.cycle_ok.{index + 1}", 0.0)
            loop_metrics.gauge(
                f"quote_loop.consecutive_failures.{index + 1}",
                float(consecutive_failures),
            )
            if consecutive_failures >= max_consecutive_failures:
                loop_alerts.notify(
                    "quote-loop-stopped",
                    f"stopped after {consecutive_failures} consecutive failures at {cycle_ref}",
                )
                break
        if index < iterations - 1 and resolved_interval_s > 0:
            sleep_fn(resolved_interval_s)

    loop_metrics.gauge("quote_loop.total_cycles", float(iterations))
    loop_metrics.gauge(
        "quote_loop.ok_cycles",
        float(sum(1 for cycle in cycles if bool(cycle["ok"]))),
    )
    loop_metrics.gauge("quote_loop.completed_cycles", float(len(cycles)))
    summary = BinanceQuoteLoopSummary(
        decision_ref=decision_ref,
        environment=stack.environment,
        venue=venue.name,
        strategy=strategy.name,
        order_mode=order_mode,
        interval_s=resolved_interval_s,
        iterations=iterations,
        cycles=cycles,
        metrics=loop_metrics.gauges,
        alerts=loop_alerts.alerts,
    )
    append_jsonl_record(
        root=base,
        audit_dir=audit_dir,
        stream_name="quote_loops",
        payload=summary.to_dict(),
    )
    return summary


def _parse_recorded_at(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def report_binance_health(
    root: str | Path,
    max_age_minutes: int = 30,
    audit_dir: str | Path | None = None,
) -> BinanceHealthReport:
    if max_age_minutes <= 0:
        raise ValueError("max_age_minutes must be positive")

    record = read_latest_jsonl_record(
        root=root,
        audit_dir=audit_dir,
        stream_name="reconcile_loops",
    )
    if record is None:
        return BinanceHealthReport(
            status="action_required",
            decision_ref=None,
            recorded_at=None,
            age_minutes=None,
            venue=None,
            order_mode=None,
            summary="missing reconcile loop audit record",
            actions=[
                "run run-binance-reconcile-loop immediately",
                "verify audit directory is writable",
            ],
            refs=[],
            metrics={},
            alerts=[{"title": "missing-audit", "body": "reconcile_loops.jsonl not found"}],
        )

    recorded_at = _parse_recorded_at(record.get("recorded_at"))
    now = datetime.now(timezone.utc)
    age_minutes = None
    stale = False
    if recorded_at is not None:
        age_minutes = round((now - recorded_at).total_seconds() / 60.0, 2)
        stale = age_minutes > float(max_age_minutes)

    alerts = record.get("alerts", [])
    cycles = record.get("cycles", [])
    metrics = record.get("metrics", {}) if isinstance(record.get("metrics"), dict) else {}
    ok_cycles = _to_float(metrics.get("reconcile_loop.ok_cycles"))
    completed_cycles = _to_float(metrics.get("reconcile_loop.completed_cycles") or metrics.get("reconcile_loop.total_cycles"))
    latest_cycle = cycles[-1] if isinstance(cycles, list) and cycles else {}
    latest_cycle_ref = str(latest_cycle.get("decision_ref") or "")
    latest_account = latest_cycle.get("account", {}) if isinstance(latest_cycle, dict) else {}
    latest_activity = latest_cycle.get("activity", {}) if isinstance(latest_cycle, dict) else {}
    account_metrics = latest_account.get("metrics", {}) if isinstance(latest_account, dict) else {}
    activity_metrics = latest_activity.get("metrics", {}) if isinstance(latest_activity, dict) else {}

    status = "ok"
    actions: list[str] = []
    summary_parts = [
        f"completed_cycles={int(completed_cycles)}",
        f"ok_cycles={int(ok_cycles)}",
    ]
    if age_minutes is not None:
        summary_parts.append(f"age_minutes={age_minutes}")
    if stale:
        status = "action_required"
        actions.append("rerun reconcile loop because latest audit is stale")
    if alerts:
        status = "action_required"
        actions.append("review latest reconcile alerts and verify account/activity drift")
    if latest_cycle and not bool(latest_cycle.get("ok")):
        status = "action_required"
        actions.append("inspect latest failed cycle and repair upstream exchange sync")
    if not actions:
        actions.append("keep current heartbeat cadence")

    refs = [value for value in [str(record.get("decision_ref") or ""), latest_cycle_ref] if value]
    merged_metrics = {
        "reconcile_loop.ok_cycles": ok_cycles,
        "reconcile_loop.completed_cycles": completed_cycles,
        "account.total_equity_usd": _to_float(account_metrics.get("account.total_equity_usd")),
        "account.available_usdt": _to_float(account_metrics.get("account.available_usdt")),
        "activity.total_trade_count": _to_float(activity_metrics.get("activity.total_trade_count")),
        "activity.total_fee_cost_usdt": _to_float(activity_metrics.get("activity.total_fee_cost_usdt")),
    }
    return BinanceHealthReport(
        status=status,
        decision_ref=str(record.get("decision_ref") or "") or None,
        recorded_at=str(record.get("recorded_at") or "") or None,
        age_minutes=age_minutes,
        venue=str(record.get("venue") or "") or None,
        order_mode=str(record.get("order_mode") or "") or None,
        summary=", ".join(summary_parts),
        actions=actions,
        refs=refs,
        metrics=merged_metrics,
        alerts=alerts if isinstance(alerts, list) else [],
    )
