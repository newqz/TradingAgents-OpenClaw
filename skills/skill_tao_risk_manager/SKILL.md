# Skill: skill-tao-risk-manager

## 描述

风险管理 Skill，评估交易风险，给出风控建议。

## 职责

- 评估市场风险
- 评估个股特定风险
- 给出仓位限制建议
- 识别关键风险因素

## 输入

```json
{
  "stock_symbol": "AAPL",
  "research_summary": {...},
  "trader_recommendations": [...],
  "market_context": {...}
}
```

## 输出

```json
{
  "overall_risk": "medium",
  "risk_score": 65,
  "position_limit_pct": 10,
  "risk_factors": [...],
  "warnings": [...]
}
```
