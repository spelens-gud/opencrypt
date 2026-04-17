# TASKS — Ops

> 状态枚举：`todo | in_progress | blocked | done`
> 引用字段约定：`review_ref`（审核记录路径）/ `incident_ref`（事故记录路径）
> 结论枚举：`Approved | Approved with notes | Needs revision | Rejected`

| id | cadence | type | objective | status | verdict | verify_command | next_action | DoD（验收标准） | review_ref | incident_ref | signal |
|----|---------|------|-----------|--------|---------|----------------|-------------|------------------|------------|--------------|--------|
| OPS-W1-001 | daily | S | 启用 Futures 实盘变更审核闸门 | in_progress | Approved with notes | 每日检查新增变更是否全部进入 `live-change-review.md` | 对缺失 `rollback_ref` 的变更一律打回 | 至少完成 3 条真实变更审核记录，且每条包含结论与审批人 | workspaces/ops/live-change-review.md | n/a | 3 |
| OPS-W1-002 | weekly | A | 建立防过拟合周检查机制 | in_progress | n/a | 每周执行一次 `overfit-checklist.md` 并记录通过/拒绝 | 对关键项不通过的策略变更标记 `Needs revision` | 产出首份周检查记录（覆盖窗口泛化/成本计入/前瞻观察三项） | workspaces/ops/overfit-checklist.md | n/a | 2 |
| OPS-W1-003 | weekly | S | 验证 kill-switch 与回滚链路可用性 | todo | n/a | 进行一次演练并记录触发到恢复的时间线 | 演练失败时生成 incident 并冻结相关上线计划 | 完成一次演练并给出时间线、执行命令、结果与改进项 | workspaces/ops/live-change-review.md | workspaces/ops/incident-template.md | 3 |
| OPS-W1-004 | daily | A | 建立异常告警值班节奏 | in_progress | n/a | 每日 3 次巡检并记录 SLO 指标是否越界 | 指标越界即执行 runbook 保护动作并留 incident_ref | 连续 5 天有巡检记录，且异常都有处理结论 | n/a | workspaces/ops/incident-template.md | 2 |
| OPS-W1-005 | weekly | S | 建立审核结论统计与拒绝原因榜单 | todo | n/a | 汇总 `Needs revision/Rejected` 的主因分布 | 输出下周改进建议并回推 CTO/CoS | 每周形成一份审核质量回顾摘要 | workspaces/ops/live-change-review.md | n/a | 1 |
| OPS-W1-006 | daily | S | 建立 paper/live 环境隔离检查 | todo | n/a | 检查凭证、运行环境、状态存储是否显式隔离 | 若发现混用，立即冻结相关上线申请 | 至少形成 1 份隔离检查记录与整改项 | workspaces/ops/live-change-review.md | n/a | 3 |
