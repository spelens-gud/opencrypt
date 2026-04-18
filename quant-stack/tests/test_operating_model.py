from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from opencrew_quant.operating_model import (
    build_agent_operating_specs,
    build_market_system_benchmarks,
    build_openclaw_delivery_contract,
    build_strategy_lane_specs,
)


ROOT = Path(__file__).resolve().parents[1]


class OperatingModelTest(unittest.TestCase):
    def test_market_benchmarks_cover_core_reference_systems(self) -> None:
        systems = {item.system for item in build_market_system_benchmarks()}
        self.assertTrue({"Freqtrade", "Hummingbot", "QuantConnect LEAN", "NautilusTrader"}.issubset(systems))

    def test_openclaw_contract_enforces_explicit_thread_mentions(self) -> None:
        contract = build_openclaw_delivery_contract()
        self.assertTrue(contract["slack_defaults"]["thread.requireExplicitMention"])

    def test_agent_specs_include_ops_review_owner(self) -> None:
        specs = {item.agent_id: item for item in build_agent_operating_specs()}
        self.assertEqual(specs["ops"].required_outputs[0], "review_ref")
        self.assertIn("microstructure_mm", specs["builder"].capability_lanes)

    def test_strategy_lanes_cover_execution_and_productized_bots(self) -> None:
        lane_ids = {item.lane_id for item in build_strategy_lane_specs()}
        self.assertTrue({"directional_alpha", "microstructure_mm", "signal_relay", "grid_dca"}.issubset(lane_ids))

    def test_cli_operating_model_outputs_json(self) -> None:
        env = dict(PYTHONPATH=str(ROOT / "src"))
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "opencrew_quant",
                "operating-model",
            ],
            cwd=ROOT,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout)
        self.assertIn("benchmarks", payload)
        self.assertIn("strategy_lanes", payload)
        self.assertIn("agents", payload)
        self.assertIn("openclaw_contract", payload)

    def test_cli_strategy_catalog_outputs_json(self) -> None:
        env = dict(PYTHONPATH=str(ROOT / "src"))
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "opencrew_quant",
                "strategy-catalog",
            ],
            cwd=ROOT,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout)
        self.assertIn("benchmarks", payload)
        self.assertIn("strategy_lanes", payload)
        self.assertGreaterEqual(len(payload["strategy_lanes"]), 5)


if __name__ == "__main__":
    unittest.main()
