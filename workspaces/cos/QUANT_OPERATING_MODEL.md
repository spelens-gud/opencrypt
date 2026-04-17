# OpenClaw Crypto Quant Operating Model

## 目标

把 OpenCrew 从“多角色协作模板”升级为 **可执行的加密量化交易编排层**：

- 前台有明确的研究、决策、实施、审核、复盘闭环
- 中台有稳定的任务状态机、引用链和回滚纪律
- 后台有 OpenClaw 友好的 session / thread / heartbeat / bindings 配置

## 五层能力面

### 1. Market Intelligence
- owner: `research`
- 产物：交易所画像、因子对标、外部系统 benchmark、策略候选池
- 输出格式：`结论 + 证据 + 系统映射 + 下一步`

### 2. Portfolio Decision
- owner: `cio`
- 产物：`decision_ref`
- 必填字段：
  - `regime`
  - `strategy_mix`
  - `risk_budget`
  - `abort_condition`
  - `evidence_ref`

### 3. Execution Engineering
- owner: `cto -> builder`
- 产物：执行任务包、代码/配置改动、验证报告、`rollback_ref`
- 模块边界：
  - `data`
  - `signal`
  - `portfolio`
  - `execution`
  - `risk`
  - `state/audit`

### 4. Risk Control
- owner: `ops`
- 产物：`review_ref`、巡检记录、事故记录、演练记录
- 审核重点：
  - 真实交易权限
  - 仓位与杠杆边界
  - kill-switch
  - 回滚可执行性
  - 监控与告警

### 5. Knowledge Flywheel
- owner: `ko`
- 产物：`pattern / scar / principle`
- 输入来源：
  - `decision_ref`
  - `review_ref`
  - `incident_ref`
  - Builder closeout

## 标准工作流

### A. 新策略或新交易所接入
1. Research 产出 benchmark / 风险画像
2. CIO 判断是否进入候选池
3. CTO 拆成 `data/signal/execution/risk` 四层任务包
4. Builder 完成回测、回放、paper、风控断言
5. Ops 审核上线与回滚
6. CoS 安排灰度与观察窗口
7. KO 沉淀经验

### B. Regime 切换
1. CIO 更新 `decision_ref`
2. CTO 执行状态切换
3. Builder 验证参数与白名单生效
4. Ops 复核风控边界
5. CoS 追踪观察期

### C. 异常事件
1. Ops 先执行保护动作
2. CoS 冻结相关上线主线
3. CIO 重估 `risk_budget`
4. CTO / Builder 处理根因
5. KO 写 scar

## OpenClaw 里的路由规则

### 常驻主 Agent
- `cos`: 主控面与用户接口
- `cio`: 投资与组合决策
- `cto`: 技术与执行架构
- `builder`: 实施者
- `ops`: 风控与审计
- `ko`: 知识沉淀
- `research`: 调研 worker，可常驻也可只做 worker

### A2A 纪律
- `sessions_send`: 主流程，适合明确 owner 的 thread 协作
- `sessions_spawn`: 只用于 Research / KO 等边车型 worker
- 每个任务一个 thread，不在频道主时间线里散落状态
- 每个 `done` 条目必须能追溯到 `decision_ref / review_ref / rollback_ref`

## 量化任务的硬门槛

- 没有 `decision_ref` 的策略任务，不得下发 Builder
- 没有 `rollback_ref` 的执行改动，不得申请 Ops 审核
- 涉及 live 权限、风控阈值、订单路由的改动，没有 `review_ref` 不得标记 done
- 出现 `R4/R5` 或 sev1/sev2，默认先 risk-off，再讨论收益恢复

## 第一阶段目标系统

优先做成“中低频、可审计、可回滚”的系统，而不是一开始追求高频极限：

- 策略：`trend_follow + mean_reversion`
- 运行环境：`backtest + replay + paper + controlled live`
- 交易所：先 1 家主交易所，再扩展多 venue
- 审计：订单、成交、仓位、风控快照必须可回放

## 非目标

- 不追求毫秒级做市撮合优化
- 不做一次性全自动无人审核上线
- 不把所有策略都塞进一个 agent 的上下文里
