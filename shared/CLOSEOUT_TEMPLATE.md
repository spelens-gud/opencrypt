# CLOSEOUT（任务结束强制输出）

## Task
- ID: [YYYYMMDD-序号]
- Type: [A/P/S]
- Owner: [agent_id]
- Stage: [research | decision | build | validate | ops_review | rollout | observe | knowledge]
- Thread: [Slack thread 链接 / channel + thread id]

## What Changed
- 产出物1：[链接/文件路径]
- 产出物2：[链接/文件路径]

## Reference Chain（量化任务强制）
- `decision_ref`:
- `validation_report_ref`:
- `review_ref`:
- `rollback_ref`:
- `incident_ref`:
- `knowledge_ref`:

## Verification
- Run:
- Output:
- Verdict: `pass | partial | fail`

## Decisions（≤3条）
1. ...
2. ...

## Risks / Gaps（≤3条）
1. ...
2. ...

## Next Actions（≤3条）
| Action | Owner | Due |
|--------|-------|-----|
| ... | ... | ... |

## Scars / Gotchas（踩坑一句话）
- ...

## Signal Score
- [0-3]：0=不用看，1=可选，2=建议看，3=必须看

## KO Intake（强制）
- 将本 closeout **同步到 #know**（不必 @ko，避免噪音；需要 KO 立刻处理时再 @）

## Promote?
- [ ] 升级为原则/流程？
- 如果是，建议内容：...
