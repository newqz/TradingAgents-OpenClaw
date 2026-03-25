# Skill: skill-tao-researcher-bear

## 描述

看空研究员 Skill，从悲观角度分析投资风险，发现潜在问题。

## 职责

- 从分析师报告中提取风险因素
- 发现估值过高或增长放缓迹象
- 回应看多方的论点
- 构建看空方论证

## 输入

```json
{
  "trace_id": "uuid-string",
  "stock_symbol": "AAPL",
  "research_summary": "...",
  "analyst_reports": {
    "fundamental": {...},
    "technical": {...},
    "sentiment": {...}
  },
  "opponent_argument": "...",  // 看多方的观点（如果有）
  "round": 1
}
```

## 输出

```json
{
  "trace_id": "uuid-string",
  "view": "bearish",
  "confidence": 0.75,
  "argument": "看空论据...",
  "key_points": ["..."],
  "response_to_bull": "对看多观点的回应..."
}
```
