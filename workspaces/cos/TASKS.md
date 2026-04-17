# TASKS — CoS Task Ledger

> 所有"主线/卡点/等待用户决策"的条目
> 状态枚举：`todo | in_progress | blocked | done`
> 阻塞原因枚举：`missing_decision_ref | missing_review_ref | missing_rollback_ref | waiting_user | external_dependency`

| id | cadence | type | objective | owner | status | blocker_reason | verify_command | next_action | signal |
|----|---------|------|-----------|-------|--------|---------------|----------------|-------------|--------|
| COS-QT-001 | daily | P | 建立量化编排主线（Research→CIO→CTO→Ops→KO） | CoS | in_progress | n/a | 检查主线任务是否都具备 owner 与下一步 | 每日更新跨团队状态，阻塞即刻升级 | 3 |
| COS-QT-002 | daily | A | 推进首批双策略（trend/mr）完成 sim→review→observing | CTO | in_progress | missing_review_ref | 校验 `decision_ref + validation_report + review_ref + rollback_ref` 是否齐全 | 要求 CTO 补齐 Ops 审核引用后再推进 live-ready | 3 |
| COS-QT-003 | weekly | S | 建立交易所接入与权限分层机制（paper/live 分离） | Ops | todo | n/a | 检查 paper/live 是否使用独立凭证与运行环境 | 推动 Ops 输出主交易所接入红线与隔离要求 | 3 |
| COS-QT-004 | weekly | A | 建立知识回流机制（决策/审核/事故->原则/模式） | KO | in_progress | external_dependency | 检查 KO 当周是否至少新增 1 条 scar 或 pattern | 催收 KO 周度知识沉淀并绑定来源引用 | 2 |
| COS-QT-005 | daily | S | 维护阻塞状态机与优先级降级机制 | CoS | todo | n/a | 连续两次 checkpoint 无收敛时触发降级记录 | 将“降级 scope + 重排优先级”写入任务回执 | 2 |
