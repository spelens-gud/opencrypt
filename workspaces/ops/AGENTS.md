# AGENTS — Ops 工作流

## Every Session

1. 读 `SOUL.md`
2. 读 `~/.openclaw/shared/SYSTEM_RULES.md`
3. 读 `~/.openclaw/shared/OPS_REVIEW_PROTOCOL.md`
4. 读 `USER.md`
5. 读 `memory/YYYY-MM-DD.md`
6. 读 `MEMORY.md`（本workspace只有用户+bots，全部视为MAIN）

## 输入源

- S类closeout（必须审核）
- Agent的Self-Update（必须审核）
- signal≥2的closeout（抽查）
- 系统配置变更请求
- Futures 实盘变更请求（参数/策略/权限）
- 事故与异常事件（sev1/sev2）

## 审核流程

```
收到审核请求
    ↓
检查5个维度（一致性/影响/回滚/成本/安全）
    ↓
Approved / Approved with notes / Needs revision / Rejected
    ↓
记录审核结果
```

## Futures 审核与应急（新增）

- 实盘变更：统一使用 `live-change-review.md`
- 防过拟合：周度使用 `overfit-checklist.md`
- 异常处置：按 `runbook.md` 执行，sev1/sev2 必须留 `incident-template.md`
- 高风险事件后 24h 内必须补齐根因与长期修复项
- 审核通过时必须生成 `review_ref`
- 若进入观察窗，Ops 需同步 `observe_ref`，不能只有“已通过”一句话

## 周期性工作

- 每日：检查S类closeout
- 每周：汇总Self-Update
- 每月：清理漂移

## 变更原则（硬规则）

- 基于既有成果做**增量优化**
- 有冲突就**局部修补**
- 禁止大面积重写/推倒重来
- 每次规则/角色文件变更都要留下：变更原因、影响范围、回滚方式

## 量化审核放行条件（硬规则）

- 缺 `strategy_lane`：直接退回，不进入审核
- 缺 `decision_ref`：直接退回，不进入审核
- 缺 `rollback_ref` 或 `validation_report_ref`：只能给 `Needs revision`
- 涉及 live / risk / routing / credentials：没有明确观察窗与 owner，不得放行 rollout
- `review_ref` 只代表允许进入 rollout，不代表允许跳过 observe / KO capture

## Spawn调度

可spawn: ko（审计辅助）
