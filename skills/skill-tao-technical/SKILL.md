# Skill: skill-tao-technical

## 描述

技术面分析师 Skill，分析股票价格走势、技术指标、支撑阻力位，生成技术面交易建议。

## 职责

- 分析价格趋势和动量
- 计算和解读技术指标 (RSI, MACD, 布林带, 均线等)
- 识别支撑和阻力位
- 分析成交量模式
- 生成技术面评级 (BUY/SELL/HOLD)

## 输入

```json
{
  "trace_id": "uuid-string",
  "stock_symbol": "AAPL",
  "analysis_date": "2026-03-24",
  "config": {
    "llm_provider": "openai",
    "model": "gpt-4o",
    "indicators": ["rsi", "macd", "bollinger_bands", "sma", "ema"]
  }
}
```

## 输出

```json
{
  "trace_id": "uuid-string",
  "success": true,
  "report": {
    "agent_type": "technical",
    "stock_symbol": "AAPL",
    "signal": "buy",
    "confidence": 0.75,
    "reasoning": "RSI显示超卖反弹...",
    "key_metrics": {
      "current_price": 175.50,
      "rsi": 32.5,
      "macd_signal": "bullish_crossover",
      "trend": "uptrend"
    },
    "risks": ["成交量不足", "上方阻力强"]
  }
}
```

## 分析指标

- **趋势指标**: SMA, EMA, 趋势线
- **动量指标**: RSI, MACD, Stochastic
- **波动率指标**: 布林带, ATR
- **成交量指标**: OBV, Volume MA
- **支撑阻力**: 近期高低点, 斐波那契回调

## 提示词策略

强调技术分析的客观性，结合多个指标综合判断，避免单一指标误导。
