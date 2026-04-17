# HEARTBEAT — Ops

## 检查项
- [ ] 有待审核的Self-Update？
- [ ] 有S类closeout待review？
- [ ] 系统是否有异常？
- [ ] 今日三次巡检是否完成并记录？
- [ ] 是否存在未绑定 `review_ref/rollback_ref` 的实盘变更？
- [ ] 是否有需升级为 incident 的未闭环事件？

## 量化巡检命令
- `cd quant-stack && PYTHONPATH=src python3 -m opencrew_quant run-binance-reconcile-loop --decision-ref OPS-HB-<date> --order-mode test --symbol BTC/USDT:USDT --limit 5 --iterations 1 --interval-s 0`
- `cd quant-stack && PYTHONPATH=src python3 -m opencrew_quant report-binance-health --max-age-minutes 30`

## 输出格式
- `status`: ok | action_required
- `actions`: 下一步动作（最多 3 条）
- `refs`: 相关 decision_ref / review_ref / incident_ref
