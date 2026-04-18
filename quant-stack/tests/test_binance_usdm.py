from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from opencrew_quant.binance_usdm import (
    BinanceApiError,
    CcxtBinanceUsdmClient,
    create_ccxt_binance_exchange,
    run_binance_cycle,
    run_binance_quote_loop,
    run_binance_reconcile_loop,
    report_binance_health,
    submit_binance_order,
    sync_binance_account,
    sync_binance_activity,
    to_binance_symbol,
)


ROOT = Path(__file__).resolve().parents[1]


class FakeExchange:
    def __init__(self) -> None:
        self.verify = True
        self.urls = {
            "api": {
                "fapiPublic": "https://fapi.binance.com",
                "fapiPrivate": "https://fapi.binance.com",
            }
        }
        self.sandbox_enabled = False
        self.demo_enabled = False
        self.loaded = False
        self.orders: list[dict[str, object]] = []
        self.cancelled_orders: list[dict[str, object]] = []
        self.options: dict[str, object] = {}

    def set_sandbox_mode(self, enabled: bool) -> None:
        self.sandbox_enabled = enabled

    def enable_demo_trading(self, enabled: bool) -> None:
        self.demo_enabled = enabled
        if enabled:
            self.urls["api"]["fapiPublic"] = "https://demo-fapi.binance.com/fapi/v1"
            self.urls["api"]["fapiPrivate"] = "https://demo-fapi.binance.com/fapi/v1"

    def load_markets(self) -> dict[str, object]:
        self.loaded = True
        return {}

    def market(self, symbol: str) -> dict[str, object]:
        return {
            "symbol": symbol,
            "limits": {
                "cost": {
                    "min": 50.0,
                }
            },
            "info": {
                "filters": [
                    {
                        "filterType": "MIN_NOTIONAL",
                        "minNotional": "50",
                    }
                ]
            },
        }

    def amount_to_precision(self, symbol: str, amount: float) -> str:
        return f"{amount:.3f}"

    def fetch_ticker(self, symbol: str) -> dict[str, object]:
        if symbol == "BTC/USDT:USDT":
            return {"symbol": symbol, "bid": 68000.0, "ask": 68010.0, "last": 68005.0, "info": {}}
        return {"symbol": symbol, "bid": 3450.0, "ask": 3452.0, "last": 3451.0, "info": {}}

    def fetch_funding_rate(self, symbol: str) -> dict[str, object]:
        if symbol == "BTC/USDT:USDT":
            return {"fundingRate": 0.0001, "markPrice": 67950.0}
        return {"fundingRate": 0.0002, "markPrice": 3460.0}

    def create_order(
        self,
        symbol: str,
        order_type: str,
        side: str,
        amount: float,
        price: float | None = None,
        params: dict[str, object] | None = None,
    ) -> dict[str, object]:
        order = {
            "id": f"fake-{len(self.orders) + 1}",
            "clientOrderId": (params or {}).get("newClientOrderId", ""),
            "symbol": symbol,
            "type": order_type,
            "side": side,
            "amount": amount,
            "price": price,
            "params": params or {},
        }
        self.orders.append(order)
        return order

    def cancel_order(
        self,
        id: str,
        symbol: str | None = None,
        params: dict[str, object] | None = None,
    ) -> dict[str, object]:
        payload = {"id": id, "symbol": symbol or "", "params": params or {}}
        self.cancelled_orders.append(payload)
        return payload

    def fetch_balance(self, params: dict[str, object] | None = None) -> dict[str, object]:
        return {
            "info": {
                "positions": [
                    {
                        "symbol": "BTCUSDT",
                        "positionAmt": "0.0022",
                        "notional": "149.61",
                    }
                ]
            },
            "USDT": {"free": 4900.0, "used": 100.0, "total": 5000.0},
            "USDC": {"free": 5000.0, "used": 0.0, "total": 5000.0},
            "BTC": {"free": 0.01, "used": 0.0, "total": 0.01},
            "timestamp": None,
        }

    def fetch_positions(
        self,
        symbols: list[str] | None = None,
        params: dict[str, object] | None = None,
    ) -> list[dict[str, object]]:
        return [
            {
                "symbol": "BTC/USDT:USDT",
                "side": "long",
                "contracts": 0.0022,
                "entryPrice": 68000.0,
                "markPrice": 67950.0,
                "notional": 149.61,
                "unrealizedPnl": -0.11,
                "marginMode": "cross",
                "percentage": -0.7,
                "timestamp": 1776422110332,
            }
        ]

    def fetch_open_orders(
        self,
        symbol: str | None = None,
        since: int | None = None,
        limit: int | None = None,
        params: dict[str, object] | None = None,
    ) -> list[dict[str, object]]:
        return [
            {
                "id": "open-1",
                "symbol": "ETH/USDT:USDT",
                "side": "sell",
                "type": "limit",
                "status": "open",
                "amount": 0.1,
                "remaining": 0.1,
                "price": 3600.0,
                "timestamp": 1776422110999,
                "info": {"reduceOnly": True},
            }
        ]

    def fetch_my_trades(
        self,
        symbol: str | None = None,
        since: int | None = None,
        limit: int | None = None,
        params: dict[str, object] | None = None,
    ) -> list[dict[str, object]]:
        return [
            {
                "id": "trade-1",
                "order": "closed-1",
                "symbol": symbol or "BTC/USDT:USDT",
                "side": "buy",
                "takerOrMaker": "taker",
                "price": 68000.0,
                "amount": 0.002,
                "cost": 136.0,
                "timestamp": 1776422110000,
                "fee": {"currency": "USDT", "cost": 0.0544},
            }
        ]

    def fetch_orders(
        self,
        symbol: str | None = None,
        since: int | None = None,
        limit: int | None = None,
        params: dict[str, object] | None = None,
    ) -> list[dict[str, object]]:
        return [
            {
                "id": "closed-1",
                "clientOrderId": "client-1",
                "symbol": symbol or "BTC/USDT:USDT",
                "side": "buy",
                "type": "market",
                "status": "closed",
                "price": 68000.0,
                "amount": 0.002,
                "filled": 0.002,
                "remaining": 0.0,
                "cost": 136.0,
                "average": 68000.0,
                "reduceOnly": False,
                "timestamp": 1776422110000,
            }
        ]


class BinanceUsdmTest(unittest.TestCase):
    def test_run_binance_reconcile_loop_runs_multiple_iterations(self) -> None:
        client = CcxtBinanceUsdmClient(exchange=FakeExchange(), order_mode="test")
        sleeps: list[int] = []
        summary = run_binance_reconcile_loop(
            ROOT,
            decision_ref="DEC-BINANCE-LOOP-001",
            order_mode="test",
            symbol="BTC/USDT:USDT",
            limit=5,
            iterations=2,
            interval_s=1,
            client=client,
            sleeper=sleeps.append,
        )
        self.assertEqual(summary.iterations, 2)
        self.assertEqual(len(summary.cycles), 2)
        self.assertEqual(sleeps, [1])
        self.assertTrue(all(cycle["ok"] for cycle in summary.cycles))

    def test_run_binance_reconcile_loop_continues_after_transient_failure(self) -> None:
        class FlakyExchange(FakeExchange):
            def __init__(self) -> None:
                super().__init__()
                self.calls = 0

            def fetch_balance(self, params: dict[str, object] | None = None) -> dict[str, object]:
                self.calls += 1
                if self.calls == 1:
                    raise RuntimeError("temporary balance failure")
                return super().fetch_balance(params)

        client = CcxtBinanceUsdmClient(exchange=FlakyExchange(), order_mode="test")
        summary = run_binance_reconcile_loop(
            ROOT,
            decision_ref="DEC-BINANCE-LOOP-FLAKY",
            order_mode="test",
            symbol="BTC/USDT:USDT",
            limit=5,
            iterations=2,
            interval_s=0,
            max_consecutive_failures=2,
            client=client,
        )
        self.assertEqual(len(summary.cycles), 2)
        self.assertFalse(summary.cycles[0]["ok"])
        self.assertTrue(summary.cycles[1]["ok"])
        self.assertTrue(any(alert["title"] == "reconcile-cycle-error" for alert in summary.alerts))

    def test_run_binance_reconcile_loop_stops_after_consecutive_failures(self) -> None:
        class BrokenExchange(FakeExchange):
            def fetch_balance(self, params: dict[str, object] | None = None) -> dict[str, object]:
                raise RuntimeError("permanent balance failure")

        client = CcxtBinanceUsdmClient(exchange=BrokenExchange(), order_mode="test")
        summary = run_binance_reconcile_loop(
            ROOT,
            decision_ref="DEC-BINANCE-LOOP-BROKEN",
            order_mode="test",
            symbol="BTC/USDT:USDT",
            limit=5,
            iterations=3,
            interval_s=0,
            max_consecutive_failures=1,
            client=client,
        )
        self.assertEqual(len(summary.cycles), 1)
        self.assertFalse(summary.cycles[0]["ok"])
        self.assertTrue(any(alert["title"] == "reconcile-loop-stopped" for alert in summary.alerts))

    def test_sync_commands_persist_jsonl_records(self) -> None:
        client = CcxtBinanceUsdmClient(exchange=FakeExchange(), order_mode="test")
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_dir = Path(tmpdir)
            sync_binance_account(
                ROOT,
                decision_ref="DEC-BINANCE-PERSIST-ACCOUNT",
                order_mode="test",
                audit_dir=audit_dir,
                client=client,
            )
            sync_binance_activity(
                ROOT,
                decision_ref="DEC-BINANCE-PERSIST-ACTIVITY",
                order_mode="test",
                symbol="BTC/USDT:USDT",
                limit=5,
                audit_dir=audit_dir,
                client=client,
            )
            run_binance_reconcile_loop(
                ROOT,
                decision_ref="DEC-BINANCE-PERSIST-LOOP",
                order_mode="test",
                symbol="BTC/USDT:USDT",
                limit=5,
                iterations=1,
                interval_s=0,
                audit_dir=audit_dir,
                client=client,
            )
            account_lines = (audit_dir / "account_snapshots.jsonl").read_text(encoding="utf-8").strip().splitlines()
            activity_lines = (audit_dir / "activity_snapshots.jsonl").read_text(encoding="utf-8").strip().splitlines()
            loop_lines = (audit_dir / "reconcile_loops.jsonl").read_text(encoding="utf-8").strip().splitlines()
            self.assertGreaterEqual(len(account_lines), 2)
            self.assertGreaterEqual(len(activity_lines), 2)
            self.assertEqual(len(loop_lines), 1)
            persisted_loop = json.loads(loop_lines[0])
            self.assertEqual(persisted_loop["decision_ref"], "DEC-BINANCE-PERSIST-LOOP")

    def test_report_binance_health_reads_latest_reconcile_loop(self) -> None:
        client = CcxtBinanceUsdmClient(exchange=FakeExchange(), order_mode="test")
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_dir = Path(tmpdir)
            run_binance_reconcile_loop(
                ROOT,
                decision_ref="DEC-BINANCE-HEALTH-001",
                order_mode="test",
                symbol="BTC/USDT:USDT",
                limit=5,
                iterations=1,
                interval_s=0,
                audit_dir=audit_dir,
                client=client,
            )
            report = report_binance_health(ROOT, max_age_minutes=30, audit_dir=audit_dir)
            self.assertEqual(report.status, "ok")
            self.assertEqual(report.decision_ref, "DEC-BINANCE-HEALTH-001")
            self.assertTrue(any(ref.startswith("DEC-BINANCE-HEALTH-001") for ref in report.refs))

    def test_report_binance_health_requires_action_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            report = report_binance_health(ROOT, max_age_minutes=30, audit_dir=tmpdir)
            self.assertEqual(report.status, "action_required")
            self.assertTrue(any(alert["title"] == "missing-audit" for alert in report.alerts))

    def test_sync_binance_activity_returns_trades_and_orders(self) -> None:
        client = CcxtBinanceUsdmClient(exchange=FakeExchange(), order_mode="test")
        summary = sync_binance_activity(
            ROOT,
            decision_ref="DEC-BINANCE-ACTIVITY-001",
            order_mode="test",
            symbol="BTC/USDT:USDT",
            limit=5,
            client=client,
        )
        self.assertTrue(summary.reconcile["ok"])
        self.assertEqual(summary.trades[0]["trade_id"], "trade-1")
        self.assertEqual(summary.orders[0]["order_id"], "closed-1")
        self.assertEqual(summary.audit_events[0]["event_type"], "activity_snapshot")

    def test_sync_binance_account_returns_snapshot(self) -> None:
        client = CcxtBinanceUsdmClient(exchange=FakeExchange(), order_mode="test")
        summary = sync_binance_account(ROOT, decision_ref="DEC-BINANCE-SYNC-001", order_mode="test", client=client)
        self.assertTrue(summary.reconcile["ok"])
        self.assertTrue(any(item["asset"] == "USDT" for item in summary.balances))
        self.assertEqual(summary.positions[0]["symbol"], "BTC/USDT:USDT")
        self.assertEqual(summary.open_orders[0]["order_id"], "open-1")
        self.assertEqual(summary.audit_events[0]["event_type"], "account_snapshot")

    def test_symbol_conversion(self) -> None:
        self.assertEqual(to_binance_symbol("BTC/USDT:USDT"), "BTCUSDT")

    def test_preview_cycle_with_fake_exchange(self) -> None:
        client = CcxtBinanceUsdmClient(exchange=FakeExchange(), order_mode="preview")
        summary = run_binance_cycle(
            ROOT,
            decision_ref="DEC-BINANCE-001",
            order_mode="preview",
            client=client,
        )
        self.assertEqual(summary.order_mode, "preview")
        self.assertGreaterEqual(len(summary.orders), 1)
        self.assertTrue(any(event["event_type"] == "binance_preview_order" for event in summary.audit_events))

    def test_test_cycle_submits_ccxt_order(self) -> None:
        exchange = FakeExchange()
        exchange.enable_demo_trading(True)
        client = CcxtBinanceUsdmClient(exchange=exchange, order_mode="test")
        summary = run_binance_cycle(
            ROOT,
            decision_ref="DEC-BINANCE-002",
            order_mode="test",
            client=client,
        )
        self.assertGreaterEqual(len(summary.orders), 1)
        self.assertTrue(exchange.demo_enabled)
        self.assertEqual(exchange.orders[0]["type"], "market")
        self.assertEqual(exchange.orders[0]["side"], "buy")

    def test_basis_carry_preview_cycle_emits_buy_and_sell_orders(self) -> None:
        class BasisCarryExchange(FakeExchange):
            def fetch_funding_rate(self, symbol: str) -> dict[str, object]:
                if symbol == "BTC/USDT:USDT":
                    return {"fundingRate": 0.0002, "markPrice": 66500.0}
                return {"fundingRate": 0.0001, "markPrice": 3490.0}

        client = CcxtBinanceUsdmClient(exchange=BasisCarryExchange(), order_mode="preview")
        summary = run_binance_cycle(
            ROOT,
            decision_ref="DEC-BINANCE-BASIS-001",
            strategy_file="basis_carry.paper.json",
            order_mode="preview",
            client=client,
        )
        sides = {order["symbol"]: order["side"] for order in summary.orders}
        self.assertEqual(sides["BTC/USDT:USDT"], "sell")
        self.assertEqual(sides["ETH/USDT:USDT"], "buy")
        self.assertTrue(any(event["payload"].get("side") == "sell" for event in summary.audit_events))

    def test_market_making_preview_cycle_emits_two_sided_limit_quotes(self) -> None:
        class MarketMakingExchange(FakeExchange):
            def fetch_ticker(self, symbol: str) -> dict[str, object]:
                return {"symbol": symbol, "bid": 67986.0, "ask": 68014.0, "last": 68000.0, "info": {"latency": 120}}

            def fetch_open_orders(
                self,
                symbol: str | None = None,
                since: int | None = None,
                limit: int | None = None,
                params: dict[str, object] | None = None,
            ) -> list[dict[str, object]]:
                return []

        client = CcxtBinanceUsdmClient(exchange=MarketMakingExchange(), order_mode="preview")
        summary = run_binance_cycle(
            ROOT,
            decision_ref="DEC-BINANCE-MM-001",
            strategy_file="market_making.paper.json",
            order_mode="preview",
            client=client,
        )
        self.assertEqual(len(summary.orders), 2)
        self.assertTrue(all(order["order_type"] == "limit" for order in summary.orders))
        self.assertTrue(all(order["post_only"] for order in summary.orders))
        self.assertEqual({order["client_tag"] for order in summary.orders}, {"maker-bid", "maker-ask"})
        self.assertTrue(any(event["event_type"] == "binance_preview_quote_order" for event in summary.audit_events))

    def test_market_making_test_cycle_replaces_existing_quotes(self) -> None:
        class ReplaceQuoteExchange(FakeExchange):
            def fetch_ticker(self, symbol: str) -> dict[str, object]:
                return {"symbol": symbol, "bid": 67982.0, "ask": 68028.0, "last": 68005.0, "info": {"latency": 140}}

            def fetch_open_orders(
                self,
                symbol: str | None = None,
                since: int | None = None,
                limit: int | None = None,
                params: dict[str, object] | None = None,
            ) -> list[dict[str, object]]:
                return [
                    {
                        "id": "open-bid-1",
                        "clientOrderId": "maker-bid",
                        "symbol": symbol or "BTC/USDT:USDT",
                        "side": "buy",
                        "type": "limit",
                        "status": "open",
                        "amount": 0.044,
                        "remaining": 0.044,
                        "price": 67995.0,
                        "timestamp": 1776422110999,
                        "info": {"reduceOnly": False, "postOnly": True, "timeInForce": "GTX", "clientOrderId": "maker-bid"},
                    },
                    {
                        "id": "open-ask-1",
                        "clientOrderId": "maker-ask",
                        "symbol": symbol or "BTC/USDT:USDT",
                        "side": "sell",
                        "type": "limit",
                        "status": "open",
                        "amount": 0.046,
                        "remaining": 0.046,
                        "price": 68005.0,
                        "timestamp": 1776422111000,
                        "info": {"reduceOnly": False, "postOnly": True, "timeInForce": "GTX", "clientOrderId": "maker-ask"},
                    },
                ]

        exchange = ReplaceQuoteExchange()
        exchange.enable_demo_trading(True)
        client = CcxtBinanceUsdmClient(exchange=exchange, order_mode="test")
        summary = run_binance_cycle(
            ROOT,
            decision_ref="DEC-BINANCE-MM-002",
            strategy_file="market_making.paper.json",
            order_mode="test",
            client=client,
        )
        self.assertEqual(len(exchange.cancelled_orders), 2)
        self.assertEqual(len(exchange.orders), 2)
        self.assertTrue(all(order["type"] == "limit" for order in exchange.orders))
        self.assertTrue(all(order["params"].get("postOnly") for order in exchange.orders))
        self.assertEqual({order["params"].get("newClientOrderId") for order in exchange.orders}, {"maker-bid", "maker-ask"})
        self.assertTrue(all(item["action"] == "replace" for item in summary.orders))
        self.assertTrue(any(event["event_type"] == "binance_test_quote_cancel" for event in summary.audit_events))

    def test_market_making_test_cycle_cancels_quotes_on_stale_riskoff(self) -> None:
        class StaleQuoteExchange(FakeExchange):
            def fetch_ticker(self, symbol: str) -> dict[str, object]:
                return {"symbol": symbol, "bid": 67990.0, "ask": 68050.0, "last": 68020.0, "info": {"latency": 900}}

            def fetch_open_orders(
                self,
                symbol: str | None = None,
                since: int | None = None,
                limit: int | None = None,
                params: dict[str, object] | None = None,
            ) -> list[dict[str, object]]:
                return [
                    {
                        "id": "open-bid-1",
                        "clientOrderId": "maker-bid",
                        "symbol": symbol or "BTC/USDT:USDT",
                        "side": "buy",
                        "type": "limit",
                        "status": "open",
                        "amount": 0.044,
                        "remaining": 0.044,
                        "price": 67979.2,
                        "timestamp": 1776422110999,
                        "info": {"reduceOnly": False, "postOnly": True, "timeInForce": "GTX", "clientOrderId": "maker-bid"},
                    },
                    {
                        "id": "open-ask-1",
                        "clientOrderId": "maker-ask",
                        "symbol": symbol or "BTC/USDT:USDT",
                        "side": "sell",
                        "type": "limit",
                        "status": "open",
                        "amount": 0.044,
                        "remaining": 0.044,
                        "price": 68020.8,
                        "timestamp": 1776422111000,
                        "info": {"reduceOnly": False, "postOnly": True, "timeInForce": "GTX", "clientOrderId": "maker-ask"},
                    },
                ]

        exchange = StaleQuoteExchange()
        exchange.enable_demo_trading(True)
        client = CcxtBinanceUsdmClient(exchange=exchange, order_mode="test")
        summary = run_binance_cycle(
            ROOT,
            decision_ref="DEC-BINANCE-MM-003",
            strategy_file="market_making.paper.json",
            order_mode="test",
            client=client,
        )
        self.assertEqual(summary.orders, [])
        self.assertEqual(len(exchange.cancelled_orders), 2)
        self.assertEqual(len(exchange.orders), 0)
        self.assertTrue(any(alert["title"] == "stale-quote" for alert in summary.alerts))

    def test_run_binance_quote_loop_preview_replaces_quotes_across_iterations(self) -> None:
        class PreviewLoopExchange(FakeExchange):
            def __init__(self) -> None:
                super().__init__()
                self.ticker_calls = 0

            def fetch_ticker(self, symbol: str) -> dict[str, object]:
                self.ticker_calls += 1
                if self.ticker_calls == 1:
                    return {"symbol": symbol, "bid": 67986.0, "ask": 68014.0, "last": 68000.0, "info": {"latency": 120}}
                return {"symbol": symbol, "bid": 67982.0, "ask": 68028.0, "last": 68005.0, "info": {"latency": 140}}

        client = CcxtBinanceUsdmClient(exchange=PreviewLoopExchange(), order_mode="preview")
        sleeps: list[int] = []
        summary = run_binance_quote_loop(
            ROOT,
            decision_ref="DEC-BINANCE-QUOTE-LOOP-001",
            order_mode="preview",
            iterations=2,
            interval_s=1,
            client=client,
            sleeper=sleeps.append,
        )
        self.assertEqual(summary.iterations, 2)
        self.assertEqual(len(summary.cycles), 2)
        self.assertEqual(sleeps, [1])
        self.assertTrue(all(cycle["ok"] for cycle in summary.cycles))
        self.assertTrue(all(order["action"] == "place" for order in summary.cycles[0]["orders"]))
        self.assertTrue(any(order["action"] == "replace" for order in summary.cycles[1]["orders"]))
        self.assertTrue(any(order["action"] == "keep" for order in summary.cycles[1]["orders"]))
        self.assertEqual(summary.cycles[0]["open_order_count"], 2)
        self.assertEqual(summary.cycles[1]["open_order_count"], 2)

    def test_run_binance_quote_loop_test_mode_cancels_on_riskoff(self) -> None:
        class QuoteLoopStaleExchange(FakeExchange):
            def __init__(self) -> None:
                super().__init__()
                self.ticker_calls = 0

            def fetch_ticker(self, symbol: str) -> dict[str, object]:
                self.ticker_calls += 1
                if self.ticker_calls == 1:
                    return {"symbol": symbol, "bid": 67986.0, "ask": 68014.0, "last": 68000.0, "info": {"latency": 120}}
                return {"symbol": symbol, "bid": 67990.0, "ask": 68050.0, "last": 68020.0, "info": {"latency": 900}}

            def fetch_open_orders(
                self,
                symbol: str | None = None,
                since: int | None = None,
                limit: int | None = None,
                params: dict[str, object] | None = None,
            ) -> list[dict[str, object]]:
                if self.ticker_calls <= 1:
                    return []
                return [
                    {
                        "id": "open-bid-1",
                        "clientOrderId": "maker-bid",
                        "symbol": symbol or "BTC/USDT:USDT",
                        "side": "buy",
                        "type": "limit",
                        "status": "open",
                        "amount": 0.044,
                        "remaining": 0.044,
                        "price": 67979.2,
                        "timestamp": 1776422110999,
                        "info": {"reduceOnly": False, "postOnly": True, "timeInForce": "GTX", "clientOrderId": "maker-bid"},
                    },
                    {
                        "id": "open-ask-1",
                        "clientOrderId": "maker-ask",
                        "symbol": symbol or "BTC/USDT:USDT",
                        "side": "sell",
                        "type": "limit",
                        "status": "open",
                        "amount": 0.044,
                        "remaining": 0.044,
                        "price": 68020.8,
                        "timestamp": 1776422111000,
                        "info": {"reduceOnly": False, "postOnly": True, "timeInForce": "GTX", "clientOrderId": "maker-ask"},
                    },
                ]

        exchange = QuoteLoopStaleExchange()
        exchange.enable_demo_trading(True)
        client = CcxtBinanceUsdmClient(exchange=exchange, order_mode="test")
        summary = run_binance_quote_loop(
            ROOT,
            decision_ref="DEC-BINANCE-QUOTE-LOOP-002",
            order_mode="test",
            iterations=2,
            interval_s=0,
            client=client,
        )
        self.assertEqual(len(summary.cycles), 2)
        self.assertTrue(summary.cycles[0]["ok"])
        self.assertFalse(summary.cycles[1]["ok"])
        self.assertEqual(len(exchange.orders), 2)
        self.assertEqual(len(exchange.cancelled_orders), 2)
        self.assertTrue(any(alert["title"] == "quote-loop-alert" for alert in summary.alerts))

    def test_quantize_amount_uses_exchange_precision(self) -> None:
        client = CcxtBinanceUsdmClient(exchange=FakeExchange(), order_mode="preview")
        self.assertEqual(client.quantize_amount("BTC/USDT:USDT", 0.123456), 0.123)

    def test_min_notional_uses_market_limits(self) -> None:
        client = CcxtBinanceUsdmClient(exchange=FakeExchange(), order_mode="preview")
        self.assertEqual(client.min_notional_usd("BTC/USDT:USDT"), 50.0)

    def test_submit_binance_order_rejects_below_min_notional(self) -> None:
        exchange = FakeExchange()
        exchange.enable_demo_trading(True)
        client = CcxtBinanceUsdmClient(exchange=exchange, order_mode="test")
        summary = submit_binance_order(
            ROOT,
            decision_ref="DEC-BINANCE-LOW-NOTIONAL",
            symbol="ETH/USDT:USDT",
            notional_usd=25.0,
            order_mode="test",
            client=client,
        )
        self.assertIsNone(summary.order)
        self.assertEqual(len(exchange.orders), 0)
        self.assertTrue(any(alert["title"] == "risk-rejected" for alert in summary.alerts))
        self.assertEqual(summary.audit_events[0]["payload"]["reason"], "min-notional-breach")

    def test_submit_binance_order_submits_minimum_order(self) -> None:
        exchange = FakeExchange()
        exchange.enable_demo_trading(True)
        client = CcxtBinanceUsdmClient(exchange=exchange, order_mode="test")
        summary = submit_binance_order(
            ROOT,
            decision_ref="DEC-BINANCE-003",
            symbol="ETH/USDT:USDT",
            notional_usd=250.0,
            order_mode="test",
            client=client,
        )
        self.assertIsNotNone(summary.order)
        self.assertEqual(summary.order["side"], "buy")
        self.assertEqual(summary.order["notional_usd"], 250.0)
        self.assertEqual(exchange.orders[0]["type"], "market")

    def test_sync_binance_account_emits_reconcile_alert_when_symbols_diverge(self) -> None:
        class DivergedExchange(FakeExchange):
            def fetch_positions(
                self,
                symbols: list[str] | None = None,
                params: dict[str, object] | None = None,
            ) -> list[dict[str, object]]:
                return []

        client = CcxtBinanceUsdmClient(exchange=DivergedExchange(), order_mode="test")
        summary = sync_binance_account(ROOT, decision_ref="DEC-BINANCE-SYNC-002", order_mode="test", client=client)
        self.assertFalse(summary.reconcile["ok"])
        self.assertEqual(summary.reconcile["missing_in_positions"], ["BTCUSDT"])
        self.assertTrue(any(alert["title"] == "reconcile-gap" for alert in summary.alerts))

    def test_sync_binance_activity_emits_gap_when_trade_order_missing(self) -> None:
        class DivergedActivityExchange(FakeExchange):
            def fetch_orders(
                self,
                symbol: str | None = None,
                since: int | None = None,
                limit: int | None = None,
                params: dict[str, object] | None = None,
            ) -> list[dict[str, object]]:
                return []

        client = CcxtBinanceUsdmClient(exchange=DivergedActivityExchange(), order_mode="test")
        summary = sync_binance_activity(
            ROOT,
            decision_ref="DEC-BINANCE-ACTIVITY-002",
            order_mode="test",
            symbol="BTC/USDT:USDT",
            limit=5,
            client=client,
        )
        self.assertFalse(summary.reconcile["ok"])
        self.assertEqual(summary.reconcile["missing_order_ids"], ["closed-1"])
        self.assertTrue(any(alert["title"] == "activity-reconcile-gap" for alert in summary.alerts))

    def test_create_exchange_requires_ccxt(self) -> None:
        try:
            create_ccxt_binance_exchange(order_mode="preview", api_key=None, api_secret=None)
        except RuntimeError as exc:
            if "ccxt 未安装" in str(exc):
                self.assertIn("ccxt", str(exc))
            else:
                self.assertNotIsInstance(exc, BinanceApiError)


if __name__ == "__main__":
    unittest.main()
