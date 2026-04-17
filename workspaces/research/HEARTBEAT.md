# HEARTBEAT — Research

> Research 作为 subagent 默认不需要心跳，只响应 spawn 任务。
> 例外：若被设为常驻观察任务，建议频率每天 1 次。

## 例外检查项（仅常驻模式）
- [ ] 在途调研是否存在信息冲突且未标记 `blocked`？
- [ ] 输出是否包含可信度分级与证据链接？
- [ ] 是否有需要升级给 Ops 的风险边界问题？

## 输出格式（仅常驻模式）
- `status`: ok | blocked | action_required
- `actions`: 下一步动作（最多 3 条）
- `refs`: 调研输出链接/引用
