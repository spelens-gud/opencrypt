# WEEKLY OPERATING CYCLE (Futures, Balanced)

## 目标
- 用固定节奏保障“策略切换、风险控制、复盘沉淀”持续执行，不依赖临场发挥。

## 引用字段约定（统一）

- `decision_ref`：指向 `workspaces/cio/decisions/*.md`
- `review_ref`：指向 Ops 审核记录（如 `live-change-review.md`）
- `incident_ref`：指向事故记录（基于 `incident-template.md`）
- `knowledge_ref`：指向 KO 知识产物（`principles/patterns/scars`）

## 每日节奏（Daily）

### 09:00 - 开盘前准备
- **Owner**: CIO
- **动作**:
  - 更新 Regime 判定（R1-R5）
  - 输出当日 `strategy mix` 与 `risk budget`
  - 写一条 decision（可用 `decisions/TEMPLATE.md`）
- **产物**:
  - `decision_ref: workspaces/cio/decisions/YYYY-MM-DD-*.md`

### 盘中巡检（建议 3 次）
- **Owner**: Ops
- **动作**:
  - 检查下单失败率、执行延迟、风险暴露
  - 检查点差与深度异常
  - 异常时按 `ops/runbook.md` 执行应急动作
- **产物**:
  - `review_ref: workspaces/ops/live-change-review.md`（如触发审核）
  - `incident_ref: workspaces/ops/incident-template.md`（如触发事故）

### 收盘后复核
- **Owner**: CIO + Ops
- **动作**:
  - CIO 补齐 decision 的 T+0 观察项
  - Ops 复核是否触发审核或停机条件
- **产物**:
  - `decision_ref` 更新（补齐 T+0 观察）
  - 必要时补 `review_ref`

## 每周节奏（Weekly）

### 周回顾（建议周末）
- **Owner**: CIO
- **动作**:
  - 使用 `signals/weekly-review-template.md` 做周评审
  - 评估阈值是否“保持/调整”
- **产物**:
  - `decision_ref` 或周评审记录（建议放在 `signals/` 下）

### 防过拟合审查
- **Owner**: Ops
- **动作**:
  - 按 `ops/overfit-checklist.md` 做周度审查
  - 标注是否通过、是否需要回滚/冻结变更
- **产物**:
  - `review_ref`（周审查记录）

### 知识沉淀
- **Owner**: KO
- **动作**:
  - 从本周 decision 与 closeout 提炼原则/模式/scar
  - 更新 `ko/knowledge/` 相关文档
- **产物**:
  - `knowledge_ref: ko/knowledge/principles.md`
  - `knowledge_ref: ko/knowledge/patterns.md`
  - `knowledge_ref: ko/knowledge/scars.md`

## 触发式流程（Event-driven）

- **触发 R5 / 流动性压力**:
  - 立即进入 `reduce_only` 倾向
  - Ops 启动保护流程，必要时 kill-switch
  - 24 小时内完成 incident 记录

- **触发参数调整需求**:
  - CIO 先写证据与预期效果
  - Ops 审核通过后执行
  - 改动后进入观察窗口（见 `signals/threshold-calibration.md`）

## 交付检查清单

- 每日是否至少有 1 条 decision 记录
- 每周是否完成 1 次周评审 + 1 次防过拟合审查
- 事故是否全部有模板化记录并闭环到 KO 知识库
