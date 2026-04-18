from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

try:
    from enum import StrEnum
except ImportError:  # pragma: no cover - Python < 3.11 compatibility for local validation.
    class StrEnum(str, Enum):
        pass


class Environment(StrEnum):
    BACKTEST = "backtest"
    REPLAY = "replay"
    PAPER = "paper"
    LIVE = "live"


class Side(StrEnum):
    BUY = "buy"
    SELL = "sell"


@dataclass(slots=True)
class StrategyConfig:
    name: str
    venue: str
    symbols: tuple[str, ...]
    regime_scope: tuple[str, ...]
    family: str | None = None
    parameters: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class RiskLimits:
    max_gross_leverage: float
    per_trade_risk_bps: int
    daily_loss_limit_bps: int
    kill_switch_enabled: bool


@dataclass(slots=True)
class VenueConfig:
    name: str
    execution_mode: str
    account_type: str
    reconcile_interval_s: int
    max_order_retry: int
    proxy_url: str | None = None
