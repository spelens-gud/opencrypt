# Pattern: Regime Switch Execution (Atomic)

## Boundary
- 适用于策略权重切换、禁用/启用策略、风险参数联动。

## Steps
1. freeze new entries (30-60s)
2. sync positions and pending orders
3. apply new strategy weights
4. apply new risk caps (leverage, per-trade risk)
5. unfreeze entries
6. emit switch event + checksum

## State Machine (required)
- `IDLE -> PREPARE -> FREEZE -> APPLY -> VERIFY -> COMMIT -> RESUME`
- 若 `VERIFY` 失败：`VERIFY -> ROLLBACK -> SAFE_MODE`
- `SAFE_MODE` 默认 `reduce_only=true`，需 Ops 审核后才能退出

## Atomic Switch Payload (minimum)
- `switch_id`
- `decision_ref`
- `regime_before` / `regime_after`
- `strategy_mix_before` / `strategy_mix_after`
- `risk_budget_before` / `risk_budget_after`
- `operator` (agent/session)
- `timestamp`

## Verification
- no orphan orders
- risk caps effective
- strategy whitelist/blacklist effective
- switch event persisted
- position reconciliation gap <= 0.1% NAV
- order ack timeout ratio <= 1%
- post-switch 5min no abnormal reject spike

## Rollback
- restore previous routing snapshot
- set reduce_only if verification fails
- alert Ops immediately

## Audit Trail
- 每次切换必须落盘：`switch_id + payload + verification + rollback(if any)`
- 落盘失败视为切换失败，进入 `SAFE_MODE`
