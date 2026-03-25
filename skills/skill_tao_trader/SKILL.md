---
name: skill-tao-trader
description: "交易员辩论 Skill。三交易员 (Bull/Neutral/Bear) 提供交易建议，RiskManager 进行风险评估，PortfolioManager 生成最终决策。当需要交易决策、投资建议时激活。"
metadata:
  {
    "openclaw": { "emoji": "💹", "requires": {} }
  }
---

# Skill: skill-tao-trader

## 描述

交易员辩论与风险管理模块，包含：
1. **BullTrader** - 激进交易员，倾向做多
2. **NeutralTrader** - 中性交易员，观望等待
3. **BearTrader** - 保守交易员，倾向减仓
4. **RiskManager** - 风险评估
5. **PortfolioManager** - 最终决策

## 调用方式

```python
# 交易员辩论
from trader_debate_orchestrator import TraderDebateOrchestrator

orchestrator = TraderDebateOrchestrator()
recommendations = orchestrator.run_trader_debate(symbol="AAPL", research=summary)
risk = orchestrator.assess_risk(symbol="AAPL", research=summary, traders=recommendations)

# 最终决策
from portfolio_manager import PortfolioManager
pm = PortfolioManager()
decision = pm.decide_simple(symbol="AAPL", research=summary, traders=recommendations, risk=risk)
```

## 组件

### TraderDebateOrchestrator
- `run_trader_debate()` - 获取三位交易员建议
- `assess_risk()` - 进行风险评估

### PortfolioManager
- `decide_simple()` - 简化版决策 (无需 LLM)
- `decide()` - 完整决策 (需要 LLM)

## 输出 - 最终决策

```json
{
  "action": "buy",
  "confidence": 0.75,
  "position_size": "medium",
  "risk_level": "medium",
  "reasoning": "综合交易员建议和风险评估..."
}
```

## 决策规则

| 风险等级 | 仓位建议 |
|---------|---------|
| LOW | large (15-20%) |
| MEDIUM | medium (8-12%) |
| HIGH | small (3-7%) |
| EXTREME | minimal (1-2%) |