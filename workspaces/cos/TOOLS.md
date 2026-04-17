# TOOLS — CoS

## 关键文件

- `CRYPTO_QUANT_STACK_BENCHMARK.md`
- `QUANT_OPERATING_MODEL.md`
- `CONFIG_GUIDE.md`
- `EXECUTION_STATE_MACHINE.md`

## CoS 必看引用

- `../cio/decisions/`
- `../cto/SYSTEM_BLUEPRINT.md`
- `../ops/live-change-review.md`
- `../ops/runbook.md`
- `../ko/knowledge/`

## 调度边界

- 主流程：优先 `sessions_send`
- 边车型调研/整理：再用 `sessions_spawn`
- 不直接给 `builder` 下生产指令

## 环境备注

- 所有交易所凭证只记录“位置”，不写明文
- paper / live 凭证与运行环境必须分开
