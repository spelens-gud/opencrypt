# Crypto Quant Stack Benchmark (Updated 2026-04-18)

## 目标

把 OpenCrew 的多 Agent 编排层，升级成适配 OpenClaw 的 **加密量化交易控制台**。

这里不只看“谁火”，而是看三件事：

- 是否有成熟的研究 / 回测 / live 经验可借鉴
- 是否适合映射到 `cio / cto / builder / ops / ko`
- 是否能为 OpenClaw 的 thread + session 协作提供清晰分层

## 当前最值得对标的系统

> 下面的“热度”优先参考 2026-04-18 当天官方 GitHub 仓库 / 官方站点可见信息、官方文档成熟度、以及它是否真能映射到 OpenClaw 的多 Agent 职责链。

| 系统 | 当前热度信号 | 更适合什么 | 我们借什么 | 不借什么 |
|------|-------------|-----------|-----------|---------|
| **Freqtrade** | GitHub `46.6k` stars；官方定位是开源 crypto trading bot | 中低频 CTA、回测、dry-run、参数迭代 | 回测/仿真基线、策略参数化、研究工作流 | 单进程包揽全栈 |
| **LEAN** | GitHub `16.3k` stars；研究/回测/live 一致性成熟 | 研究到生产一致性、事件驱动状态机 | phase gate、broker/risk 分层、研究/生产 parity | 全资产全平台的大而全迁移 |
| **Hummingbot** | GitHub `15.5k` stars；官方文档强调 connectors / executors / Dashboard / Gateway | 做市、套利、执行器、订单簿驱动 | connector/executor 抽象、执行器扩展、订单生命周期、多 bot 编排 | 让执行器直接越过治理闸门 |
| **NautilusTrader** | GitHub `17.3k` stars；官方强调 deterministic event-driven | 工程化 live/backtest 一致性、强状态模型 | 订单状态机、适配器、审计边界 | 第一阶段就追求其复杂度 |
| **Jesse** | GitHub `7.3k` stars；交易员友好 | 策略试错、回放、研究体验 | trader-friendly 策略接口、快速反馈 | 过度偏单策略开发体验 |
| **OctoBot** | GitHub `5k+` stars；官方强调 Web/Mobile/Telegram 控制台与模板化策略 | 产品化运营、控制台、模板化运行 | 控制台视角、操作路径、面向用户的监控组织 | 一体化 UI 驱动底层架构 |
| **3Commas** | 商业平台；官方页面强调 DCA/Grid/Signal/SmartTrade 与控制台 | 面向终端用户的 bot 产品、运营编排 | dashboard、bot 模板、策略入口与管理体验 | 黑盒执行、SaaS 依赖 |

## 本地 clone 结果

已按 2026-04-18 的调研结果将主要开源参考系统 clone 到本地，便于后续直接读源码和文档做 lane 映射：

| 系统 | 本地路径 |
|------|---------|
| Freqtrade | `.benchmarks/external/freqtrade` |
| Hummingbot | `.benchmarks/external/hummingbot` |
| QuantConnect LEAN | `.benchmarks/external/lean` |
| NautilusTrader | `.benchmarks/external/nautilus_trader` |
| Jesse | `.benchmarks/external/jesse` |
| OctoBot | `.benchmarks/external/octobot` |

> `3Commas` 是商业产品，没有可 clone 的官方开源主仓，保留为产品层 benchmark。

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
  - Dashboard/多实例运维组织方式
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
  - 官方产品页强调 `DCA / Grid / Signal / SmartTrade`、回测和统一控制台，这代表真实市场对 bot 产品的入口预期
  - 更像产品层而不是底层引擎
- 我们借什么：
  - 用户入口与运营编排思路
  - 策略参数、信号触发、运行监控的交互组织方式
- 不直接照搬什么：
  - 不依赖 SaaS 封闭能力
  - 不把核心执行与风控外包给黑盒

## 交易逻辑摘要

### Freqtrade / Jesse：方向型研究主线
- 共同点：
  - 策略逻辑主要围绕 K 线、指标、参数调优、回测和 paper/live 切换
  - 都强调“研究者快速试错”，适合做 `trend_follow / mean_reversion / breakout / ml_filter`
- 对 OpenClaw 的启发：
  - `research -> cio` 负责提出候选策略和阈值
  - `cto -> builder` 负责把方向策略转成可回放、可 paper 的执行闭环
  - 不应把全部治理收敛到策略 runtime 内部

### Hummingbot / NautilusTrader：执行器与状态机主线
- 共同点：
  - 更强调 connectors / adapters / executors / order lifecycle
  - 更适合 `market making / cross venue / basis carry / hedge rebalance`
- 对 OpenClaw 的启发：
  - `cto` 必须把任务包拆到 `data / execution / reconcile / risk`
  - `builder` 的验证不止是策略收益，还包括 orphan order、quote staleness、hedge mismatch
  - `ops` 对这类 lane 的审核重点必须从“收益”转向“状态一致性和失控保护”

### LEAN：模块化工作流主线
- 核心逻辑：
  - `Alpha -> Portfolio Construction -> Risk Management -> Execution`
  - 研究、回测、live 共享一套模块接口和数据流
- 对 OpenClaw 的启发：
  - `cio` 输出的不是模糊观点，而是对 `strategy_mix / risk_budget` 的模块化输入
  - `cto` 负责把输入变成各层模块契约
  - `ops` 永远在 `Execution` 前拥有硬闸门

### OctoBot / 3Commas：产品化 bot 主线
- 核心逻辑：
  - 用 DCA、Grid、Signal、SmartTrade、TradingView/Webhook 作为策略入口
  - 把“创建 bot、启停 bot、观察 bot、调整 bot”做成运营控制台
- 对 OpenClaw 的启发：
  - 量化团队不能只有研发链路，还要有 `signal relay / grid dca / operator console` 视角
  - CoS/Ops 需要管理 bot 模板、观察窗、健康检查，而不是只关心代码 merge

## 热度结论

如果以 2026-04-18 的“GitHub 热度 + 官方文档成熟度 + 产品活跃度 + 对 OpenClaw 可映射性”综合判断：

- **研究回测主线**：`Freqtrade`
- **做市/套利执行主线**：`Hummingbot`
- **架构参考主线**：`LEAN + NautilusTrader`
- **产品化运营主线**：`OctoBot + 3Commas`

最适合 OpenClaw 团队的不是“选一个系统全盘照抄”，而是做 **混合式参考架构**：

- `Freqtrade` 负责研究回测方法论
- `LEAN / NautilusTrader` 负责状态机和研究到生产一致性
- `Hummingbot` 负责执行器和 connector 设计
- `OctoBot / 3Commas` 负责控制台、运营与模板化体验

## 五条落地主线（strategy lanes）

外部系统对标后，OpenClaw 量化团队不再只区分“角色”，而是区分 5 条可执行主线：

1. `directional_alpha`
   - 代表系统：`Freqtrade / Jesse / LEAN`
   - 典型策略：`trend_follow / mean_reversion / breakout / ml_filter`
2. `basis_carry`
   - 代表系统：`Hummingbot / NautilusTrader / LEAN`
   - 典型策略：`funding_arbitrage / cash_and_carry / basis_neutral`
3. `microstructure_mm`
   - 代表系统：`Hummingbot / NautilusTrader`
   - 典型策略：`inventory_skew / grid market making / maker-taker hedge`
4. `signal_relay`
   - 代表系统：`OctoBot / 3Commas / Hummingbot`
   - 典型策略：`TradingView webhook / external alert router / AI advisory gate`
5. `grid_dca`
   - 代表系统：`OctoBot / 3Commas`
   - 典型策略：`grid / DCA ladder / basket rebalance`

后续所有 Task Card、decision、validation、ops review 都应该显式带 `strategy_lane`。

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

## 对这个仓库的直接改造要求

基于以上 benchmark，这个仓库不应继续停留在“模板化角色描述”。它至少要具备：

- 一套面向 `research -> decision -> build -> validate -> ops_review -> rollout -> observe -> knowledge` 的阶段门禁
- 一套可追溯的引用链：`decision_ref / validation_report_ref / review_ref / rollback_ref / incident_ref / knowledge_ref`
- 一套符合 OpenClaw 多智能体路由的工作区与 heartbeat 设计
- 一套与量化系统真实模块对应的 `data / signal / portfolio / execution / risk / audit / observability` 边界

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
- 3Commas: https://3commas.io/dca-bots/ , https://3commas.io/smart-trade
