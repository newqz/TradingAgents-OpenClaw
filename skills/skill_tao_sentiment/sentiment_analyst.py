"""
情绪分析师 Skill
分析新闻情绪，生成市场情绪报告
"""

import os
import json
import importlib
from typing import Any, Dict, List, Optional
from datetime import datetime

import sys
PROJECT_ROOT = '/root/.openclaw/workspace/TradingAgents-OpenClaw'
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
from shared.models import (
    AnalystInput, AnalystOutput, AnalystReport,
    TradingSignal, AgentType, TokenUsage
)
from shared.json_utils import safe_json_parse

# 懒加载数据层提供器
_data_provider_getter = None

def _get_data_provider_getter():
    """懒加载获取数据层提供器"""
    global _data_provider_getter
    if _data_provider_getter is None:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "data_provider",
            os.path.join(os.path.dirname(__file__), "..", "skill_tao_data", "data_provider.py")
        )
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            _data_provider_getter = module.get_data_provider
    return _data_provider_getter


SENTIMENT_ANALYST_PROMPT = """You are a professional sentiment analyst specializing in market psychology and news impact assessment.

Your task is to analyze the provided news articles and generate a comprehensive sentiment analysis report.

## Analysis Framework

1. **News Sentiment Assessment**
   - Analyze each news article for sentiment (positive/negative/neutral)
   - Identify key themes and narratives
   - Assess the credibility and impact of each source

2. **Overall Sentiment Score**
   - Calculate weighted sentiment based on article importance
   - Consider recency (more recent = higher weight)
   - Factor in source credibility

3. **Key Events and Catalysts**
   - Identify major events driving sentiment
   - Flag potential catalysts (earnings, product launches, regulatory changes)
   - Note any contrarian indicators

4. **Trend Analysis**
   - Compare current sentiment to recent trends
   - Identify momentum shifts
   - Detect sentiment extremes (potential reversal signals)

5. **Risk Factors**
   - Highlight potential sentiment risks
   - Note upcoming events that could shift sentiment
   - Flag information asymmetries

## Output Format

Respond in the following JSON format:

```json
{
  "signal": "buy|sell|hold",
  "confidence": 0.72,
  "reasoning": "Detailed sentiment analysis summary...",
  "key_metrics": {
    "sentiment_score": 0.65,
    "positive_news_pct": 60,
    "negative_news_pct": 20,
    "neutral_news_pct": 20,
    "key_themes": ["theme1", "theme2"],
    "potential_catalysts": ["earnings on X date", "product launch"]
  },
  "risks": ["Risk 1", "Risk 2"]
}
```

Sentiment Score Guidelines:
- 0.7 to 1.0: Very Positive → BUY signal
- 0.3 to 0.7: Neutral → HOLD signal  
- -1.0 to 0.3: Negative → SELL signal

Be objective and base your analysis strictly on the provided news data."""


class SentimentAnalyst:
    """情绪分析师"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.data_provider = _get_data_provider_getter()()
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
        """执行情绪分析"""
        import time
        start_time = time.time()
        
        try:
            symbol = input_data.stock_symbol
            
            print(f"[{input_data.trace_id}] Fetching news data for {symbol}...")
            
            # 1. 获取新闻数据
            news_limit = self.config.get("news_limit", 20)
            news_data = self.data_provider.get_news(symbol, limit=news_limit)
            global_news = self.data_provider.get_global_news(limit=10)
            
            # 2. 构建分析提示词
            prompt = self._build_analysis_prompt(
                symbol=symbol,
                news_data=news_data,
                global_news=global_news
            )
            
            # 3. 调用 LLM 分析
            print(f"[{input_data.trace_id}] Analyzing sentiment with LLM...")
            
            response = self.llm_client.chat.completions.create(
                model=self.config.get("model", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": SENTIMENT_ANALYST_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config.get("temperature", 0.7),
                response_format={"type": "json_object"}
            )
            
            analysis_text = response.choices[0].message.content
            # 安全解析JSON
            analysis_json = safe_json_parse(
                analysis_text,
                default=None,
                validate_keys=["signal", "confidence", "reasoning"]
            )
            
            if analysis_json is None:
                print(f"[{input_data.trace_id}] Failed to parse sentiment analyst response")
                return AnalystOutput(
                    trace_id=input_data.trace_id,
                    success=False,
                    error="Failed to parse LLM response: JSON format error",
                    latency_ms=int((time.time() - start_time) * 1000)
                )
            
            # 安全处理signal枚举值
            try:
                signal = TradingSignal(analysis_json.get("signal", "hold"))
            except ValueError:
                signal = TradingSignal.HOLD
            
            # 4. 构建报告
            report = AnalystReport(
                agent_type=AgentType.SENTIMENT,
                stock_symbol=symbol,
                signal=signal,
                confidence=max(0.0, min(1.0, analysis_json.get("confidence", 0.5))),
                reasoning=analysis_json.get("reasoning", ""),
                key_metrics=analysis_json.get("key_metrics", {}),
                risks=analysis_json.get("risks", []),
                raw_output=analysis_text
            )
            
            # 5. 计算使用量
            token_usage = self._get_token_usage(response)
            latency_ms = int((time.time() - start_time) * 1000)
            
            print(f"[{input_data.trace_id}] Sentiment analysis completed in {latency_ms}ms")
            
            return AnalystOutput(
                trace_id=input_data.trace_id,
                success=True,
                report=report,
                latency_ms=latency_ms,
                token_usage=token_usage
            )
            
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            print(f"[{input_data.trace_id}] Sentiment analysis failed: {e}")
            
            return AnalystOutput(
                trace_id=input_data.trace_id,
                success=False,
                error=str(e),
                latency_ms=latency_ms
            )
    
    def _build_analysis_prompt(
        self,
        symbol: str,
        news_data: Dict,
        global_news: Dict
    ) -> str:
        """构建分析提示词"""
        
        news_list = news_data.get("news", [])
        
        # 格式化新闻
        news_text = []
        for i, news in enumerate(news_list[:15], 1):  # 取前15条
            news_text.append(
                f"{i}. {news.get('title', 'N/A')}\n"
                f"   Source: {news.get('publisher', 'N/A')}\n"
                f"   Summary: {news.get('summary', 'N/A')[:200]}..."
            )
        
        prompt = f"""Please analyze the following news articles for {symbol}:

## Company News ({len(news_list)} articles total)

{chr(10).join(news_text)}

## Analysis Instructions

1. Analyze the sentiment of each news article
2. Calculate overall sentiment metrics
3. Identify key themes and potential catalysts
4. Assess sentiment trend and momentum
5. Provide trading signal with confidence

Provide your analysis in the specified JSON format."""
        
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


def analyze_sentiment(
    symbol: str,
    trace_id: Optional[str] = None,
    config: Optional[Dict] = None
) -> AnalystOutput:
    """便捷函数：分析股票情绪"""
    from shared.models import AnalystInput
    
    analyst = SentimentAnalyst(config=config)
    
    input_data = AnalystInput(
        trace_id=trace_id or f"sent_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        stock_symbol=symbol,
        analysis_date=datetime.now().strftime("%Y-%m-%d"),
        config=config or {}
    )
    
    return analyst.analyze(input_data)


if __name__ == "__main__":
    print("Testing Sentiment Analyst...")
    
    result = analyze_sentiment(
        symbol="AAPL",
        config={
            "llm_provider": "openai",
            "model": "gpt-4o-mini",
            "temperature": 0.7
        }
    )
    
    if result.success:
        print(f"\nAnalysis Result for {result.report.stock_symbol}:")
        print(f"Signal: {result.report.signal.value}")
        print(f"Confidence: {result.report.confidence}")
    else:
        print(f"Analysis failed: {result.error}")
