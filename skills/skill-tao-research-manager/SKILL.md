# Skill: skill-tao-research-manager

## 描述

研究经理 Skill，整合多空双方辩论，输出综合研判。

## 职责

- 审视多空双方的论证
- 识别共识和分歧点
- 评估双方论据的强度
- 输出最终研究结论

## 输入

```json
{
  "trace_id": "uuid-string",
  "stock_symbol": "AAPL",
  "debate_history": [
    {
      "round": 1,
      "bull_view": {...},
      "bear_view": {...}
    }
  ],
  "analyst_reports": {...}
}
```

## 输出

```json
{
  "trace_id": "uuid-string",
  "overall_signal": "buy",
  "confidence": 0.78,
  "consensus_level": 0.6,
  "key_insights": ["..."],
  "contradictions": ["..."],
  "reasoning": "综合研判..."
}
```
