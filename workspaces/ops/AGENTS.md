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

## 周期性工作

- 每日：检查S类closeout
- 每周：汇总Self-Update
- 每月：清理漂移

## 变更原则（硬规则）

- 基于既有成果做**增量优化**
- 有冲突就**局部修补**
- 禁止大面积重写/推倒重来
- 每次规则/角色文件变更都要留下：变更原因、影响范围、回滚方式

## Spawn调度

可spawn: ko（审计辅助）
