# Execution State Machine (Crypto Quant)

## 目标

统一量化系统里“想法、决策、实现、审核、上线、观察、复盘”的状态语义。

如果没有统一状态机，最容易出现两类假完成：

- 只有代码改动，没有决策依据
- 只有回测结果，没有上线审核和回滚路径

## 标准状态

- `idea`: 想法已出现，但还没有正式 owner
- `research_ready`: benchmark / 资料已足够支撑判断
- `decision_ready`: CIO 已给出 `decision_ref`
- `build_ready`: CTO 已给出任务包
- `sim_ready`: Builder 已完成 backtest / replay / paper
- `review_ready`: 已具备 `rollback_ref`，等待 Ops 审核
- `live_ready`: Ops 已放行，可进入受控上线
- `observing`: 已灰度/上线，处于观察窗口
- `done`: 观察通过，知识已沉淀
- `blocked`: 被明确阻塞
- `rolled_back`: 已执行回滚

## 阻塞原因枚举

- `missing_decision_ref`
- `missing_review_ref`
- `missing_rollback_ref`
- `missing_validation_report`
- `waiting_user`
- `external_dependency`
- `risk_gate_failed`

## 迁移规则

### 1. Research
- `idea -> research_ready`
- 条件：至少有结论、证据、适配建议、可信度

### 2. CIO
- `research_ready -> decision_ready`
- 条件：形成 `decision_ref`
- `decision_ref` 最少包含：
  - `regime`
  - `strategy_mix`
  - `risk_budget`
  - `abort_condition`

### 3. CTO / Builder
- `decision_ready -> build_ready`
- 条件：CTO 已生成任务包，写明 `scope + DoD + rollback_ref`
- `build_ready -> sim_ready`
- 条件：Builder 提交 `validation_report`
- `validation_report` 至少覆盖：
  - 回测或回放结果
  - 风控断言
  - 异常样本

### 4. Ops
- `sim_ready -> review_ready`
- 条件：需要 live 变更时，提交审核包
- `review_ready -> live_ready`
- 条件：Ops 给出 `review_ref`

### 5. Rollout
- `live_ready -> observing`
- 条件：CoS 安排灰度、观察窗口与负责人
- `observing -> done`
- 条件：
  - 观察期通过
  - 无未关闭事故
  - KO 已沉淀知识

### 6. Rollback
- `review_ready -> rolled_back`
- `live_ready -> rolled_back`
- `observing -> rolled_back`
- 条件：任一风控门失败或 Ops 判定需要回滚

## done 的强制条件

- 必须具备：`decision_ref`
- live 相关必须具备：`review_ref`
- 任何非只读变更必须具备：`rollback_ref`
- 必须具备：`validation_report`
- 必须具备：`knowledge_ref` 或 KO 沉淀记录

任一引用缺失，不得标记 `done`。
