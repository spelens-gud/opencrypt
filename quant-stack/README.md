# Crypto Quant Repo Layout

这个目录不是运行代码，而是给你后续落地真实交易系统时的 **仓结构骨架**。

目标是让 OpenClaw 团队的角色分工，能直接映射到代码仓模块。

## 推荐目录

```text
quant-stack/
  market-data/
  signal-engine/
  portfolio-engine/
  execution-gateway/
  risk-engine/
  audit-log/
  observability/
  configs/
  runbooks/
```

## 模块说明

### `market-data/`
- 行情接入
- orderbook / kline / funding / oi 归一化
- freshness 检查

### `signal-engine/`
- regime routing
- 策略信号
- 参数快照与版本

### `portfolio-engine/`
- 目标仓位
- 权重映射
- 风险预算到仓位规则

### `execution-gateway/`
- 交易所适配器
- 下单、撤单、重试
- order / fill 生命周期

### `risk-engine/`
- pre-trade checks
- 杠杆上限
- per-trade risk
- daily loss cap
- reduce-only / kill-switch

### `audit-log/`
- orders
- fills
- positions
- risk snapshots
- regime switch events
- review / rollback / incident refs

### `observability/`
- metrics
- alerts
- dashboards
- replay traces

### `configs/`
- `paper/`
- `live/`
- `strategies/`
- `venues/`

### `runbooks/`
- rollout
- rollback
- incident
- kill-switch

## 团队映射

| 代码模块 | 主要 owner |
|----------|------------|
| market-data | CTO / Builder |
| signal-engine | CIO / CTO / Builder |
| portfolio-engine | CIO / CTO |
| execution-gateway | CTO / Builder |
| risk-engine | CTO / Ops |
| audit-log | CTO / Ops / KO |
| observability | Ops |
| configs | CIO / CTO / Ops |
| runbooks | Ops / CoS |

## 最小落地顺序

1. `configs/strategies`
2. `signal-engine`
3. `execution-gateway`
4. `risk-engine`
5. `audit-log`
6. `runbooks`

先把闭环跑通，再扩复杂度。

## 当前可运行内容

源码级可执行入口：

```bash
cd quant-stack
PYTHONPATH=src python3 -m opencrew_quant blueprint
PYTHONPATH=src python3 -m opencrew_quant run-paper-cycle --decision-ref DEC-2026-04-17-001
```

当前 `run-paper-cycle` 会串起：

- 模拟行情
- 信号生成
- 目标仓位计算
- 风控审批
- paper 下单
- 审计事件输出

它是最小主线，不接真实交易所。

## 币安 Futures 接入

当前已经改成基于 **CCXT 的 Binance USDⓈ-M Futures 适配**：

```bash
cd quant-stack

# 只拉币安公开行情，不发单
PYTHONPATH=src python3 -m opencrew_quant run-binance-cycle \
  --decision-ref DEC-2026-04-17-002 \
  --order-mode preview

# 使用 CCXT demo trading 下单
export BINANCE_DEMO_API_KEY=...
export BINANCE_DEMO_API_SECRET=...
PYTHONPATH=src python3 -m opencrew_quant run-binance-cycle \
  --decision-ref DEC-2026-04-17-003 \
  --order-mode test
```

默认规则：

- `preview`：只用币安公开行情，不发单
- `test`：通过 `ccxt.binance.enable_demo_trading(True)` 走 Binance demo trading
- `live`：通过 `ccxt.binance` 发真实订单

建议先只用 `preview` 和 `test`。

变量约定：

- `BINANCE_DEMO_API_KEY / BINANCE_DEMO_API_SECRET`：demo trading 专用
- `BINANCE_API_KEY / BINANCE_API_SECRET`：真实 live 专用

持续 reconcile 轮询：

```bash
cd quant-stack

PYTHONPATH=src python3 -m opencrew_quant run-binance-reconcile-loop \
  --decision-ref DEC-2026-04-17-LOOP-001 \
  --order-mode test \
  --symbol BTC/USDT:USDT \
  --limit 5 \
  --iterations 3 \
  --max-consecutive-failures 3
```

说明：

- 每个 cycle 会依次执行 `sync-binance-account` 和 `sync-binance-activity`
- 默认间隔来自 `configs/venues/*.json` 的 `reconcile_interval_s`
- 可用 `--interval-s` 临时覆盖
- 连续错误达到 `--max-consecutive-failures` 后会主动停止
- 输出会包含每一轮的账户快照、活动快照和 cycle 级告警

审计落盘：

- `sync-binance-account` 默认写入 `state/audit/account_snapshots.jsonl`
- `sync-binance-activity` 默认写入 `state/audit/activity_snapshots.jsonl`
- `run-binance-reconcile-loop` 默认写入 `state/audit/reconcile_loops.jsonl`
- 如需覆盖目录，可为这三个命令传 `--audit-dir /absolute/path`

健康摘要：

```bash
cd quant-stack

PYTHONPATH=src python3 -m opencrew_quant report-binance-health \
  --max-age-minutes 30
```

输出适合接到 CoS / Ops heartbeat：

- `status`: `ok | action_required`
- `summary`: 最近 reconcile 轮询概况
- `actions`: 建议下一步动作
- `refs`: 最新 `decision_ref / cycle_ref`

代理约定：

- `configs/venues/binance.paper.json` 已内置 `proxy_url`，默认指向 `http://127.0.0.1:7897`
- 如需临时覆盖，优先级从高到低为：
  `BINANCE_HTTPS_PROXY` -> `HTTPS_PROXY` -> `BINANCE_PROXY` -> `ALL_PROXY` -> `venue.proxy_url`
- 当前实现只会为 Binance 适配层显式设置代理，不依赖 `requests` 自动继承环境变量

币安最小名义金额：

- Binance USDⓈ-M Futures 当前会返回合约的最小 `notional`
- 量化入口会在风控审批前读取该值，并对低于门槛的订单直接拒绝
- 例如 BTCUSDT demo 目前低于 `50 USDT` 的开仓单会被提前拦截，不再等交易所回 `-4164`

如果你的网络环境有企业代理或自签证书链，可选：

```bash
export BINANCE_CA_BUNDLE=/path/to/ca.pem
# 仅限受控环境临时排障，不建议长期使用
export BINANCE_SKIP_SSL_VERIFY=1
```
