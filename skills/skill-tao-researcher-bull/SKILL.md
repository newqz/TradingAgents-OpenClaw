# Skill: skill-tao-researcher-bull

## 描述

看多研究员 Skill，从乐观角度分析投资标的，发现增长机会。

## 职责

- 从分析师报告中提取看涨论据
- 发现被低估的价值和增长潜力
- 回应看空方的质疑
- 构建看多方论证

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
  "opponent_argument": "...",  // 看空方的观点（如果有）
  "round": 1
}
```

## 输出

```json
{
  "trace_id": "uuid-string",
  "view": "bullish",
  "confidence": 0.85,
  "argument": "看多论据...",
  "key_points": ["..."],
  "response_to_bear": "对看空观点的回应..."
}
```
