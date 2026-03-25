---
name: skill-tao-fundamental
description: "基本面分析师 Skill。分析公司财务数据、估值指标、盈利能力等基本面信息。当用户请求基本面分析、财务分析、估值分析时激活。"
metadata:
  {
    "openclaw": { "emoji": "📊", "requires": {} }
  }
---

# Skill: skill-tao-fundamental

## 描述

基本面分析师 Skill，分析公司财务数据、估值指标、盈利能力等基本面信息，生成投资建议。

## 职责

- 分析公司财务健康状况
- 评估估值水平 (P/E, P/B, PEG 等)
- 评估盈利能力和增长趋势
- 识别潜在风险
- 生成基本面评级 (BUY/SELL/HOLD)

## 调用方式

```python
from skill_tao_fundamental.fundamental_analyst import FundamentalAnalyst

analyst = FundamentalAnalyst(config={"llm_provider": "openai", "model": "gpt-4o"})
result = analyst.analyze({
    "trace_id": "uuid",
    "stock_symbol": "AAPL",
    "analysis_date": "2026-03-25"
})
```

## 输入

```json
{
  "trace_id": "uuid-string",
  "stock_symbol": "AAPL",
  "analysis_date": "2026-03-25",
  "config": {
    "llm_provider": "openai",
    "model": "gpt-4o",
    "temperature": 0.7
  }
}
```

## 输出

```json
{
  "success": true,
  "report": {
    "agent_type": "fundamental",
    "stock_symbol": "AAPL",
    "signal": "buy",
    "confidence": 0.82,
    "reasoning": "详细分析理由...",
    "key_metrics": {
      "pe_ratio": 28.5,
      "pb_ratio": 8.2,
      "revenue_growth": 0.15,
      "profit_margin": 0.25
    },
    "risks": ["估值偏高", "市场竞争加剧"]
  }
}
```

## 依赖

- skill-tao-data (数据层)
- OpenAI/Anthropic LLM