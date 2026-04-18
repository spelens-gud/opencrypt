# AGENTS — CIO 工作流

## Every Session

1. 读 `SOUL.md`
2. 读 `~/.openclaw/shared/SYSTEM_RULES.md`
3. 读 `USER.md`
4. 读 `memory/YYYY-MM-DD.md`
5. 读 `MEMORY.md`（本workspace只有用户+bots，全部视为MAIN）

## 任务类型

- **跟踪**：持仓状态更新
- **复盘**：决策记录与分析
- **预警**：逻辑变化检测
- **框架**：投资原则迭代

## 量化运行节奏（Futures）

- **Daily**：至少产出 1 条 decision（记录 regime、策略组合、风险预算）。
- **Weekly**：完成 1 次 `weekly-review-template.md` 评审，判断阈值“保持/调整”。
- **Event-driven**：触发 R4/R5 或异常告警时，优先执行保护动作并同步 Ops。

## 输出规范

任务完成时closeout必须包含：
- `strategy_lane`
- 决策/观点
- 依据（数据/逻辑）
- 风险提示（如有）
- 需要用户决策的点（如有）
- 若 `ops_required=yes`，必须附上 Ops 审核引用信息
- 量化主线必须产出 `decision_ref`
- 若建议进入 rollout，还要写明观察窗条件，供 CoS/Ops 转成 `rollout_ref / observe_ref`

量化决策新增要求：
- `directional_alpha`：明确 alpha 假设、失效条件、仓位上限
- `basis_carry / microstructure_mm`：明确允许的库存/对冲偏差、撤单或 risk-off 触发器
- `signal_relay / grid_dca`：明确 bot 模板、单 bot 资本上限、何时停新单

## 文件读取优先级（量化场景）

1. `SOUL.md`
2. `signals/regime-routing.md`
3. `signals/metric-dictionary.md`
4. `WEEKLY_OPERATING_CYCLE.md`
5. `decisions/README.md` 与 `decisions/TEMPLATE.md`

## Spawn调度

- 行业调研 → spawn research
- 复盘整理 → spawn ko

## Memory维护

- **daily notes**: `memory/YYYY-MM-DD.md`
- **principles/**: 投资原则
- **decisions/**: 决策日志
