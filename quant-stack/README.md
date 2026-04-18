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
PYTHONPATH=src python3 -m opencrew_quant operating-model
PYTHONPATH=src python3 -m opencrew_quant openclaw-spec
PYTHONPATH=src python3 -m opencrew_quant strategy-catalog
PYTHONPATH=src python3 -m opencrew_quant run-paper-cycle --decision-ref DEC-2026-04-17-001
PYTHONPATH=src python3 -m opencrew_quant run-paper-cycle --decision-ref DEC-2026-04-18-BC-001 --strategy-file basis_carry.paper.json
PYTHONPATH=src python3 -m opencrew_quant run-paper-cycle --decision-ref DEC-2026-04-18-MM-001 --strategy-file market_making.paper.json
PYTHONPATH=src python3 -m opencrew_quant run-paper-replay --decision-ref DEC-2026-04-18-MM-REPLAY-001 --scenario inventory_refresh
PYTHONPATH=src python3 -m opencrew_quant run-binance-quote-loop --decision-ref DEC-2026-04-19-MM-LOOP-001 --order-mode preview --iterations 2
```

新增的三个入口不是“又一份文档”，而是给 OpenClaw 团队输出统一的可机读契约：

- `operating-model`：输出热门量化系统 benchmark、strategy lanes、团队职责、阶段 gate、OpenClaw 适配约束
- `openclaw-spec`：输出适合直接映射到 `agents.list / bindings / heartbeat / sessions_send` 设计的团队规格
- `strategy-catalog`：输出方向策略、basis/carry、做市、signal relay、grid/DCA 等 lane 的可机读目录

当前 `run-paper-cycle` 会串起：

- 模拟行情
- 信号生成
- 目标仓位计算
- 风控审批
- paper 下单
- 审计事件输出

当前 `run-paper-replay` 会专门覆盖 `microstructure_mm` 的 quote lifecycle：

- seed quotes
- inventory skew refresh
- replace / keep / cancel
- stale quote risk-off
- replay 级审计事件输出

当前已接通的最小策略闭环：

- `trend_follow`
- `mean_reversion`
- `basis_carry`（以 signed target weight 形式输出对冲方向，可在 paper / binance preview 中产出 buy+sell intent）
- `market_making`（以 post-only 双边 limit quote 形式输出 maker-bid / maker-ask，并带 inventory skew / stale quote / orphan order gate）

它是最小主线，不接真实交易所。

其中 `market_making` 现在已经拆成两层：

- `run-paper-cycle`：单周期 quote 计划与风控审批
- `run-paper-replay`：多周期 quote refresh / replace / cancel-risk-off 验证
- `run-binance-cycle --strategy-file market_making.paper.json`：Binance preview/test 的 maker limit / post-only / open-order replace-cancel 骨架
- `run-binance-quote-loop`：把做市 lane 挂到连续迭代里，验证跨周期 `keep / replace / cancel`

## OpenClaw 团队契约

这个目录现在不只提供“代码骨架”，还提供了和多 agent 编排直接对应的运行契约：

- 工作流阶段：`research -> decision -> build -> validate -> ops_review -> rollout -> observe -> knowledge`
- 交付阶段：`backtest -> replay -> paper -> ops_review -> live`
- 强制引用链：
  - `decision_ref`
  - `validation_plan_ref`
  - `validation_report_ref`
  - `rollback_ref`
  - `review_ref`
  - `rollout_ref`
  - `observe_ref`
  - `knowledge_ref`

这些字段会同时出现在：

- workspace 协议
- closeout / task card 模板
- `opencrew_quant operating-model` 输出

除此之外，量化主线现在还要求每个任务显式声明 `strategy_lane`，用于把任务绑定到正确的验证路径：

- `directional_alpha`
- `basis_carry`
- `microstructure_mm`
- `signal_relay`
- `grid_dca`

## 策略目录

`configs/strategies/` 现在分两类：

- 当前已串通最小执行主线的：`trend_follow.paper.json`、`mean_reversion.paper.json`、`basis_carry.paper.json`、`market_making.paper.json`
- 作为多 agent 编排目标能力清单的：`signal_router.paper.json`、`grid_dca.paper.json`

其中 `market_making.paper.json` 已经不只是 lane 占位，而是会驱动最小 quote engine 输出双边挂单计划；`signal_router` 和 `grid_dca` 目前仍主要作为 OpenClaw 团队可引用的配置契约。

## 币安 Futures 接入

当前已经改成基于 **CCXT 的 Binance USDⓈ-M Futures 适配**：

```bash
cd quant-stack

# 只拉币安公开行情，不发单
PYTHONPATH=src python3 -m opencrew_quant run-binance-cycle \
  --decision-ref DEC-2026-04-17-002 \
  --order-mode preview

# 做市 lane：生成 post-only limit quotes，并在 preview/test 路径执行 replace/cancel 逻辑
PYTHONPATH=src python3 -m opencrew_quant run-binance-cycle \
  --decision-ref DEC-2026-04-18-MM-BINANCE-001 \
  --strategy-file market_making.paper.json \
  --order-mode preview

# 做市 lane：连续跑 2 个 quote 周期，观察 keep / replace / cancel
PYTHONPATH=src python3 -m opencrew_quant run-binance-quote-loop \
  --decision-ref DEC-2026-04-19-MM-BINANCE-LOOP-001 \
  --strategy-file market_making.paper.json \
  --order-mode preview \
  --iterations 2 \
  --interval-s 1

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

对 `market_making` 来说，`preview/test` 当前已经不是简单 market order 预览，而是：

- 生成 `limit + postOnly + newClientOrderId`
- 读取当前 open orders
- 按 quote plan 做 `keep / replace / cancel`
- 在 stale quote 或 risk-off 条件下主动撤掉已有 quote

`run-binance-quote-loop` 会把这套逻辑连续执行，并将结果写入 `state/audit/quote_loops.jsonl`。

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
