from __future__ import annotations

import json
import argparse
import os
from pathlib import Path

from .config import load_stack_config
from .binance_usdm import (
    run_binance_cycle,
    submit_binance_order,
    sync_binance_account,
    sync_binance_activity,
    run_binance_reconcile_loop,
    report_binance_health,
)
from .domain.models import Side
from .paper_cycle import run_paper_cycle
from .pipeline import STAGE_ORDER, describe_stage_gates


def build_system_blueprint() -> dict[str, list[str]]:
    return {
        "market_data": ["market-feed", "account-feed", "freshness-check"],
        "signal_engine": ["regime-router", "signal-engine", "parameter-store"],
        "portfolio_engine": ["allocation-engine", "position-targeting"],
        "execution_gateway": ["venue-adapter", "order-manager", "reconcile-loop"],
        "risk_engine": ["pre-trade-checks", "loss-cap", "kill-switch"],
        "audit_log": ["order-log", "fill-log", "risk-snapshot-log"],
        "observability": ["metrics", "alerts", "replay-traces"],
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="opencrew_quant")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("blueprint")

    run_cycle = subparsers.add_parser("run-paper-cycle")
    run_cycle.add_argument("--decision-ref", required=True)
    run_cycle.add_argument(
        "--strategy-file",
        default="trend_follow.paper.json",
        choices=["trend_follow.paper.json", "mean_reversion.paper.json"],
    )
    run_cycle.add_argument("--nav-usd", type=float, default=100000.0)

    run_binance = subparsers.add_parser("run-binance-cycle")
    run_binance.add_argument("--decision-ref", required=True)
    run_binance.add_argument(
        "--strategy-file",
        default="trend_follow.paper.json",
        choices=["trend_follow.paper.json", "mean_reversion.paper.json"],
    )
    run_binance.add_argument("--nav-usd", type=float, default=100000.0)
    run_binance.add_argument(
        "--order-mode",
        default="preview",
        choices=["preview", "test", "live"],
    )

    submit_binance = subparsers.add_parser("submit-binance-order")
    submit_binance.add_argument("--decision-ref", required=True)
    submit_binance.add_argument("--symbol", default="BTC/USDT:USDT")
    submit_binance.add_argument("--notional-usd", type=float, default=25.0)
    submit_binance.add_argument("--side", default="buy", choices=["buy", "sell"])
    submit_binance.add_argument(
        "--order-mode",
        default="test",
        choices=["preview", "test", "live"],
    )

    sync_binance = subparsers.add_parser("sync-binance-account")
    sync_binance.add_argument("--decision-ref", required=True)
    sync_binance.add_argument(
        "--order-mode",
        default="test",
        choices=["test", "live"],
    )
    sync_binance.add_argument("--audit-dir")

    sync_activity = subparsers.add_parser("sync-binance-activity")
    sync_activity.add_argument("--decision-ref", required=True)
    sync_activity.add_argument(
        "--strategy-file",
        default="trend_follow.paper.json",
        choices=["trend_follow.paper.json", "mean_reversion.paper.json"],
    )
    sync_activity.add_argument("--symbol")
    sync_activity.add_argument("--limit", type=int, default=20)
    sync_activity.add_argument(
        "--order-mode",
        default="test",
        choices=["test", "live"],
    )
    sync_activity.add_argument("--audit-dir")

    reconcile_loop = subparsers.add_parser("run-binance-reconcile-loop")
    reconcile_loop.add_argument("--decision-ref", required=True)
    reconcile_loop.add_argument(
        "--strategy-file",
        default="trend_follow.paper.json",
        choices=["trend_follow.paper.json", "mean_reversion.paper.json"],
    )
    reconcile_loop.add_argument("--symbol")
    reconcile_loop.add_argument("--limit", type=int, default=20)
    reconcile_loop.add_argument("--iterations", type=int, default=1)
    reconcile_loop.add_argument("--interval-s", type=int)
    reconcile_loop.add_argument("--max-consecutive-failures", type=int, default=3)
    reconcile_loop.add_argument(
        "--order-mode",
        default="test",
        choices=["test", "live"],
    )
    reconcile_loop.add_argument("--audit-dir")

    report_health = subparsers.add_parser("report-binance-health")
    report_health.add_argument("--max-age-minutes", type=int, default=30)
    report_health.add_argument("--audit-dir")
    return parser


def main(argv: list[str] | None = None) -> int:
    root = Path(__file__).resolve().parents[2]
    parser = _build_parser()
    args = parser.parse_args(argv)

    sample_config = root / "configs" / "paper" / "core-stack.json"
    stack = load_stack_config(sample_config)
    if args.command in (None, "blueprint"):
        output = {
            "system": build_system_blueprint(),
            "stage_order": STAGE_ORDER,
            "stage_gates": describe_stage_gates(),
            "sample_config": stack.to_dict(),
        }
    elif args.command == "run-paper-cycle":
        summary = run_paper_cycle(
            root=root,
            decision_ref=args.decision_ref,
            strategy_file=args.strategy_file,
            nav_usd=args.nav_usd,
        )
        output = summary.to_dict()
    elif args.command == "run-binance-cycle":
        if args.order_mode == "live" and (
            not os.getenv("BINANCE_API_KEY") or not os.getenv("BINANCE_API_SECRET")
        ):
            parser.error("run-binance-cycle 在 live 模式下需要设置 BINANCE_API_KEY 和 BINANCE_API_SECRET")
        if args.order_mode == "test":
            test_key = os.getenv("BINANCE_DEMO_API_KEY") or os.getenv("BINANCE_API_KEY")
            test_secret = os.getenv("BINANCE_DEMO_API_SECRET") or os.getenv("BINANCE_API_SECRET")
            if not test_key or not test_secret:
                parser.error(
                    "run-binance-cycle 在 test 模式下需要设置 BINANCE_DEMO_API_KEY/BINANCE_DEMO_API_SECRET，"
                    "或回退使用 BINANCE_API_KEY/BINANCE_API_SECRET"
                )
        summary = run_binance_cycle(
            root=root,
            decision_ref=args.decision_ref,
            strategy_file=args.strategy_file,
            nav_usd=args.nav_usd,
            order_mode=args.order_mode,
        )
        output = summary.to_dict()
    elif args.command == "submit-binance-order":
        if args.order_mode == "live" and (
            not os.getenv("BINANCE_API_KEY") or not os.getenv("BINANCE_API_SECRET")
        ):
            parser.error("submit-binance-order 在 live 模式下需要设置 BINANCE_API_KEY 和 BINANCE_API_SECRET")
        if args.order_mode == "test":
            test_key = os.getenv("BINANCE_DEMO_API_KEY") or os.getenv("BINANCE_API_KEY")
            test_secret = os.getenv("BINANCE_DEMO_API_SECRET") or os.getenv("BINANCE_API_SECRET")
            if not test_key or not test_secret:
                parser.error(
                    "submit-binance-order 在 test 模式下需要设置 BINANCE_DEMO_API_KEY/BINANCE_DEMO_API_SECRET，"
                    "或回退使用 BINANCE_API_KEY/BINANCE_API_SECRET"
                )
        summary = submit_binance_order(
            root=root,
            decision_ref=args.decision_ref,
            symbol=args.symbol,
            notional_usd=args.notional_usd,
            side=Side(args.side),
            order_mode=args.order_mode,
        )
        output = summary.to_dict()
    elif args.command == "sync-binance-account":
        if args.order_mode == "live" and (
            not os.getenv("BINANCE_API_KEY") or not os.getenv("BINANCE_API_SECRET")
        ):
            parser.error("sync-binance-account 在 live 模式下需要设置 BINANCE_API_KEY 和 BINANCE_API_SECRET")
        if args.order_mode == "test":
            test_key = os.getenv("BINANCE_DEMO_API_KEY") or os.getenv("BINANCE_API_KEY")
            test_secret = os.getenv("BINANCE_DEMO_API_SECRET") or os.getenv("BINANCE_API_SECRET")
            if not test_key or not test_secret:
                parser.error(
                    "sync-binance-account 在 test 模式下需要设置 BINANCE_DEMO_API_KEY/BINANCE_DEMO_API_SECRET，"
                    "或回退使用 BINANCE_API_KEY/BINANCE_API_SECRET"
                )
        summary = sync_binance_account(
            root=root,
            decision_ref=args.decision_ref,
            order_mode=args.order_mode,
            audit_dir=args.audit_dir,
        )
        output = summary.to_dict()
    elif args.command == "sync-binance-activity":
        if args.order_mode == "live" and (
            not os.getenv("BINANCE_API_KEY") or not os.getenv("BINANCE_API_SECRET")
        ):
            parser.error("sync-binance-activity 在 live 模式下需要设置 BINANCE_API_KEY 和 BINANCE_API_SECRET")
        if args.order_mode == "test":
            test_key = os.getenv("BINANCE_DEMO_API_KEY") or os.getenv("BINANCE_API_KEY")
            test_secret = os.getenv("BINANCE_DEMO_API_SECRET") or os.getenv("BINANCE_API_SECRET")
            if not test_key or not test_secret:
                parser.error(
                    "sync-binance-activity 在 test 模式下需要设置 BINANCE_DEMO_API_KEY/BINANCE_DEMO_API_SECRET，"
                    "或回退使用 BINANCE_API_KEY/BINANCE_API_SECRET"
                )
        summary = sync_binance_activity(
            root=root,
            decision_ref=args.decision_ref,
            order_mode=args.order_mode,
            strategy_file=args.strategy_file,
            symbol=args.symbol,
            limit=args.limit,
            audit_dir=args.audit_dir,
        )
        output = summary.to_dict()
    elif args.command == "run-binance-reconcile-loop":
        if args.order_mode == "live" and (
            not os.getenv("BINANCE_API_KEY") or not os.getenv("BINANCE_API_SECRET")
        ):
            parser.error("run-binance-reconcile-loop 在 live 模式下需要设置 BINANCE_API_KEY 和 BINANCE_API_SECRET")
        if args.order_mode == "test":
            test_key = os.getenv("BINANCE_DEMO_API_KEY") or os.getenv("BINANCE_API_KEY")
            test_secret = os.getenv("BINANCE_DEMO_API_SECRET") or os.getenv("BINANCE_API_SECRET")
            if not test_key or not test_secret:
                parser.error(
                    "run-binance-reconcile-loop 在 test 模式下需要设置 BINANCE_DEMO_API_KEY/BINANCE_DEMO_API_SECRET，"
                    "或回退使用 BINANCE_API_KEY/BINANCE_API_SECRET"
                )
        summary = run_binance_reconcile_loop(
            root=root,
            decision_ref=args.decision_ref,
            order_mode=args.order_mode,
            strategy_file=args.strategy_file,
            symbol=args.symbol,
            limit=args.limit,
            iterations=args.iterations,
            interval_s=args.interval_s,
            max_consecutive_failures=args.max_consecutive_failures,
            audit_dir=args.audit_dir,
        )
        output = summary.to_dict()
    else:
        summary = report_binance_health(
            root=root,
            max_age_minutes=args.max_age_minutes,
            audit_dir=args.audit_dir,
        )
        output = summary.to_dict()
    print(json.dumps(output, ensure_ascii=True, indent=2, sort_keys=True))
    return 0
