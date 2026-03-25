# Skill: skill-tao-sentiment

## 描述

情绪分析师 Skill，分析新闻、社交媒体情绪，生成市场情绪报告。

## 职责

- 采集并分析股票相关新闻
- 评估新闻情绪倾向（正面/负面/中性）
- 识别关键事件和催化剂
- 分析情绪变化趋势
- 生成情绪信号和置信度

## 输入

```json
{
  "trace_id": "uuid-string",
  "stock_symbol": "AAPL",
  "analysis_date": "2026-03-24",
  "config": {
    "llm_provider": "openai",
    "model": "gpt-4o",
    "news_limit": 20
  }
}
```

## 输出

```json
{
  "trace_id": "uuid-string",
  "success": true,
  "report": {
    "agent_type": "sentiment",
    "stock_symbol": "AAPL",
    "signal": "buy",
    "confidence": 0.72,
    "reasoning": "近期新闻情绪偏正面...",
    "key_metrics": {
      "sentiment_score": 0.65,
      "positive_news_pct": 60,
      "negative_news_pct": 20,
      "neutral_news_pct": 20
    },
    "risks": ["财报前情绪可能反转"]
  }
}
```

## 数据源

- Yahoo Finance News
- Alpha Vantage News
- 新闻情绪分析

## 分析方法

1. 获取近期新闻
2. LLM 分析每条新闻情绪
3. 统计情绪分布
4. 识别关键事件
5. 生成情绪信号
