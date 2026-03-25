# HEARTBEAT.md - TradingAgents 心跳任务

## 定期检查任务

### 1. 市场数据更新检查 (每30分钟)
- 检查数据缓存是否过期
- 必要时刷新股票数据

### 2. 分析历史整理 (每小时)
- 检查 `memory/` 目录
- 清理超过7天的旧记录
- 更新每日分析汇总

### 3. 系统健康检查 (每15分钟)
- 检查 LLM API 连接
- 检查数据源可用性
- 检查日志文件大小

## 任务说明

1. **市场数据更新**: 确保分析的股票数据是最新的
2. **历史整理**: 保持 memory 目录整洁，避免浪费空间
3. **系统健康**: 及时发现问题，避免分析失败

## 状态追踪

检查状态保存在 `memory/heartbeat-state.json`：
```json
{
  "lastChecks": {
    "marketData": null,
    "historyCleanup": null,
    "systemHealth": null
  }
}
```

## 注意事项

- 心跳执行时间尽量分散，避免集中
- 简单任务快速完成，复杂任务可跳过
- 无事发生时回复 `HEARTBEAT_OK`
