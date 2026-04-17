# Crypto Quant System Blueprint

## 目标

给 CTO / Builder 一个统一的实施边界，避免“策略想法”和“交易系统实现”混在一起。

## 模块分层

### 1. Market Data Layer
- 行情订阅
- K 线与 orderbook 归一化
- funding / open interest / basis / account data
- freshness 检查与降级策略

### 2. Signal Layer
- 因子计算
- regime routing
- strategy whitelist / blacklist
- 参数版本管理

### 3. Portfolio Layer
- 目标仓位
- 策略权重与净敞口
- 杠杆与风险预算映射
- 仓位收敛与再平衡

### 4. Execution Layer
- venue adapter
- order manager
- submit / cancel / retry
- fill / partial fill / reject / timeout 生命周期

### 5. Risk Layer
- pre-trade checks
- per-trade risk
- max gross / net exposure
- daily loss cap
- reduce-only / kill-switch

### 6. State & Audit Layer
- orders / fills / positions
- risk snapshots
- regime switch events
- review / rollback / incident references

### 7. Observability Layer
- metrics
- alerts
- replay logs
- anomaly timeline

## 模块责任映射

| 模块 | owner | 典型产物 |
|------|-------|----------|
| data | CTO/Builder | adapter、schema、freshness checks |
| signal | CIO/CTO/Builder | signal config、参数快照、回测报告 |
| portfolio | CIO/CTO | 目标仓位规则、策略权重映射 |
| execution | CTO/Builder | order manager、router、重试逻辑 |
| risk | CTO/Ops | 风控规则、断言、kill-switch |
| audit | CTO/Ops/KO | review refs、incident refs、知识沉淀 |

## Builder 任务包最小字段

- `objective`
- `decision_ref`
- `scope`
- `risk_scope`
- `DoD`
- `rollback_ref`
- `validation_plan`

## 验证顺序

1. unit / integration
2. backtest
3. replay
4. paper
5. controlled live

任何阶段失败，都不能跳过直接进入下一阶段。

## 第一阶段建议实现

### 策略
- `trend_follow`
- `mean_reversion`

### 交易所
- 先单 venue
- 后多 venue / basis / carry

### 状态存储
- PostgreSQL 或等价结构化存储
- 日志至少可追到 order / fill / position / risk snapshot

## 不要做的事

- 不把策略逻辑硬编码在频道对话里
- 不把风控规则只放在口头说明或 closeout 里
- 不让订单状态只能靠聊天记录追溯
