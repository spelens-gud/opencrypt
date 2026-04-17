from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
import unittest

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
