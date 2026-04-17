# OpenClaw Crypto Quant 配置说明

## 目标

配置的目标不是“把 7 个 Agent 跑起来”，而是让它们形成 **量化交易系统的生产闭环**：

- 研究和决策分开
- 决策和执行分开
- 执行和审核分开
- 上线和复盘分开

## 推荐主 Agent 列表

| agent | 角色 | 主工作区 |
|------|------|----------|
| `cos` | 控制塔 | `workspaces/cos` |
| `cio` | 策略与风险预算 | `workspaces/cio` |
| `cto` | 交易平台与执行架构 | `workspaces/cto` |
| `builder` | 实施者 | `workspaces/builder` |
| `ops` | 风控与值班 | `workspaces/ops` |
| `ko` | 知识沉淀 | `workspaces/ko` |
| `research` | 调研 worker | `workspaces/research` |

## 推荐频道 / 群组

| 频道 | 绑定 agent | 用途 |
|------|-----------|------|
| `#hq` | `cos` | 用户主入口、主线推进、跨团队同步 |
| `#cio` | `cio` | regime、策略组合、风险预算 |
| `#research` | `research` | 外部 benchmark、交易所/策略/连接器调研 |
| `#cto` | `cto` | 架构、任务拆解、技术收敛 |
| `#build` | `builder` | 具体实现、验证、checkpoint |
| `#ops` | `ops` | 审核、巡检、事故、回滚 |
| `#know` | `ko` | closeout 汇总、知识沉淀 |

最小可用可以是：

- `#hq`
- `#cio`
- `#cto`
- `#build`
- `#ops`

## 推荐 allowAgents

### `cos`
- `["cto", "cio", "research", "ops", "ko"]`
- 作用：主控面可以拉起研究、决策、执行与审核链路

### `cto`
- `["builder", "research", "ko"]`
- 作用：拆解任务、调用实施者、并行拉 research 做技术验证

### `cio`
- `["research", "ko"]`
- 作用：外部情报和复盘整理

### `ops`
- `["ko"]`
- 作用：事故后要求知识沉淀

### `research / builder / ko`
- 默认不再继续 fan-out，避免嵌套失控

## 推荐 heartbeat

| agent | 频率 | 重点检查 |
|------|------|---------|
| `cos` | 12h | 阻塞任务、引用链完整性、跨团队无响应 |
| `cio` | 24h | 是否产出当日 `decision_ref` |
| `cto` | 12h | 关键任务是否缺 `decision_ref / rollback_ref` |
| `ops` | 8h | 风险告警、数据新鲜度、live 变更是否都走审核 |
| `ko` | 48h | 是否有高 signal closeout 未沉淀 |

## bindings 路由原则

- 一个角色一个主频道，避免混杂上下文
- 一个任务一个 thread，避免状态散落
- `cos` 可以旁听 `#cio / #cto / #ops`
- `cto` 可以旁听 `#research`
- 不建议让 `builder` 同时监听多个业务频道

## sessions_send 与 sessions_spawn

### sessions_send
用于正式主流程：

- `CoS -> CIO`
- `CoS -> CTO`
- `CTO -> Builder`
- `CTO/CoS -> Ops`
- `CTO/CoS/Ops -> KO`

### sessions_spawn
只用于边车型并行任务：

- benchmark
- 连接器资料收集
- 事故后材料整理

## 量化场景的关键配置建议

### `agentToAgent.maxPingPongTurns`
- 推荐维持低值或 `0`
- 原因：量化场景里状态需要显式留痕，不要让自动 ping-pong 代替真实的 thread 记录

### `sessions.visibility`
- 推荐 `all`
- 原因：Ops / CoS / KO 需要跨团队追溯上下文

### credentials
- 交易所 API、Webhook、告警凭证只放环境变量或秘密管理
- `paper` 与 `live` 使用不同凭证，不混用

### paper / live 分离
- 推荐至少在命名与文档层显式区分：
  - `paper-...`
  - `live-...`
- 所有 live 相关任务都必须显式出现 `review_ref`

## 标准主线

### 策略上线
1. `research` 输出 benchmark
2. `cio` 输出 `decision_ref`
3. `cto` 生成任务包
4. `builder` 提交验证结果
5. `ops` 生成 `review_ref`
6. `cos` 安排 rollout
7. `ko` 记录知识

### 异常处理
1. `ops` 先保护
2. `cos` 重排优先级
3. `cio` 重估风险预算
4. `cto/builder` 修复
5. `ko` 写 scar

## 不建议的配置

- 用一个频道承载所有策略、执行、审核和事故
- 让 Builder 直接接收用户生产指令
- 跳过 `ops` 让 `cto` 或 `builder` 自行放行 live
- 把实盘和仿真复用同一个凭证和状态存储
