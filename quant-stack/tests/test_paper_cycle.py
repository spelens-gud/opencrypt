from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
import unittest

from opencrew_quant.market_data.simulated import SimulatedMarketDataSource, SnapshotSeed
from opencrew_quant.paper_cycle import run_paper_cycle


ROOT = Path(__file__).resolve().parents[1]


class PaperCycleTest(unittest.TestCase):
    def test_trend_follow_cycle_emits_orders(self) -> None:
        summary = run_paper_cycle(ROOT, decision_ref="DEC-TEST-001")
        self.assertEqual(summary.environment, "paper")
        self.assertGreaterEqual(len(summary.orders), 1)
        self.assertTrue(any(event["event_type"] == "paper_order" for event in summary.audit_events))

    def test_mean_reversion_cycle_skips_positive_momentum_symbol(self) -> None:
        summary = run_paper_cycle(
            ROOT,
            decision_ref="DEC-TEST-002",
            strategy_file="mean_reversion.paper.json",
        )
        symbols = {order["symbol"] for order in summary.orders}
        self.assertIn("ETH/USDT:USDT", symbols)
        self.assertNotIn("BTC/USDT:USDT", symbols)

    def test_basis_carry_cycle_emits_hedged_buy_and_sell_orders(self) -> None:
        summary = run_paper_cycle(
            ROOT,
            decision_ref="DEC-TEST-003",
            strategy_file="basis_carry.paper.json",
        )
        order_sides = {order["symbol"]: order["side"] for order in summary.orders}
        self.assertEqual(order_sides["BTC/USDT:USDT"], "sell")
        self.assertEqual(order_sides["ETH/USDT:USDT"], "buy")
        self.assertTrue(any(order["target_weight"] < 0 for order in summary.orders))
        self.assertTrue(any(order["target_weight"] > 0 for order in summary.orders))

    def test_market_making_cycle_emits_two_sided_limit_quotes(self) -> None:
        data_source = SimulatedMarketDataSource.from_seeds(
            [
                SnapshotSeed(
                    symbol="BTC/USDT:USDT",
                    mid_price=68000.0,
                    reference_price=68000.0,
                    funding_rate=0.0,
                    latency_ms=120,
                    best_bid=67986.0,
                    best_ask=68014.0,
                    inventory_ratio=0.2,
                    quote_age_ms=120,
                )
            ]
        )
        summary = run_paper_cycle(
            ROOT,
            decision_ref="DEC-TEST-004",
            strategy_file="market_making.paper.json",
            data_source=data_source,
        )
        self.assertEqual(len(summary.orders), 2)
        order_sides = {order["client_tag"]: order["side"] for order in summary.orders}
        self.assertEqual(order_sides["maker-bid"], "buy")
        self.assertEqual(order_sides["maker-ask"], "sell")
        self.assertTrue(all(order["order_type"] == "limit" for order in summary.orders))
        self.assertTrue(all(order["post_only"] for order in summary.orders))
        maker_bid = next(order for order in summary.orders if order["client_tag"] == "maker-bid")
        maker_ask = next(order for order in summary.orders if order["client_tag"] == "maker-ask")
        self.assertLess(maker_bid["notional_usd"], maker_ask["notional_usd"])

    def test_market_making_cycle_stops_on_stale_orphan_quotes(self) -> None:
        data_source = SimulatedMarketDataSource.from_seeds(
            [
                SnapshotSeed(
                    symbol="BTC/USDT:USDT",
                    mid_price=68000.0,
                    reference_price=68000.0,
                    funding_rate=0.0,
                    latency_ms=150,
                    best_bid=67986.0,
                    best_ask=68014.0,
                    inventory_ratio=0.0,
                    orphan_order_count=1,
                    quote_age_ms=900,
                )
            ]
        )
        summary = run_paper_cycle(
            ROOT,
            decision_ref="DEC-TEST-005",
            strategy_file="market_making.paper.json",
            data_source=data_source,
        )
        self.assertEqual(summary.orders, [])
        alert_types = {alert["title"] for alert in summary.alerts}
        self.assertIn("stale-quote", alert_types)

    def test_cli_run_paper_cycle_outputs_json(self) -> None:
        env = dict(PYTHONPATH=str(ROOT / "src"))
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "opencrew_quant",
                "run-paper-cycle",
                "--decision-ref",
                "DEC-CLI-001",
            ],
            cwd=ROOT,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["decision_ref"], "DEC-CLI-001")
        self.assertEqual(payload["environment"], "paper")


if __name__ == "__main__":
    unittest.main()
