---
name: skill-tao-trading
description: "TradingAgents 完整交易分析系统。执行完整三阶段分析流程：Phase 1 三分析师 (基本面/技术面/情绪面) 并行分析 → Phase 2 研究员多空辩论 → Phase 3 交易员辩论 + 风险管理 + 最终决策。当用户请求股票分析、投资建议、交易决策时激活。输入股票代码，返回完整分析报告和交易建议。"
metadata:
  {
    "openclaw": { "emoji": "📈", "requires": {} }
  }
---

# TradingAgents-OpenClaw Skill

## 描述

完整的三阶段量化交易分析系统：

### Phase 1: 三分析师并行
- 📊 **Fundamental Analyst** - 基本面分析 (财务、估值、盈利)
- 📈 **Technical Analyst** - 技术面分析 (趋势、指标、形态)
- 💬 **Sentiment Analyst** - 情绪面分析 (新闻、社交媒体)

### Phase 2: 研究员辩论
- 🐂 **Bull Researcher** - 看多观点
- 🐻 **Bear Researcher** - 看空观点
- 📋 **Research Manager** - 综合裁决

### Phase 3: 交易员决策
- 🟢 **Bull Trader** - 激进做多
- 🟡 **Neutral Trader** - 中性观望
- 🔴 **Bear Trader** - 保守做空
- ⚠️ **Risk Manager** - 风险评估
- 🎯 **Portfolio Manager** - 最终决策

## 调用方式

### 方式 1: 直接执行 (Python)

```python
import asyncio
import sys
sys.path.insert(0, '/root/.openclaw/workspace/TradingAgents-OpenClaw')

from master_agent.orchestrator_phase3 import TradingOrchestrator
from shared.models import TAOConfig, FeishuCommand
from datetime import datetime

async def analyze():
    orchestrator = TradingOrchestrator()
    command = FeishuCommand(
        command="analyze",
        stock_symbols=["NVDA"],
        analysis_date=datetime.now().strftime("%Y-%m-%d"),
        user_id="user123",
        chat_id="chat456"
    )
    result = await orchestrator.process_command(command)
    return result

result = asyncio.run(analyze())
print(f"决策: {result.final_decision.action}")
print(f"置信度: {result.final_decision.confidence}")
```

### 方式 2: Shell 命令

```bash
cd /root/.openclaw/workspace/TradingAgents-OpenClaw
python3 -c "
import asyncio
import sys
sys.path.insert(0, '.')
from master_agent.orchestrator_phase3 import TradingOrchestrator
from shared.models import FeishuCommand
from datetime import datetime

async def main():
    orchestrator = TradingOrchestrator()
    result = await orchestrator.process_command(FeishuCommand(
        command='analyze',
        stock_symbols=['NVDA'],
        analysis_date=datetime.now().strftime('%Y-%m-%d')
    ))
    print(f'Final Decision: {result.final_decision.action}')

asyncio.run(main())
"
```

### 方式 3: OpenClaw sessions_spawn (推荐生产使用)

```javascript
// 在 OpenClaw 中调用
sessions_spawn({
    runtime: "subagent",
    task: "执行 TradingAgents 分析: 分析 AAPL",
    cwd: "/root/.openclaw/workspace/TradingAgents-OpenClaw"
})
```

## 输入

```json
{
  "command": "analyze",
  "stock_symbols": ["NVDA", "AAPL"],
  "analysis_date": "2026-03-25",
  "user_id": "user123",
  "chat_id": "chat456"
}
```

## 输出

```json
{
  "trace_id": "abc123",
  "stock_symbol": "NVDA",
  "status": "completed",
  "fundamental_report": { "signal": "buy", "confidence": 0.85 },
  "technical_report": { "signal": "buy", "confidence": 0.78 },
  "sentiment_report": { "signal": "hold", "confidence": 0.62 },
  "research_summary": { "overall_signal": "buy", "confidence": 0.75 },
  "trader_recommendations": [
    { "trader_type": "bull", "action": "buy" },
    { "trader_type": "neutral", "action": "hold" },
    { "trader_type": "bear", "action": "sell" }
  ],
  "risk_assessment": { "overall_risk": "medium", "risk_score": 55 },
  "final_decision": {
    "action": "buy",
    "confidence": 0.72,
    "position_size": "medium",
    "risk_level": "medium"
  }
}
```

## 文件结构

```
TradingAgents-OpenClaw/
├── master-agent/
│   ├── orchestrator_phase3.py    # 完整编排器
│   ├── portfolio_manager.py      # 最终决策
│   ├── trader_debate_orchestrator.py  # 交易员辩论
│   └── feishu_adapter.py         # 飞书适配
├── skills/
│   ├── skill-tao-fundamental/   # 基本面分析
│   ├── skill-tao-technical/     # 技术分析
│   ├── skill-tao-sentiment/     # 情绪分析
│   ├── skill-tao-research-manager/  # 研究整合
│   └── skill-tao-trader/        # 交易员
└── shared/
    └── models.py                # 数据模型
```

## 依赖

- Python 3.8+
- openai >= 1.0.0
- pandas >= 2.0.0
- yfinance >= 0.2.28