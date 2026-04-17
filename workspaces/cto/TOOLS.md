# TOOLS — CTO Local Notes

## Skills（能力嫁接）
Skills 是 OpenClaw 已安装的“能力包”（不需要在 workspace 里建 skills 文件夹）。

- 查看可用技能：`openclaw skills list`
- 检查技能依赖是否齐备：`openclaw skills check`

当任务需要专用能力（例如 GitHub、Obsidian、Reminders、Feishu 等），优先使用对应 skill 的工作流。

## 开发环境
- （根据实际配置添加）

## 凭证位置
- （不写明文，只写位置）

## 常用命令备忘
- （根据实际情况添加）

## Futures 协作文件

- `patterns/regime-switch-execution.md`
- `../cio/signals/regime-routing.md`
- `../ops/live-change-review.md`
- `SYSTEM_BLUEPRINT.md`
- `../cos/QUANT_OPERATING_MODEL.md`
- `templates/EXECUTION_TASK_PACKET_TEMPLATE.md`

## 推荐实现路线（默认）
- 研究与回测：Freqtrade 风格（Python）
- 执行连接：ccxt + 交易所原生 ws/rest
- 审计存证：订单/成交/仓位/切换事件必须可追溯
