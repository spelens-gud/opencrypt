from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(slots=True)
class MarketSystemBenchmark:
    system: str
    heat_signal: str
    best_for: str
    trading_logic: tuple[str, ...]
    borrow: tuple[str, ...]
    avoid: tuple[str, ...]
    recommended_lanes: tuple[str, ...]
    local_clone_dir: str
    source_refs: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class StrategyLaneSpec:
    lane_id: str
    summary: str
    source_systems: tuple[str, ...]
    strategy_patterns: tuple[str, ...]
    required_market_data: tuple[str, ...]
    build_focus: tuple[str, ...]
    risk_focus: tuple[str, ...]
    required_refs: tuple[str, ...]
    validation_stages: tuple[str, ...]
    owner_chain: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class AgentOperatingSpec:
    agent_id: str
    role: str
    primary_channel: str
    owns: tuple[str, ...]
    capability_lanes: tuple[str, ...]
    stage_focus: tuple[str, ...]
    required_inputs: tuple[str, ...]
    required_outputs: tuple[str, ...]
    allow_agents: tuple[str, ...]
    heartbeat: str | None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_market_system_benchmarks() -> list[MarketSystemBenchmark]:
    return [
        MarketSystemBenchmark(
            system="Freqtrade",
            heat_signal="GitHub 46.6k stars; active docs/runtime for crypto bot research",
            best_for="Research-to-backtest-to-dry-run loop for directional strategies",
            trading_logic=(
                "K-line and indicator driven directional entries/exits are expressed as strategy callbacks.",
                "The dominant workflow is download data -> backtest -> hyperopt -> dry-run -> live.",
                "Trade intake is constrained by protections, pairlists, stoploss and position limits.",
            ),
            borrow=(
                "strategy parameterization",
                "backtest baseline",
                "dry-run workflow",
                "research iteration discipline",
            ),
            avoid=(
                "single-process ownership of the entire trading stack",
                "collapsing governance into the strategy runtime",
            ),
            recommended_lanes=("directional_alpha",),
            local_clone_dir=".benchmarks/external/freqtrade",
            source_refs=(
                "https://github.com/freqtrade/freqtrade",
                "https://www.freqtrade.io/",
            ),
        ),
        MarketSystemBenchmark(
            system="Hummingbot",
            heat_signal="GitHub 15.5k stars; official docs emphasize connectors, executors, Dashboard and Gateway",
            best_for="Connector-heavy execution, market making, arbitrage, multi-venue bot orchestration",
            trading_logic=(
                "Connectors normalize CEX, DEX and Gateway venues behind a common execution surface.",
                "Controllers read market data and emit executor actions rather than placing orders directly.",
                "Executors own order lifecycle, retries, rebalancing and stateful position management.",
            ),
            borrow=(
                "connector abstraction",
                "executor lifecycle",
                "multi-instance orchestration",
                "execution-centric monitoring",
            ),
            avoid=(
                "letting executors bypass human/Ops approval gates",
                "using execution concerns as the only system boundary",
            ),
            recommended_lanes=("microstructure_mm", "basis_carry", "signal_relay"),
            local_clone_dir=".benchmarks/external/hummingbot",
            source_refs=(
                "https://github.com/hummingbot/hummingbot",
                "https://hummingbot.org/docs/",
            ),
        ),
        MarketSystemBenchmark(
            system="QuantConnect LEAN",
            heat_signal="GitHub 16.3k stars; mature event-driven research/backtest/live parity",
            best_for="Event-driven state models and production parity between research and live",
            trading_logic=(
                "Algorithm Framework flows Alpha -> Portfolio Construction -> Risk Management -> Execution.",
                "Research, backtest and live share the same engine semantics and brokerage boundary.",
                "Portfolio targets are adjusted by risk models before execution models route orders.",
            ),
            borrow=(
                "research-production parity",
                "broker/risk separation",
                "phase gates for deployment",
            ),
            avoid=(
                "dragging the whole multi-asset platform into OpenClaw",
                "over-expanding asset class scope in phase 1",
            ),
            recommended_lanes=("directional_alpha", "basis_carry", "microstructure_mm"),
            local_clone_dir=".benchmarks/external/lean",
            source_refs=(
                "https://github.com/QuantConnect/Lean",
                "https://www.quantconnect.com/docs/v2/lean-cli/key-concepts/introduction",
            ),
        ),
        MarketSystemBenchmark(
            system="NautilusTrader",
            heat_signal="GitHub 17.3k stars; deterministic event-driven architecture and strong execution state model",
            best_for="Strict stateful execution, auditability, live/backtest consistency",
            trading_logic=(
                "Venue adapters translate raw feeds into a normalized domain model on the message bus.",
                "Order lifecycle, fills and portfolio state are driven by deterministic event ordering.",
                "Research and live execution share the same execution semantics and time model.",
            ),
            borrow=(
                "deterministic order state machine",
                "adapter boundaries",
                "audit-first live operations",
            ),
            avoid=(
                "copying phase-1 complexity",
                "prematurely matching its full performance abstraction layer",
            ),
            recommended_lanes=("microstructure_mm", "basis_carry"),
            local_clone_dir=".benchmarks/external/nautilus_trader",
            source_refs=(
                "https://github.com/nautechsystems/nautilus_trader",
                "https://nautilustrader.io/docs/latest/",
            ),
        ),
        MarketSystemBenchmark(
            system="Jesse",
            heat_signal="GitHub 7.3k stars; trader-friendly strategy workflow and optimization UX",
            best_for="Fast strategy prototyping, replay, optimization and trader-facing ergonomics",
            trading_logic=(
                "Strategy classes encode should_long/go_long style entry and exit logic with low boilerplate.",
                "Benchmark, optimize, Monte Carlo and ML loops are first-class research tools.",
                "Paper/live trading keeps trader-facing monitoring, alerts and charts close to strategy authors.",
            ),
            borrow=(
                "simple strategy interface",
                "replay workflow",
                "rapid feedback for researchers",
            ),
            avoid=(
                "optimizing only for single-strategy authoring",
                "sacrificing team governance for developer convenience",
            ),
            recommended_lanes=("directional_alpha",),
            local_clone_dir=".benchmarks/external/jesse",
            source_refs=(
                "https://github.com/jesse-ai/jesse",
                "https://docs.jesse.trade/",
            ),
        ),
        MarketSystemBenchmark(
            system="OctoBot",
            heat_signal="GitHub 5k+ stars; official product emphasizes web/mobile control, DCA/Grid/TradingView automation",
            best_for="Operator UX, strategy templates, bot lifecycle management for non-engineers",
            trading_logic=(
                "Productized bot templates package grid, DCA, TradingView and basket workflows behind UI flows.",
                "Backtesting, paper trading and live execution are exposed as operator actions in one console.",
                "Bot health, portfolio, orders and notifications are treated as first-class runtime surfaces.",
            ),
            borrow=(
                "dashboard thinking",
                "paper-to-live operational flow",
                "template-driven rollout paths",
            ),
            avoid=(
                "making the UI drive core system design",
                "hiding execution/risk mechanics behind a black box",
            ),
            recommended_lanes=("grid_dca", "signal_relay"),
            local_clone_dir=".benchmarks/external/octobot",
            source_refs=(
                "https://github.com/Drakkar-Software/OctoBot",
                "https://www.octobot.cloud/",
            ),
        ),
        MarketSystemBenchmark(
            system="3Commas",
            heat_signal="Commercial leader; official product pages emphasize DCA bots, SmartTrade and strategy operations",
            best_for="Strategy entry points, template packaging and operator-friendly control tower experience",
            trading_logic=(
                "Signal Bot relays external alerts into exchange orders with position and margin caps.",
                "DCA and Grid bots expose reusable templates, multi-take-profit and trade management controls.",
                "SmartTrade packages entries, stop loss, trailing logic and position actions in one operator flow.",
            ),
            borrow=(
                "productized strategy entry points",
                "bot templates",
                "unified operations console framing",
            ),
            avoid=(
                "outsourcing execution and risk guarantees to SaaS",
                "copying opaque black-box automation assumptions",
            ),
            recommended_lanes=("signal_relay", "grid_dca"),
            local_clone_dir="n/a-commercial",
            source_refs=(
                "https://3commas.io/dca-bots",
                "https://3commas.io/smart-trade",
            ),
        ),
    ]


def build_strategy_lane_specs() -> list[StrategyLaneSpec]:
    return [
        StrategyLaneSpec(
            lane_id="directional_alpha",
            summary="K-line and factor driven directional sleeves for trend, mean reversion and breakout families.",
            source_systems=("Freqtrade", "QuantConnect LEAN", "Jesse"),
            strategy_patterns=("trend_follow", "mean_reversion", "breakout", "ml_filtered_directional"),
            required_market_data=("candles", "funding", "open_interest", "volatility_regime"),
            build_focus=("signal_engine", "parameter_store", "portfolio_targets", "paper_cycle"),
            risk_focus=("max_open_positions", "stoploss", "leverage_budget", "daily_loss_cap"),
            required_refs=("benchmark_ref", "decision_ref", "validation_plan_ref", "validation_report_ref", "review_ref"),
            validation_stages=("backtest", "replay", "paper", "controlled_live"),
            owner_chain=("research", "cio", "cto", "builder", "ops", "cos", "ko"),
        ),
        StrategyLaneSpec(
            lane_id="basis_carry",
            summary="Funding, carry and market-neutral sleeves that coordinate multiple venues or instruments.",
            source_systems=("Hummingbot", "QuantConnect LEAN", "NautilusTrader"),
            strategy_patterns=("funding_arbitrage", "cash_and_carry", "basis_neutral", "hedged_rebalance"),
            required_market_data=("spot_perp_basis", "funding_rates", "borrow_cost", "hedge_inventory", "latency"),
            build_focus=("basis_router", "hedge_manager", "multi_venue_reconcile", "residual_exposure_checks"),
            risk_focus=("leg_mismatch", "borrow_availability", "liquidation_gap", "transfer_delay"),
            required_refs=("benchmark_ref", "decision_ref", "rollback_ref", "validation_plan_ref", "validation_report_ref", "review_ref"),
            validation_stages=("historical_basis_replay", "paper", "sandbox_hedge", "controlled_live"),
            owner_chain=("research", "cio", "cto", "builder", "ops", "cos", "ko"),
        ),
        StrategyLaneSpec(
            lane_id="microstructure_mm",
            summary="Orderbook-sensitive market making and liquidity provision with explicit executor state machines.",
            source_systems=("Hummingbot", "NautilusTrader", "OctoBot"),
            strategy_patterns=("grid_market_making", "inventory_skew", "lp_rebalancer", "maker_taker_hedge"),
            required_market_data=("l2_orderbook", "trades", "spread", "queue_position", "fill_latency"),
            build_focus=("connector_layer", "executor_state_machine", "quote_refresh", "inventory_skew_controller"),
            risk_focus=("quote_staleness", "orphan_orders", "inventory_drift", "self_trade_prevention"),
            required_refs=("benchmark_ref", "decision_ref", "rollback_ref", "validation_plan_ref", "validation_report_ref", "review_ref", "observe_ref"),
            validation_stages=("orderbook_replay", "paper", "sandbox_executor", "controlled_live"),
            owner_chain=("research", "cio", "cto", "builder", "ops", "cos", "ko"),
        ),
        StrategyLaneSpec(
            lane_id="signal_relay",
            summary="Webhook and external signal intake lanes that translate alerts into governed order intents.",
            source_systems=("OctoBot", "3Commas", "Hummingbot"),
            strategy_patterns=("tradingview_webhook", "analyst_signal", "ai_advisory_gate", "external_alert_router"),
            required_market_data=("signal_payloads", "exchange_ack", "position_state", "cooldown_state"),
            build_focus=("idempotent_router", "signal_registry", "template_mapping", "order_intent_audit"),
            risk_focus=("duplicate_signals", "stale_alerts", "auth_failures", "missing_reduce_only"),
            required_refs=("benchmark_ref", "decision_ref", "validation_plan_ref", "validation_report_ref", "review_ref"),
            validation_stages=("sandbox_signal_replay", "paper", "controlled_live"),
            owner_chain=("research", "cio", "cto", "builder", "ops", "cos", "ko"),
        ),
        StrategyLaneSpec(
            lane_id="grid_dca",
            summary="Productized bot templates for laddered accumulation, price-band harvesting and basket rebalancing.",
            source_systems=("OctoBot", "3Commas"),
            strategy_patterns=("grid_bot", "dca_ladder", "basket_rebalance", "range_harvest"),
            required_market_data=("candles", "portfolio_holdings", "price_bands", "ladder_state"),
            build_focus=("strategy_templates", "capital_sleeves", "order_ladder_health", "operator_controls"),
            risk_focus=("max_capital_allocation", "martingale_creep", "trapped_inventory", "ladder_overlap"),
            required_refs=("benchmark_ref", "decision_ref", "validation_plan_ref", "validation_report_ref", "review_ref", "observe_ref"),
            validation_stages=("backtest", "paper", "controlled_live"),
            owner_chain=("research", "cio", "cto", "builder", "ops", "cos", "ko"),
        ),
    ]


def build_agent_operating_specs() -> list[AgentOperatingSpec]:
    return [
        AgentOperatingSpec(
            agent_id="cos",
            role="Control tower and rollout owner",
            primary_channel="#hq",
            owns=("priority", "cross-team routing", "rollout", "observation handoff"),
            capability_lanes=("directional_alpha", "basis_carry", "microstructure_mm", "signal_relay", "grid_dca"),
            stage_focus=("rollout", "observe", "knowledge"),
            required_inputs=("decision_ref", "review_ref", "checkpoint_ref"),
            required_outputs=("rollout_ref", "observe_ref", "knowledge_ref"),
            allow_agents=("cto", "cio", "research", "ops", "ko"),
            heartbeat="12h",
        ),
        AgentOperatingSpec(
            agent_id="cio",
            role="Portfolio decision and risk budget owner",
            primary_channel="#cio",
            owns=("regime", "strategy_mix", "risk_budget", "abort_condition"),
            capability_lanes=("directional_alpha", "basis_carry", "microstructure_mm", "signal_relay", "grid_dca"),
            stage_focus=("decision", "observe"),
            required_inputs=("benchmark_ref", "evidence_ref"),
            required_outputs=("decision_ref",),
            allow_agents=("research", "ko"),
            heartbeat="24h",
        ),
        AgentOperatingSpec(
            agent_id="cto",
            role="Execution engineering and system decomposition owner",
            primary_channel="#cto",
            owns=("task_packet", "module_boundary", "validation_plan", "rollback_path"),
            capability_lanes=("directional_alpha", "basis_carry", "microstructure_mm", "signal_relay", "grid_dca"),
            stage_focus=("build", "validate"),
            required_inputs=("decision_ref",),
            required_outputs=("execution_packet_ref", "rollback_ref", "validation_plan_ref"),
            allow_agents=("builder", "research", "ko"),
            heartbeat="12h",
        ),
        AgentOperatingSpec(
            agent_id="builder",
            role="Implementation and validation owner",
            primary_channel="#build",
            owns=("code_changes", "backtest", "replay", "paper_validation"),
            capability_lanes=("directional_alpha", "basis_carry", "microstructure_mm", "signal_relay", "grid_dca"),
            stage_focus=("build", "validate"),
            required_inputs=("decision_ref", "rollback_ref", "validation_plan_ref"),
            required_outputs=("validation_report_ref",),
            allow_agents=(),
            heartbeat=None,
        ),
        AgentOperatingSpec(
            agent_id="ops",
            role="Risk control, audit and incident owner",
            primary_channel="#ops",
            owns=("ops_review", "risk_gate", "incident_response", "kill_switch"),
            capability_lanes=("directional_alpha", "basis_carry", "microstructure_mm", "signal_relay", "grid_dca"),
            stage_focus=("ops_review", "observe"),
            required_inputs=("decision_ref", "rollback_ref", "validation_report_ref"),
            required_outputs=("review_ref", "incident_ref", "observe_ref"),
            allow_agents=("ko",),
            heartbeat="8h",
        ),
        AgentOperatingSpec(
            agent_id="ko",
            role="Knowledge and scar extraction owner",
            primary_channel="#know",
            owns=("pattern", "scar", "principle"),
            capability_lanes=("directional_alpha", "basis_carry", "microstructure_mm", "signal_relay", "grid_dca"),
            stage_focus=("knowledge",),
            required_inputs=("closeout_ref", "review_ref", "incident_ref"),
            required_outputs=("knowledge_ref",),
            allow_agents=(),
            heartbeat="48h",
        ),
        AgentOperatingSpec(
            agent_id="research",
            role="Evidence worker and external benchmark owner",
            primary_channel="#research",
            owns=("benchmark", "venue_report", "risk_notes"),
            capability_lanes=("directional_alpha", "basis_carry", "microstructure_mm", "signal_relay", "grid_dca"),
            stage_focus=("research",),
            required_inputs=("research_brief_ref",),
            required_outputs=("benchmark_ref", "evidence_ref"),
            allow_agents=(),
            heartbeat=None,
        ),
    ]


def build_openclaw_delivery_contract() -> dict[str, object]:
    return {
        "routing_principles": [
            "One agent maps to one isolated workspace, one agentDir and one session namespace.",
            "Bindings route inbound work; do not infer ownership from channel names alone.",
            "One task runs in one thread; the channel root is the stable anchor, the thread is the execution unit.",
            "sessions_send is the default for mainline work; sessions_spawn is only for bounded sidecar workers.",
            "Every mainline task must declare a strategy_lane so the team follows the correct validation and risk path.",
        ],
        "slack_defaults": {
            "replyToMode": "all",
            "thread.historyScope": "thread",
            "thread.inheritParent": False,
            "thread.requireExplicitMention": True,
        },
        "heartbeat_guidance": {
            "only_control_plane_agents_run": ["cos", "cio", "cto", "ops", "ko"],
            "builder_and_research_default": "disabled",
            "heartbeat_prompt_focus": [
                "missing references",
                "stalled checkpoints",
                "risk alerts",
                "data freshness",
                "knowledge backlog",
            ],
        },
        "task_card_required_fields": [
            "strategy_lane",
            "decision_ref",
            "risk_scope",
            "rollback_ref",
            "validation_plan_ref",
        ],
        "closeout_required_fields": [
            "strategy_lane",
            "decision_ref",
            "validation_plan_ref",
            "validation_report_ref",
            "review_ref",
            "rollback_ref",
            "observe_ref",
            "knowledge_ref",
        ],
        "hard_gates": {
            "build_requires": ["decision_ref"],
            "validate_requires": ["decision_ref", "rollback_ref", "validation_plan_ref"],
            "ops_review_requires": ["decision_ref", "rollback_ref", "validation_report_ref"],
            "rollout_requires": ["review_ref", "rollout_ref"],
            "observe_requires": ["observe_ref"],
            "knowledge_requires": ["knowledge_ref"],
        },
        "lane_gate_matrix": {
            "directional_alpha": [
                "baseline_compare_required",
                "lookahead_bias_check",
                "paper_slippage_review",
            ],
            "basis_carry": [
                "hedge_ratio_check",
                "funding_and_borrow_cost_model",
                "leg_mismatch_alerts",
            ],
            "microstructure_mm": [
                "orderbook_replay_required",
                "quote_staleness_limits",
                "orphan_order_reconcile",
            ],
            "signal_relay": [
                "idempotency_check",
                "signal_auth_and_expiry_check",
                "reduce_only_mapping_when_needed",
            ],
            "grid_dca": [
                "ladder_capital_limit",
                "inventory_trap_review",
                "position_limit_and_healthcheck",
            ],
        },
    }
