# HEARTBEAT — Builder

> Builder 默认不需要心跳，只响应 spawn/sessions_send 任务。
> 例外：长任务（>1天）可启用每天 1 次 checkpoint 心跳。

## 例外检查项（仅长任务模式）
- [ ] 当前轮是否已按 `Done / Run / Output / WAIT` 留痕？
- [ ] 是否存在缺失 `rollback_ref` 的高风险改动？
- [ ] 是否有验证失败但未升级给 CTO 的问题？

## 输出格式（仅长任务模式）
- `status`: ok | blocked | action_required
- `actions`: 下一步动作（最多 3 条）
- `refs`: 任务线程 / 验证命令
