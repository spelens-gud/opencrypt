from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
import unittest

from opencrew_quant.paper_replay import run_market_making_replay


ROOT = Path(__file__).resolve().parents[1]


class PaperReplayTest(unittest.TestCase):
    def test_market_making_replay_replaces_quotes_on_inventory_shift(self) -> None:
        summary = run_market_making_replay(
            ROOT,
            decision_ref="DEC-REPLAY-001",
            scenario="inventory_refresh",
        )
        self.assertEqual(len(summary.steps), 2)
        first_actions = {action["action"] for action in summary.steps[0].actions}
        second_actions = {action["action"] for action in summary.steps[1].actions}
        self.assertEqual(first_actions, {"place"})
        self.assertIn("replace", second_actions)
        self.assertEqual(len(summary.final_open_orders), 2)
        self.assertTrue(any(event["event_type"] == "quote_replace" for event in summary.audit_events))

    def test_market_making_replay_cancels_quotes_on_stale_riskoff(self) -> None:
        summary = run_market_making_replay(
            ROOT,
            decision_ref="DEC-REPLAY-002",
            scenario="stale_riskoff",
        )
        self.assertEqual(len(summary.steps), 2)
        self.assertEqual(len(summary.steps[0].open_orders), 2)
        self.assertEqual(summary.steps[1].open_orders, [])
        second_actions = {action["action"] for action in summary.steps[1].actions}
        self.assertEqual(second_actions, {"cancel"})
        self.assertTrue(any(alert["title"] == "stale-quote" for alert in summary.alerts))
        self.assertTrue(any(event["event_type"] == "quote_cancel" for event in summary.audit_events))

    def test_cli_run_paper_replay_outputs_json(self) -> None:
        env = dict(PYTHONPATH=str(ROOT / "src"))
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "opencrew_quant",
                "run-paper-replay",
                "--decision-ref",
                "DEC-REPLAY-CLI-001",
                "--scenario",
                "inventory_refresh",
            ],
            cwd=ROOT,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["decision_ref"], "DEC-REPLAY-CLI-001")
        self.assertEqual(payload["scenario"], "inventory_refresh")
        self.assertEqual(len(payload["steps"]), 2)


if __name__ == "__main__":
    unittest.main()
