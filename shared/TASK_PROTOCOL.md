# TASK_PROTOCOL（任务分类、台账、完成定义）

## 1) Task Card（仅对 A/P/S）
在 `TASKS.md` 新建一条任务卡：
- id：YYYYMMDD-序号
- type：A/P/S
- owner：cos/cto/builder/cio/ko/ops
- objective：一句话
- stage：`research | decision | build | validate | ops_review | rollout | observe | knowledge`
- definition_of_done：可验证条件（必须客观）
- risks：1-3条
- next_action：下一步（可执行）
- signal：0-3（是否需要KO/Ops复盘）

量化任务额外强制字段：
- decision_ref：策略或变更依据；没有则不得进入 build
- risk_scope：影响 `data/signal/portfolio/execution/risk/audit/ops` 哪一层
- rollback_ref：任何非只读改动都要有
- review_ref：涉及 live / 风控阈值 / 权限 / 路由变更时必填
- validation_report_ref：涉及实现、参数、策略验证时必填

## 2) 完成判定（Definition of Done）
任务完成必须同时满足：
- DoD条件全部满足
- 关键产物已落盘（链接/文件/PR/笔记）
- 已写closeout（A/P/S）
- 量化任务的引用链完整（至少满足当前阶段要求）

阶段门槛：
- `research`：结论 + 证据 + 可信度
- `decision`：`decision_ref`
- `build/validate`：`decision_ref + rollback_ref + validation_report_ref`
- `ops_review/live`：`decision_ref + rollback_ref + review_ref`
- `done`：若涉及上线，还需 `knowledge_ref` 或 KO 沉淀记录

## 3) 何时写 Closeout
- A：涉及代码/配置/投资框架/长期原则 → 必须
- P：必须
- S：必须
- Q：默认不写；若形成"可复用认知/原则/坑" → 写入MEMORY并打signal≥2

## 4) 何时写 Checkpoint（切割长任务）
任一触发即可：
- 任务跨天仍未完成
- 对话轮次 > 20轮
- 工具返回大量数据（如搜索结果 > 50条）
- 你预计用户可能中断/忘记回到此任务
- 需要把主线拆成多个并行子任务（spawn）

Checkpoint的结果：
- 刷新TASKS.md：把下一步明确化
- 必要时：生成"子任务列表"，由主Agent spawn执行
- 若是量化主线，同时更新当前 `stage` 与缺失引用（如 `missing_review_ref`）

## 5) Spawn子任务
当需要并行/隔离/非阻塞执行：
- 用 SUBAGENT_PACKET_TEMPLATE.md 组装自包含任务包
- subagent没有你的SOUL/USER/MEMORY，任务描述必须完整
- 要求announce必须带：Status/Result/Notes
- 量化任务下发前，主Agent必须先写清：`objective + stage + decision_ref + risk_scope + DoD + rollback_ref`
