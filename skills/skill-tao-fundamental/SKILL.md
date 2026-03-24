# Skill: skill-tao-fundamental

## 描述

基本面分析师 Skill，分析公司财务数据、估值指标、盈利能力等基本面信息，生成投资建议。

## 职责

- 分析公司财务健康状况
- 评估估值水平 (P/E, P/B, PEG 等)
- 评估盈利能力和增长趋势
- 识别潜在风险
- 生成基本面评级 (BUY/SELL/HOLD)

## 输入

```json
{
  "trace_id": "uuid-string",
  "stock_symbol": "AAPL",
  "analysis_date": "2026-03-24",
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
  "trace_id": "uuid-string",
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
  },
  "latency_ms": 3250,
  "token_usage": {
    "prompt_tokens": 2500,
    "completion_tokens": 800,
    "total_tokens": 3300,
    "cost_usd": 0.12
  }
}
```

## 数据源

- 公司概况 (sector, industry, description)
- 财务报表 (资产负债表、利润表、现金流量表)
- 估值指标 (P/E, P/B, PEG, EV/EBITDA)
- 盈利指标 (profit margin, ROE, ROA)

## 分析方法

1. 获取公司基本信息和财务数据
2. 计算关键财务比率
3. 与行业平均和历史数据对比
4. 识别优势、劣势、风险
5. 生成投资信号和置信度

## 提示词策略

使用系统提示词定义分析师角色，使用 few-shot 示例提高输出质量。

## 依赖

- skill-tao-data (数据层)
- OpenAI/Anthropic LLM
