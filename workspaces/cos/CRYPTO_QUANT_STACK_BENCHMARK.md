# Crypto Quant Stack Benchmark (2026Q2)

## 目标

把 OpenCrew 的多 Agent 编排层，升级成适配 OpenClaw 的 **加密量化交易控制台**。

这里不只看“谁火”，而是看三件事：

- 是否有成熟的研究 / 回测 / live 经验可借鉴
- 是否适合映射到 `cio / cto / builder / ops / ko`
- 是否能为 OpenClaw 的 thread + session 协作提供清晰分层

## 当前最值得对标的系统

### 1. Freqtrade
- 类型：开源、Python、偏中低频策略交易
- 为什么值得参考：
  - 回测、dry-run、hyperopt、Web UI、策略插件体系较完整
  - 社区活跃，适合 CTA / 择时 / 因子筛选的研究到仿真闭环
- 我们借什么：
  - `strategy runtime`
  - `backtest / dry-run baseline`
  - `strategy config` 与参数化工作流
- 不直接照搬什么：
  - 不把 OpenClaw 变成单机器人交易框架
  - 不把所有交易逻辑都塞进一个进程或一个 agent

### 2. Hummingbot
- 类型：开源、做市 / 套利 / 多 venue 执行框架
- 为什么值得参考：
  - CEX / DEX 连接器能力强
  - 更关注订单簿、执行与策略脚本，不只看 K 线信号
- 我们借什么：
  - `connector + executor` 设计
  - 做市、套利、执行器扩展模型
- 不直接照搬什么：
  - 不让做市逻辑覆盖所有团队流程
  - 不让执行器绕过 Ops 闸门直接 live

### 3. QuantConnect LEAN
- 类型：成熟事件驱动量化引擎
- 为什么值得参考：
  - 研究、回测、live 采用统一事件模型
  - 对“策略逻辑”和“订单/风控/经纪商适配”分层清楚
- 我们借什么：
  - `research / production parity`
  - 事件驱动状态机
  - 策略、订单、风险的职责切分
- 不直接照搬什么：
  - 不迁移整套平台
  - 不引入与 OpenClaw 协作无关的大而全资产支持层

### 4. NautilusTrader
- 类型：工程化程度更高的事件驱动交易平台
- 为什么值得参考：
  - 面向 live 与 backtest 一致性的架构清晰
  - 更强调订单生命周期、数据建模与状态存证
- 我们借什么：
  - `order manager + portfolio + risk engine + adapters`
  - 更严格的执行面与存证面边界
- 不直接照搬什么：
  - 不在第一阶段追求其复杂度和全量抽象

### 5. Jesse
- 类型：以交易员体验为导向的加密量化框架
- 为什么值得参考：
  - 策略开发体验好，研究和交易者语言距离近
  - 对单策略开发、回测、参数调试很顺手
- 我们借什么：
  - `researcher / trader friendly` 的策略接口
  - 快速试错与回放体验
- 不直接照搬什么：
  - 不让单策略体验压倒团队级治理和审计

### 6. OctoBot
- 类型：全栈机器人产品，偏运营与自动化
- 为什么值得参考：
  - 更接近终端用户视角，有自动化、Web 管理、交易所接入与产品化外壳
  - 对“操作便利性”比纯框架更敏感
- 我们借什么：
  - 控制台视角
  - 自动化任务、模板、用户操作路径
- 不直接照搬什么：
  - 不牺牲工程与风控边界去换一体化体验

### 7. 3Commas
- 类型：商业化交易机器人平台
- 为什么值得参考：
  - 代表用户对“策略模板、自动化、信号接入、运营可视化”的真实需求
  - 更像产品层而不是底层引擎
- 我们借什么：
  - 用户入口与运营编排思路
  - 策略参数、信号触发、运行监控的交互组织方式
- 不直接照搬什么：
  - 不依赖 SaaS 封闭能力
  - 不把核心执行与风控外包给黑盒

## 热度结论

如果以 2026Q2 的“社区讨论度 + 官方文档成熟度 + GitHub / 产品活跃度 + 可复用性”综合判断：

- **研究回测主线**：`Freqtrade`
- **做市/套利执行主线**：`Hummingbot`
- **架构参考主线**：`LEAN + NautilusTrader`
- **产品化运营主线**：`OctoBot + 3Commas`

最适合 OpenClaw 团队的不是“选一个系统全盘照抄”，而是做 **混合式参考架构**。

## OpenClaw 量化版目标架构

### L1: Research & Decision Plane
- owner: `research + cio`
- 输入：市场、交易所、因子、成本、外部 benchmark
- 输出：`decision_ref`

### L2: Execution Engineering Plane
- owner: `cto + builder`
- 输入：`decision_ref + scope + DoD`
- 输出：回测、回放、paper、连接器、下单与回执追踪

### L3: Risk & Control Plane
- owner: `ops`
- 输入：变更申请、演练结果、巡检告警
- 输出：`review_ref / incident_ref / rollback_ref`

### L4: Knowledge & Governance Plane
- owner: `cos + ko`
- 输入：closeout、incident、review
- 输出：优先级调整、经验沉淀、流程升级

## 推荐落地路线

### Phase 1: 先做“可验证”
- 研究回测：`Python + vectorbt/freqtrade-style`
- 仿真：`replay + paper`
- 执行：`ccxt + exchange native ws/rest`
- 风控：`daily loss cap / max leverage / reduce_only / kill-switch`
- 审计：`PostgreSQL + structured logs + decision/review refs`

### Phase 2: 再做“可扩展”
- 多 venue 路由
- basis / carry / market making 策略
- 更强的订单状态机
- 观察期自动报告

### Phase 3: 再做“可运营”
- 控制台工作流
- 自动巡检与异常路由
- 策略目录与上线模板

## 对 OpenClaw 团队的直接要求

- CoS 负责控制塔，而不是直接下单
- CIO 只做策略与风险预算决策，不碰执行细节
- CTO 负责把观点翻译成模块化任务包
- Builder 交付可运行产物与验证结果
- Ops 拥有上线否决权
- KO 负责把经验变成可复用知识

## 最小可运行系统

- 至少 2 条策略：`trend_follow / mean_reversion`
- 至少 1 家主交易所可完成 paper -> controlled live
- 至少 1 套统一的 `review_ref / rollback_ref / incident_ref` 机制
- 至少 1 个日常 heartbeat 检查 risk / fills / data freshness
- 每周固定形成“决策 -> 执行 -> 审核 -> 复盘 -> 知识”闭环

## 参考来源（官方）

- Freqtrade: https://www.freqtrade.io/ , https://github.com/freqtrade/freqtrade
- Hummingbot: https://hummingbot.org/ , https://github.com/hummingbot/hummingbot
- QuantConnect LEAN: https://www.quantconnect.com/docs/v2/lean-cli/key-concepts/introduction , https://github.com/QuantConnect/Lean
- NautilusTrader: https://nautilustrader.io/docs/latest/ , https://github.com/nautechsystems/nautilus_trader
- Jesse: https://docs.jesse.trade/ , https://github.com/jesse-ai/jesse
- OctoBot: https://www.octobot.cloud/ , https://github.com/Drakkar-Software/OctoBot
- 3Commas: https://3commas.io/
