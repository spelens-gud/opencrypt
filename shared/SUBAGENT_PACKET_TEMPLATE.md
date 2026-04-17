# SUBAGENT_PACKET（给 `sessions_spawn.task` / `sessions_send` 的模板）

> 目标：让 subagent 在缺少你的人格、记忆和上下文时，仍能按同一执行契约稳定交付。
> 默认假设：subagent 只有 `AGENTS.md + TOOLS.md + 任务包`，没有 `SOUL/USER/MEMORY`。

## 1) Objective（一句话）
- 这次任务要解决什么：

## 2) Decision Context（为什么现在做）
- 项目/场景：
- 所处阶段：`research | decision | build | validate | ops_review | rollout | observe | knowledge`
- 上游引用：
  - `decision_ref`:
  - `review_ref`:
  - `incident_ref`:
- 当前阻塞：

## 3) Scope（边界清楚）
- 本次只做：
- 明确不做：
- 风险影响面：`data | signal | portfolio | execution | risk | audit | ops`
- 用户偏好：结论先行、少细节、可验证、不要啰嗦

## 4) Evidence / Inputs（证据或输入）
- 必读文件：
- 外部来源：
- 现有结论或假设：

## 5) Deliverables（可验证产物）
- 产出物1：
- 产出物2：
- 每个产物对应路径/链接：

## 6) Definition of Done（客观验收）
- 至少满足哪些条件才算完成：
- 需要包含哪些引用链：
- 需要执行哪些验证命令：

## 7) Guardrails（不可触碰）
- 不做不可逆动作（发版、交易、资金划转、对外发送、删除）
- 不绕过 `Ops` 审核或 `decision_ref / rollback_ref` 要求
- 需要凭证/敏感信息时：提出最小需求，不要猜
- 不再 spawn subagent（禁止无限扇出）

## 8) Output Format（announce 必须这样回）
```text
Status: success | blocked | partial
Result:
  - 结论 / 改动
  - 关键证据 / 文件路径 / 链接
  - 验证结果
Notes:
  - 风险或缺口
  - 建议下一步
  - 需要上游补齐的引用（如有）
```
