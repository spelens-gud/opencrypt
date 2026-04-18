**中文**

> 📖 [README](../README.md) → [量化交易系统版](../README.md#量化交易系统版) → **Slack 量化版配置参考**

# OpenClaw Crypto Quant for Slack 最小增量配置

> 适用：
> - 已安装并能运行 OpenClaw
> - 已完成 Slack 接入
> - 准备用 OpenClaw 管理一个 **加密量化交易团队**

> 原则：
> - 不提供完整 `openclaw.json`
> - 只提供量化版所需的最小增量
> - 保持可回滚

---

## 改之前先备份

```bash
cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.bak.$(date +%Y%m%d-%H%M%S)
```

---

## 你需要准备的频道

- `<SLACK_CHANNEL_ID_HQ>`: `#hq`
- `<SLACK_CHANNEL_ID_CIO>`: `#cio`
- `<SLACK_CHANNEL_ID_CTO>`: `#cto`
- `<SLACK_CHANNEL_ID_BUILD>`: `#build`
- `<SLACK_CHANNEL_ID_OPS>`: `#ops`
- `<SLACK_CHANNEL_ID_KNOW>`: `#know`
- `<SLACK_CHANNEL_ID_RESEARCH>`: `#research`

建议把 `#cio / #cto / #build / #ops` 都保留为独立频道，不要混到一个频道里。

---

## 最小增量配置

### A) `agents.list`

```json
{
  "agents": {
    "list": [
      {
        "id": "cos",
        "name": "Chief of Staff / Quant Control Tower",
        "workspace": "~/.openclaw/workspace-cos",
        "agentDir": "~/.openclaw/agents/cos/agent",
        "subagents": { "allowAgents": ["cto", "cio", "research", "ops", "ko"] },
        "heartbeat": { "every": "12h", "target": "slack", "to": "channel:<SLACK_CHANNEL_ID_HQ>" }
      },
      {
        "id": "cio",
        "name": "CIO / Strategy & Risk Budget",
        "workspace": "~/.openclaw/workspace-cio",
        "agentDir": "~/.openclaw/agents/cio/agent",
        "subagents": { "allowAgents": ["research", "ko"] },
        "heartbeat": { "every": "24h", "target": "slack", "to": "channel:<SLACK_CHANNEL_ID_CIO>" }
      },
      {
        "id": "cto",
        "name": "CTO / Quant Platform",
        "workspace": "~/.openclaw/workspace-cto",
        "agentDir": "~/.openclaw/agents/cto/agent",
        "subagents": { "allowAgents": ["builder", "research", "ko"] },
        "heartbeat": { "every": "12h", "target": "slack", "to": "channel:<SLACK_CHANNEL_ID_CTO>" }
      },
      {
        "id": "builder",
        "name": "Builder / Quant Executor",
        "workspace": "~/.openclaw/workspace-builder",
        "agentDir": "~/.openclaw/agents/builder/agent",
        "subagents": { "allowAgents": [] }
      },
      {
        "id": "ops",
        "name": "Ops / Risk Control",
        "workspace": "~/.openclaw/workspace-ops",
        "agentDir": "~/.openclaw/agents/ops/agent",
        "subagents": { "allowAgents": ["ko"] },
        "heartbeat": { "every": "8h", "target": "slack", "to": "channel:<SLACK_CHANNEL_ID_OPS>" }
      },
      {
        "id": "ko",
        "name": "Knowledge Officer",
        "workspace": "~/.openclaw/workspace-ko",
        "agentDir": "~/.openclaw/agents/ko/agent",
        "subagents": { "allowAgents": [] },
        "heartbeat": { "every": "48h", "target": "slack", "to": "channel:<SLACK_CHANNEL_ID_KNOW>" }
      },
      {
        "id": "research",
        "name": "Research Worker",
        "workspace": "~/.openclaw/workspace-research",
        "agentDir": "~/.openclaw/agents/research/agent",
        "subagents": { "allowAgents": [] }
      }
    ]
  }
}
```

### B) `tools` + `session`

```json
{
  "tools": {
    "agentToAgent": { "enabled": true, "allow": ["cos", "cio", "cto", "ops"] },
    "subagents": { "tools": { "deny": ["group:sessions"] } }
  },
  "session": {
    "agentToAgent": { "maxPingPongTurns": 2 }
  }
}
```

### C) `bindings`

```json
{
  "bindings": [
    { "agentId": "cos", "match": { "channel": "slack", "peer": { "kind": "channel", "id": "<SLACK_CHANNEL_ID_HQ>" } } },
    { "agentId": "cio", "match": { "channel": "slack", "peer": { "kind": "channel", "id": "<SLACK_CHANNEL_ID_CIO>" } } },
    { "agentId": "cto", "match": { "channel": "slack", "peer": { "kind": "channel", "id": "<SLACK_CHANNEL_ID_CTO>" } } },
    { "agentId": "builder", "match": { "channel": "slack", "peer": { "kind": "channel", "id": "<SLACK_CHANNEL_ID_BUILD>" } } },
    { "agentId": "ops", "match": { "channel": "slack", "peer": { "kind": "channel", "id": "<SLACK_CHANNEL_ID_OPS>" } } },
    { "agentId": "ko", "match": { "channel": "slack", "peer": { "kind": "channel", "id": "<SLACK_CHANNEL_ID_KNOW>" } } },
    { "agentId": "research", "match": { "channel": "slack", "peer": { "kind": "channel", "id": "<SLACK_CHANNEL_ID_RESEARCH>" } } }
  ]
}
```

### D) `channels.slack`

```json
{
  "channels": {
    "slack": {
      "replyToMode": "all",
      "groupPolicy": "allowlist",
      "thread": {
        "historyScope": "thread",
        "inheritParent": false,
        "requireExplicitMention": true
      },
      "channels": {
        "<SLACK_CHANNEL_ID_HQ>": { "allow": true, "requireMention": false },
        "<SLACK_CHANNEL_ID_CIO>": { "allow": true, "requireMention": false },
        "<SLACK_CHANNEL_ID_CTO>": { "allow": true, "requireMention": false },
        "<SLACK_CHANNEL_ID_BUILD>": { "allow": true, "requireMention": false },
        "<SLACK_CHANNEL_ID_OPS>": { "allow": true, "requireMention": true },
        "<SLACK_CHANNEL_ID_KNOW>": { "allow": true, "requireMention": true },
        "<SLACK_CHANNEL_ID_RESEARCH>": { "allow": true, "requireMention": true }
      }
    }
  }
}
```

---

## 量化版额外建议

- `paper` 与 `live` 使用不同 API key
- 任何 live 相关变更必须先有 `decision_ref`
- 每个 mainline 任务都必须先声明 `strategy_lane`
  - `directional_alpha`
  - `basis_carry`
  - `microstructure_mm`
  - `signal_relay`
  - `grid_dca`
- 任何提交到 `ops` 的审核包必须附：
  - `strategy_lane`
  - `validation_plan_ref`
  - `validation_report_ref`
  - `rollback_ref`
  - `review_ref`
- rollout 期间还应补：
  - `rollout_ref`
  - `observe_ref`
- `#build` 只做实施，不直接接用户生产指令

---

## 工作区目录

```bash
mkdir -p ~/.openclaw/workspace-{cos,cio,cto,builder,ops,ko,research}/memory
mkdir -p ~/.openclaw/workspace-cto/{patterns,scars,templates}
mkdir -p ~/.openclaw/workspace-builder/templates
mkdir -p ~/.openclaw/workspace-ops/templates
mkdir -p ~/.openclaw/workspace-ko/{inbox,knowledge}
```

---

## 验证顺序

1. 在 `#cio` 发消息，确认 CIO 可产出带 `strategy_lane` 的 `decision_ref`
2. 在 `#cto` 派发任务，确认 Builder 在 `#build` thread 回复，且任务包包含 lane-specific 验证要求
3. 在 `#ops` 提交一条模拟变更审核，确认 `review_ref` 留痕
4. 检查 heartbeat 是否运行

```bash
openclaw gateway restart
openclaw status
openclaw system heartbeat last
```

---

## 建议的量化 heartbeat 用法

建议让 `#ops` 和 `#hq` 的 heartbeat 在 thread 里执行以下两步：

1. 先跑一次对账轮询：

```bash
cd quant-stack
PYTHONPATH=src python3 -m opencrew_quant run-binance-reconcile-loop \
  --decision-ref HB-<YYYYMMDD-HHMM> \
  --order-mode test \
  --symbol BTC/USDT:USDT \
  --limit 5 \
  --iterations 1 \
  --interval-s 0
```

2. 再生成健康摘要：

```bash
cd quant-stack
PYTHONPATH=src python3 -m opencrew_quant report-binance-health \
  --max-age-minutes 30
```

推荐让 heartbeat 消息只贴摘要，不贴整段 JSONL。

---

## Lane 示例

- `directional_alpha`
  - 例：`trend_follow / mean_reversion`
  - 重点：回测、replay、paper、一致性验证
- `basis_carry`
  - 例：`funding arbitrage / cash-and-carry`
  - 重点：hedge 对齐、basis/funding 成本、腿间失配告警
- `microstructure_mm`
  - 例：`grid market making / inventory skew`
  - 重点：orderbook replay、quote 生命周期、orphan order
- `signal_relay`
  - 例：`TradingView webhook / 外部策略信号`
  - 重点：信号鉴权、去重、reduce-only 映射
- `grid_dca`
  - 例：`grid bot / DCA ladder`
  - 重点：单 bot 资金上限、梯子健康、库存陷阱

---

## 回滚

```bash
cp ~/.openclaw/openclaw.json.bak.<timestamp> ~/.openclaw/openclaw.json
openclaw gateway restart
```

并删除这次新增的：

- `agents.list` 量化团队条目
- `bindings` 新增项
- `channels.slack.channels` 的 allowlist 条目
- 量化工作区目录
