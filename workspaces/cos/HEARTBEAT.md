# HEARTBEAT — CoS

> 心跳触发时的检查清单。保持简短以限制token消耗。
> 如果没有需要做的事，回复 HEARTBEAT_OK

## 检查项（每天 2 次）
- [ ] 各Agent是否有卡点需要推进？
- [ ] 用户的主要方向有无偏离？
- [ ] 是否需要准备Daily Briefing？
- [ ] 是否存在 `blocked` 超过 24h 且未升级处理的任务？
- [ ] `done` 任务是否满足引用链完整性（decision/review/rollback）？

## 升级触发器
- 出现 R4/R5、sev1/sev2、或实盘风险边界变化：立即拉起 Ops。
- 同一任务连续 2 个心跳周期无进展：强制重排优先级并缩小 scope。

## 主动工作（可在heartbeat时做）
- 整理TASKS.md
- 催促跨天任务的checkpoint
- 准备briefing素材
- 查看最新量化健康摘要：
  `cd quant-stack && PYTHONPATH=src python3 -m opencrew_quant report-binance-health --max-age-minutes 30`

## 输出格式
- `status`: ok | action_required
- `actions`: 下一步动作（最多 3 条）
- `refs`: 相关 task_id / review_ref
