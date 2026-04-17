# TASKS — CTO Task Ledger

| id | type | project | objective | status | next_action | signal |
|----|------|---------|-----------|--------|-------------|--------|
| CTO-QT-001 | P | quant-core | 建立双策略生产执行主线（trend/mr） | in_progress | 输出执行任务包 v1（data/signal/execution/risk 四层）并绑定 `decision_ref` | 3 |
| CTO-QT-002 | A | quant-core | 落地 Regime 原子切换状态机接入规范 | todo | 产出状态转换检查清单与失败回滚演练步骤 | 3 |
| CTO-QT-003 | S | quant-core | 与 Ops 对齐上线闸门与审核字段 | todo | 所有实盘变更模板补齐 `review_ref + rollback_ref` | 2 |
| CTO-QT-004 | A | quant-core | 建立执行验证命令基线 | todo | 统一回测/回放/风控断言命令格式并写入 closeout 要求 | 2 |
| CTO-QT-005 | A | quant-core | 建立订单状态机与审计存证蓝图 | todo | 对齐 order/fill/position/risk snapshot 的最小字段与存证路径 | 3 |
| CTO-QT-006 | A | quant-core | 建立 replay/paper/live 阶段切换标准 | todo | 写明每个阶段的进入条件、退出条件与 owner | 2 |
