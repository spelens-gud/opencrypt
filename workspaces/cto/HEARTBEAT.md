# HEARTBEAT — CTO

> 建议频率：每天 2 次（中段 / 收盘后）。
> 如果没有需要做的事，回复 `HEARTBEAT_OK`。

## 检查项
- [ ] 在途任务是否都具备 `decision_ref + DoD + rollback_ref`？
- [ ] 是否存在连续两次 checkpoint 无收敛任务？
- [ ] 是否有实盘相关改动未绑定 `review_ref`？
- [ ] 验证命令是否可复现且结果已留痕？

## 升级触发器
- 连续两次 checkpoint 无收敛：立刻降级 scope 并通知 CoS。
- 执行状态不一致或验证失败：进入 SAFE_MODE 路径并通知 Ops。

## 输出格式
- `status`: ok | action_required
- `actions`: 下一步动作（最多 3 条）
- `refs`: task_id / review_ref / rollback_ref
