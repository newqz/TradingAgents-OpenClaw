"""
基本面分析师 Skill
分析公司财务数据，生成基本面投资报告

入口点应先调用:
  from bootstrap import setup; setup()
"""

import os
import json
import importlib
from typing import Any, Dict, List, Optional
from datetime import datetime

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


# 基本面分析系统提示词
FUNDAMENTAL_ANALYST_PROMPT = """You are a professional fundamental analyst with 20 years of experience in equity research.

Your task is to analyze the provided company's financial data and generate a comprehensive fundamental analysis report.

## Analysis Framework

1. **Business Overview**
   - Industry and competitive position
   - Business model and revenue drivers
   - Key growth catalysts and risks

2. **Financial Health**
   - Revenue and earnings trends
   - Profitability metrics (gross margin, operating margin, net margin)
   - Return metrics (ROE, ROA, ROIC)
   - Cash flow generation ability

3. **Valuation Analysis**
   - Current valuation multiples (P/E, P/B, PEG, EV/EBITDA)
   - Comparison to industry peers and historical averages
   - Assessment of over/under valuation

4. **Balance Sheet Strength**
   - Debt levels and debt servicing capability
   - Liquidity position
   - Asset quality

5. **Investment Signal**
   Based on your analysis, provide:
   - Signal: BUY / SELL / HOLD
   - Confidence: 0.0 to 1.0
   - Key supporting reasons (3-5 bullet points)
   - Major risks (2-3 bullet points)

## Output Format

Respond in the following JSON format:

```json
{
  "signal": "buy|sell|hold",
  "confidence": 0.85,
  "reasoning": "Detailed analysis summary...",
  "key_metrics": {
    "pe_ratio": 25.5,
    "pb_ratio": 8.2,
    "revenue_growth": 0.15,
    "profit_margin": 0.25,
    "roe": 0.28,
    "debt_to_equity": 0.5
  },
  "risks": ["Risk 1", "Risk 2"]
}
```

Be objective, thorough, and base your analysis strictly on the provided financial data."""


class FundamentalAnalyst:
    """基本面分析师"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.data_provider = _get_data_provider_getter()()
        self.llm_client = self._init_llm_client()
    
    def _init_llm_client(self):
        """初始化 LLM 客户端"""
        provider = self.config.get("llm_provider", "openai")
        
        try:
            from shared import get_llm_client
            return get_llm_client(provider)
        except ImportError:
            raise ImportError("shared package required. Ensure TradingAgents-OpenClaw is properly installed.")
    
    def _call_llm(self, prompt: str, system_message: str) -> str:
        """调用 LLM"""
        model = self.config.get("model", "gpt-4o-mini")
        temperature = self.config.get("temperature", 0.7)
        
        response = self.llm_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            response_format={"type": "json_object"}
        )
        
        return response.choices[0].message.content
    
    def _get_token_usage(self, response) -> TokenUsage:
        """获取 token 使用情况"""
        usage = response.usage if hasattr(response, 'usage') else None
        
        if usage:
            # 估算成本 (gpt-4o-mini)
            prompt_cost = usage.prompt_tokens * 0.000000165  # $0.165 / 1M tokens
            completion_cost = usage.completion_tokens * 0.00000066  # $0.66 / 1M tokens
            
            return TokenUsage(
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                total_tokens=usage.total_tokens,
                cost_usd=round(prompt_cost + completion_cost, 6)
            )
        
        return TokenUsage()
    
    def analyze(self, input_data: AnalystInput) -> AnalystOutput:
        """
        执行基本面分析
        
        Args:
            input_data: 分析输入
            
        Returns:
            AnalystOutput: 分析结果
        """
        import time
        start_time = time.time()
        
        try:
            # 1. 获取数据
            symbol = input_data.stock_symbol
            
            print(f"[{input_data.trace_id}] Fetching fundamental data for {symbol}...")
            
            fundamentals = self.data_provider.get_fundamentals(symbol)
            balance_sheet = self.data_provider.get_balance_sheet(symbol)
            income_stmt = self.data_provider.get_income_statement(symbol)
            cashflow = self.data_provider.get_cashflow(symbol)
            
            # 2. 构建分析提示词
            prompt = self._build_analysis_prompt(
                symbol=symbol,
                fundamentals=fundamentals,
                balance_sheet=balance_sheet,
                income_stmt=income_stmt,
                cashflow=cashflow
            )
            
            # 3. 调用 LLM 分析
            print(f"[{input_data.trace_id}] Analyzing with LLM...")
            
            response = self.llm_client.chat.completions.create(
                model=self.config.get("model", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": FUNDAMENTAL_ANALYST_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config.get("temperature", 0.7),
                response_format={"type": "json_object"}
            )
            
            analysis_text = response.choices[0].message.content
            # 安全解析JSON，支持验证必填字段
            analysis_json = safe_json_parse(
                analysis_text,
                default=None,
                validate_keys=["signal", "confidence", "reasoning"]
            )
            
            # 如果解析失败，返回错误
            if analysis_json is None:
                print(f"[{input_data.trace_id}] Failed to parse LLM response as JSON: {analysis_text[:200]}...")
                return AnalystOutput(
                    trace_id=input_data.trace_id,
                    success=False,
                    error=f"Failed to parse LLM response: JSON format error",
                    latency_ms=int((time.time() - start_time) * 1000)
                )
            
            # 4. 构建报告 (安全处理signal枚举值)
            try:
                signal_value = analysis_json.get("signal", "hold")
                signal = TradingSignal(signal_value)
            except ValueError:
                print(f"[{input_data.trace_id}] Invalid signal '{signal_value}', defaulting to HOLD")
                signal = TradingSignal.HOLD
            
            report = AnalystReport(
                agent_type=AgentType.FUNDAMENTAL,
                stock_symbol=symbol,
                signal=signal,
                confidence=max(0.0, min(1.0, analysis_json.get("confidence", 0.5))),  # clamp 0-1
                reasoning=analysis_json.get("reasoning", ""),
                key_metrics=analysis_json.get("key_metrics", {}),
                risks=analysis_json.get("risks", []),
                raw_output=analysis_text
            )
            
            # 5. 计算 token 使用量
            token_usage = self._get_token_usage(response)
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            print(f"[{input_data.trace_id}] Fundamental analysis completed in {latency_ms}ms")
            
            return AnalystOutput(
                trace_id=input_data.trace_id,
                success=True,
                report=report,
                latency_ms=latency_ms,
                token_usage=token_usage
            )
            
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            
            print(f"[{input_data.trace_id}] Fundamental analysis failed: {e}")
            
            return AnalystOutput(
                trace_id=input_data.trace_id,
                success=False,
                error=str(e),
                latency_ms=latency_ms
            )
    
    def _build_analysis_prompt(
        self,
        symbol: str,
        fundamentals: Dict,
        balance_sheet: Dict,
        income_stmt: Dict,
        cashflow: Dict
    ) -> str:
        """构建分析提示词"""
        
        company_info = fundamentals.get("company_info", {})
        financial_highlights = fundamentals.get("financial_highlights", {})
        valuation = fundamentals.get("valuation", {})
        
        prompt = f"""Please analyze the following fundamental data for {symbol}:

## Company Overview
- Name: {company_info.get('name', 'N/A')}
- Sector: {company_info.get('sector', 'N/A')}
- Industry: {company_info.get('industry', 'N/A')}
- Country: {company_info.get('country', 'N/A')}

## Valuation Metrics
- P/E Ratio: {valuation.get('pe_ratio', 'N/A')}
- Forward P/E: {valuation.get('forward_pe', 'N/A')}
- P/B Ratio: {valuation.get('pb_ratio', 'N/A')}
- PEG Ratio: {valuation.get('peg_ratio', 'N/A')}
- EV/EBITDA: {valuation.get('ev_ebitda', 'N/A')}
- Price-to-Sales: {valuation.get('ps_ratio', 'N/A')}

## Financial Highlights
- Market Cap: ${financial_highlights.get('market_cap', 'N/A')}
- Revenue: ${financial_highlights.get('revenue', 'N/A')}
- Revenue Growth: {financial_highlights.get('revenue_growth', 'N/A')}
- Gross Profit: ${financial_highlights.get('gross_profit', 'N/A')}
- EBITDA: ${financial_highlights.get('ebitda', 'N/A')}
- Net Income: ${financial_highlights.get('net_income', 'N/A')}
- Profit Margin: {financial_highlights.get('profit_margin', 'N/A')}
- Operating Margin: {financial_highlights.get('operating_margin', 'N/A')}

## Raw Financial Data
```json
{json.dumps(fundamentals.get('raw_info', {}), indent=2)[:2000]}
```

Please provide a comprehensive fundamental analysis with investment signal (buy/sell/hold), confidence level (0.0-1.0), detailed reasoning, key metrics, and risk factors.
"""
        
        return prompt


# 便捷函数
def analyze_fundamentals(
    symbol: str,
    trace_id: Optional[str] = None,
    config: Optional[Dict] = None
) -> AnalystOutput:
    """
    便捷函数：分析股票基本面
    
    使用示例:
        result = analyze_fundamentals("AAPL")
        print(result.report.signal)  # buy/sell/hold
        print(result.report.confidence)  # 0.0-1.0
    """
    from shared.models import AnalystInput
    
    analyst = FundamentalAnalyst(config=config)
    
    input_data = AnalystInput(
        trace_id=trace_id or f"fund_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        stock_symbol=symbol,
        analysis_date=datetime.now().strftime("%Y-%m-%d"),
        config=config or {}
    )
    
    return analyst.analyze(input_data)


if __name__ == "__main__":
    # 测试
    import asyncio
    
    print("Testing Fundamental Analyst...")
    
    result = analyze_fundamentals(
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
        print(f"Reasoning: {result.report.reasoning[:200]}...")
        print(f"Latency: {result.latency_ms}ms")
        print(f"Cost: ${result.token_usage.cost_usd}")
    else:
        print(f"Analysis failed: {result.error}")
