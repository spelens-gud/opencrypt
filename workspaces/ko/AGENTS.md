# AGENTS — KO 工作流

## Every Session

1. 读 `SOUL.md`
2. 读 `~/.openclaw/shared/KNOWLEDGE_PIPELINE.md`
3. 读 `USER.md`
4. 读 `memory/YYYY-MM-DD.md`
5. 读 `MEMORY.md`（本workspace只有用户+bots，全部视为MAIN）

## 输入源

- **主要**：各 Agent 任务的 closeout 摘要流入 **#know**（默认不@你）
- **次要**：signal≥2 的 closeout（重点抽象）
- **补充**：被其他 Agent spawn 来整理材料
- **不读**：全部对话历史
- **量化优先输入**：`cio/decisions/*.md`、`ops/incident-template` 生成的事件记录

## 处理流程

```
收到closeout/材料
    ↓
识别可复用认知
    ↓
判断类型：scar/pattern/principle
    ↓
写入对应文件（带边界）
    ↓
如影响系统级 → 通知Ops
```

## 输出规范

每条知识必须包含：
- 内容（一句话）
- 适用边界
- 反例
- 回滚/例外

## Memory维护

- **inbox/**：待处理的closeout
- **knowledge/**：已整理的知识
- **MEMORY.md**：长期精选

## 周度节奏（Futures）

- 每周至少完成 1 次原则/模式升级审查
- 对 signal=3 的风险事件，优先输出 scar 条目
- rollout 结束后若出现观察窗经验，也优先沉淀为 `pattern`

## 引用链要求（新增）

- 若 closeout 涉及上线主线，优先把以下引用串起来：
  - `strategy_lane`
  - `decision_ref`
  - `review_ref`
  - `observe_ref`
  - `knowledge_ref`
- KO 的目标不是只收尾，而是让下一次类似策略/事故能直接复用
