# EXECUTION TASK PACKET TEMPLATE

## 1. Objective
- ...

## 2. Decision Reference
- `strategy_lane`:
- `decision_ref`:
- `regime`:
- `strategy_mix`:
- `risk_budget`:

## 3. Scope
- `data_scope`:
- `signal_scope`:
- `execution_scope`:
- `risk_scope`:

## 4. Deliverables
- `strategy_config`
- `execution_config`
- `risk_config`
- `validation_report`

## 5. Validation Plan
- backtest:
- replay:
- paper:
- risk assertions:

## 5.1 Lane-Specific Validation
- `directional_alpha`: lookahead / baseline / parameter drift
- `basis_carry`: hedge parity / funding-cost model / leg mismatch drills
- `microstructure_mm`: orderbook replay / quote staleness / orphan order reconcile
- `signal_relay`: signal replay / idempotency / auth-expiry / reduce-only mapping
- `grid_dca`: capital sleeve limit / ladder overlap / trapped inventory review

## 6. Rollback
- `rollback_ref`:
- rollback trigger:
- rollback owner:

## 7. DoD
- ...

## 8. Boundaries
- 不做真实交易
- 不跳过风控断言
- 不省略 `validation_report`
- 不省略 `strategy_lane`
