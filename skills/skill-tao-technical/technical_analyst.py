"""
技术面分析师 Skill
分析价格走势和技术指标，生成技术面交易报告
"""

import os
import json
from typing import Any, Dict, List, Optional
from datetime import datetime

# 导入共享模型
import sys
sys.path.insert(0, '/root/.openclaw-coding/workspace/TradingAgents-OpenClaw')
from shared.models import (
    AnalystInput, AnalystOutput, AnalystReport,
    TradingSignal, AgentType, TokenUsage
)

# 导入数据层
sys.path.insert(0, '/root/.openclaw-coding/workspace/TradingAgents-OpenClaw/skills/skill-tao-data')
from skill_tao_data import get_data_provider


# 技术面分析系统提示词
TECHNICAL_ANALYST_PROMPT = """You are a professional technical analyst with 15 years of experience in chart analysis and algorithmic trading.

Your task is to analyze the provided stock's price action and technical indicators to generate a trading signal.

## Analysis Framework

1. **Trend Analysis**
   - Primary trend direction (uptrend, downtrend, sideways)
   - Trend strength and sustainability
   - Moving average alignment (bullish/bearish alignment)

2. **Momentum Analysis**
   - RSI level and divergence signals
   - MACD trend and signal line crossovers
   - Momentum confirmation or divergence

3. **Volatility Analysis**
   - Bollinger Bands position (squeeze, expansion)
   - Price position relative to bands
   - Volatility regime (high/low)

4. **Support/Resistance Levels**
   - Key support levels from recent price action
   - Key resistance levels to watch
   - Fibonacci retracement levels if applicable

5. **Volume Analysis**
   - Volume trend confirmation
   - Volume spikes and their significance

## Trading Signal Guidelines

- **BUY**: Price in uptrend + momentum positive + not overbought
- **SELL**: Price in downtrend + momentum negative + not oversold
- **HOLD**: Mixed signals, consolidation, or counter-trend extremes

## Output Format

Respond in the following JSON format:

```json
{
  "signal": "buy|sell|hold",
  "confidence": 0.75,
  "reasoning": "Detailed technical analysis...",
  "key_metrics": {
    "current_price": 175.50,
    "rsi": 32.5,
    "macd_signal": "bullish_crossover",
    "trend": "uptrend",
    "sma_20": 170.0,
    "sma_50": 165.0,
    "support_level": 168.0,
    "resistance_level": 180.0
  },
  "risks": ["Risk 1", "Risk 2"]
}
```

Be precise in your technical analysis. Consider multiple indicators for confirmation."""


class TechnicalAnalyst:
    """技术面分析师"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.data_provider = get_data_provider()
        self.llm_client = self._init_llm_client()
    
    def _init_llm_client(self):
        """初始化 LLM 客户端"""
        provider = self.config.get("llm_provider", "openai")
        
        if provider == "openai":
            try:
                from openai import OpenAI
                return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            except ImportError:
                raise ImportError("openai package required: pip install openai")
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    
    def analyze(self, input_data: AnalystInput) -> AnalystOutput:
        """
        执行技术面分析
        
        Args:
            input_data: 分析输入
            
        Returns:
            AnalystOutput: 分析结果
        """
        import time
        start_time = time.time()
        
        try:
            symbol = input_data.stock_symbol
            
            print(f"[{input_data.trace_id}] Fetching technical data for {symbol}...")
            
            # 1. 获取价格数据
            price_data = self.data_provider.get_stock_data(
                symbol=symbol,
                period="6mo",
                interval="1d"
            )
            
            # 2. 获取技术指标
            indicators = self.config.get(
                "indicators",
                ["rsi", "macd", "bollinger_bands", "sma", "ema"]
            )
            
            technical_data = self.data_provider.get_indicators(
                symbol=symbol,
                indicators=indicators,
                period="6mo"
            )
            
            # 3. 计算额外的技术指标
            additional_metrics = self._calculate_additional_metrics(price_data)
            
            # 4. 构建分析提示词
            prompt = self._build_analysis_prompt(
                symbol=symbol,
                price_data=price_data,
                technical_data=technical_data,
                additional_metrics=additional_metrics
            )
            
            # 5. 调用 LLM 分析
            print(f"[{input_data.trace_id}] Analyzing technicals with LLM...")
            
            response = self.llm_client.chat.completions.create(
                model=self.config.get("model", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": TECHNICAL_ANALYST_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config.get("temperature", 0.7),
                response_format={"type": "json_object"}
            )
            
            analysis_text = response.choices[0].message.content
            analysis_json = json.loads(analysis_text)
            
            # 6. 构建报告
            report = AnalystReport(
                agent_type=AgentType.TECHNICAL,
                stock_symbol=symbol,
                signal=TradingSignal(analysis_json.get("signal", "hold")),
                confidence=analysis_json.get("confidence", 0.5),
                reasoning=analysis_json.get("reasoning", ""),
                key_metrics=analysis_json.get("key_metrics", {}),
                risks=analysis_json.get("risks", []),
                raw_output=analysis_text
            )
            
            # 7. 计算使用量
            token_usage = self._get_token_usage(response)
            latency_ms = int((time.time() - start_time) * 1000)
            
            print(f"[{input_data.trace_id}] Technical analysis completed in {latency_ms}ms")
            
            return AnalystOutput(
                trace_id=input_data.trace_id,
                success=True,
                report=report,
                latency_ms=latency_ms,
                token_usage=token_usage
            )
            
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            
            print(f"[{input_data.trace_id}] Technical analysis failed: {e}")
            
            return AnalystOutput(
                trace_id=input_data.trace_id,
                success=False,
                error=str(e),
                latency_ms=latency_ms
            )
    
    def _calculate_additional_metrics(self, price_data: Dict) -> Dict:
        """计算额外的技术指标"""
        try:
            import pandas as pd
            
            df = pd.DataFrame(price_data.get("data", []))
            if df.empty:
                return {}
            
            # 确保 Close 列存在
            close_col = "Close" if "Close" in df.columns else "close"
            if close_col not in df.columns:
                return {}
            
            closes = df[close_col]
            
            # 计算支撑阻力位（简化版：近期高低点）
            support = closes.tail(20).min()
            resistance = closes.tail(20).max()
            
            # 当前价格
            current_price = closes.iloc[-1]
            
            # 20日价格变化
            price_change_20d = (closes.iloc[-1] - closes.iloc[-20]) / closes.iloc[-20] * 100 if len(closes) >= 20 else 0
            
            # 波动率 (20日标准差)
            volatility = closes.tail(20).std() / closes.tail(20).mean() * 100
            
            return {
                "current_price": round(current_price, 2),
                "support_level_20d": round(support, 2),
                "resistance_level_20d": round(resistance, 2),
                "price_change_20d_pct": round(price_change_20d, 2),
                "volatility_20d_pct": round(volatility, 2)
            }
            
        except Exception as e:
            print(f"Error calculating additional metrics: {e}")
            return {}
    
    def _build_analysis_prompt(
        self,
        symbol: str,
        price_data: Dict,
        technical_data: Dict,
        additional_metrics: Dict
    ) -> str:
        """构建分析提示词"""
        
        # 提取最近的价格数据
        recent_data = price_data.get("data", [])[-30:]  # 最近30天
        
        # 格式化价格数据
        price_summary = []
        for day in recent_data[-5:]:  # 最近5天
            date = day.get("Date", day.get("date", "N/A"))
            close = day.get("Close", day.get("close", "N/A"))
            volume = day.get("Volume", day.get("volume", "N/A"))
            price_summary.append(f"{date}: Close=${close}, Volume={volume}")
        
        # 提取技术指标
        indicators = technical_data.get("indicators", {})
        
        rsi_data = indicators.get("rsi", {})
        macd_data = indicators.get("macd", {})
        bb_data = indicators.get("bollinger_bands", {})
        sma_data = indicators.get("sma", {})
        
        prompt = f"""Please analyze the following technical data for {symbol}:

## Price Summary (Last 5 Days)
{chr(10).join(price_summary)}

## Technical Indicators

### RSI
- Value: {rsi_data.get('value', 'N/A')}
- Interpretation: {rsi_data.get('interpretation', 'N/A')}

### MACD
- MACD Line: {macd_data.get('macd', 'N/A')}
- Signal Line: {macd_data.get('signal', 'N/A')}
- Histogram: {macd_data.get('histogram', 'N/A')}
- Trend: {macd_data.get('trend', 'N/A')}

### Bollinger Bands
- Upper Band: {bb_data.get('upper', 'N/A')}
- Middle Band (SMA 20): {bb_data.get('middle', 'N/A')}
- Lower Band: {bb_data.get('lower', 'N/A')}
- Position: {bb_data.get('position', 'N/A')}

### Moving Averages
- SMA 20: {sma_data.get('sma_20', 'N/A')}
- SMA 50: {sma_data.get('sma_50', 'N/A')}

## Additional Metrics
- Current Price: ${additional_metrics.get('current_price', 'N/A')}
- 20-Day Support: ${additional_metrics.get('support_level_20d', 'N/A')}
- 20-Day Resistance: ${additional_metrics.get('resistance_level_20d', 'N/A')}
- 20-Day Return: {additional_metrics.get('price_change_20d_pct', 'N/A')}%
- 20-Day Volatility: {additional_metrics.get('volatility_20d_pct', 'N/A')}%

Please provide a comprehensive technical analysis with:
1. Overall trend assessment
2. Key technical signals
3. Support/resistance levels
4. Trading signal (buy/sell/hold) with confidence
5. Risk factors
"""
        
        return prompt
    
    def _get_token_usage(self, response) -> TokenUsage:
        """获取 token 使用情况"""
        usage = response.usage if hasattr(response, 'usage') else None
        
        if usage:
            prompt_cost = usage.prompt_tokens * 0.000000165
            completion_cost = usage.completion_tokens * 0.00000066
            
            return TokenUsage(
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                total_tokens=usage.total_tokens,
                cost_usd=round(prompt_cost + completion_cost, 6)
            )
        
        return TokenUsage()


# 便捷函数
def analyze_technicals(
    symbol: str,
    trace_id: Optional[str] = None,
    config: Optional[Dict] = None
) -> AnalystOutput:
    """
    便捷函数：分析股票技术面
    
    使用示例:
        result = analyze_technicals("AAPL")
        print(result.report.signal)
        print(result.report.key_metrics.get("rsi"))
    """
    from shared.models import AnalystInput
    
    analyst = TechnicalAnalyst(config=config)
    
    input_data = AnalystInput(
        trace_id=trace_id or f"tech_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        stock_symbol=symbol,
        analysis_date=datetime.now().strftime("%Y-%m-%d"),
        config=config or {}
    )
    
    return analyst.analyze(input_data)


if __name__ == "__main__":
    # 测试
    print("Testing Technical Analyst...")
    
    result = analyze_technicals(
        symbol="AAPL",
        config={
            "llm_provider": "openai",
            "model": "gpt-4o-mini",
            "temperature": 0.7,
            "indicators": ["rsi", "macd", "bollinger_bands", "sma"]
        }
    )
    
    if result.success:
        print(f"\nAnalysis Result for {result.report.stock_symbol}:")
        print(f"Signal: {result.report.signal.value}")
        print(f"Confidence: {result.report.confidence}")
        print(f"Key Metrics: {result.report.key_metrics}")
        print(f"Latency: {result.latency_ms}ms")
    else:
        print(f"Analysis failed: {result.error}")
