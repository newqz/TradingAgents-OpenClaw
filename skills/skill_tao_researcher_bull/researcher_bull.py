"""
看多研究员 Skill
从乐观角度分析投资机会
"""

import os
import json
from typing import Any, Dict, List, Optional
from datetime import datetime

import sys
PROJECT_ROOT = '/root/.openclaw/workspace/TradingAgents-OpenClaw'
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
from shared.models import (
    AnalystReport, AgentType, TradingSignal
)
from shared.json_utils import safe_json_parse


BULL_RESEARCHER_PROMPT = """You are a bullish researcher with expertise in growth investing and opportunity identification.

Your role is to analyze the provided research data from a BULLISH perspective and construct a compelling investment case.

## Your Mindset

- Focus on growth opportunities and undervalued potential
- Emphasize positive trends and catalysts
- Acknowledge risks but explain why they are manageable or temporary
- Use data to support optimistic scenarios

## Analysis Framework

1. **Growth Catalysts**
   - Identify key drivers for future growth
   - Highlight competitive advantages
   - Note positive industry trends

2. **Valuation Opportunity**
   - Explain why current price offers value
   - Compare to peers and historical valuations
   - Project upside potential

3. **Risk Mitigation**
   - Address identified risks
   - Explain why risks are overstated or temporary
   - Highlight management quality and track record

4. **Contrarian Opportunities**
   - Identify market overreactions or misunderstandings
   - Point to overlooked strengths
   - Highlight inflection points

## If Opposing View Provided

You MUST directly respond to the bearish arguments:
- Address each concern with data
- Explain why the pessimistic view is incomplete or incorrect
- Turn bearish concerns into bullish opportunities where possible

## Output Format

Respond in the following JSON format:

```json
{
  "view": "bullish",
  "confidence": 0.85,
  "argument": "Your comprehensive bullish argument...",
  "key_points": [
    "Key point 1 with specific data",
    "Key point 2 with specific data",
    "Key point 3 with specific data"
  ],
  "response_to_bear": "Direct response to bearish arguments...",
  "upside_target": "Price target or % upside",
  "time_horizon": "short_term|medium_term|long_term"
}
```

Be enthusiastic but grounded in data. Your goal is to present the strongest possible bullish case."""


class BullResearcher:
    """看多研究员"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.llm_client = self._init_llm_client()
    
    def _init_llm_client(self):
        provider = self.config.get("llm_provider", "openai")
        if provider == "openai":
            from openai import OpenAI
            from shared import get_llm_client; return get_llm_client(provider)
        raise ValueError(f"Unsupported LLM provider: {provider}")
    
    def research(self, 
        symbol: str,
        analyst_reports: Dict[str, AnalystReport],
        opponent_argument: Optional[str] = None,
        round_num: int = 1,
        trace_id: str = ""
    ) -> Dict[str, Any]:
        """执行看多研究"""
        
        prompt = self._build_prompt(symbol, analyst_reports, opponent_argument, round_num)
        
        response = self.llm_client.chat.completions.create(
            model=self.config.get("model", "gpt-4o"),
            messages=[
                {"role": "system", "content": BULL_RESEARCHER_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        # 安全解析JSON
        response_text = response.choices[0].message.content
        result = safe_json_parse(response_text, default=None)
        
        if result is None:
            print(f"[{trace_id}] Failed to parse bull researcher response")
            return {
                "trace_id": trace_id,
                "round": round_num,
                "bull_points": [],
                "bear_points": [],
                "overall_sentiment": "neutral",
                "error": "JSON parse error"
            }
        
        result["trace_id"] = trace_id
        result["round"] = round_num
        
        return result
    
    def _build_prompt(self, symbol: str, reports: Dict, opponent: Optional[str], round_num: int) -> str:
        """构建提示词"""
        
        # 整理分析师报告
        reports_text = []
        for agent_type, report in reports.items():
            if report:
                reports_text.append(
                    f"## {agent_type.upper()} Analysis\n"
                    f"Signal: {report.signal.value}\n"
                    f"Confidence: {report.confidence}\n"
                    f"Reasoning: {report.reasoning[:300]}...\n"
                    f"Key Metrics: {report.key_metrics}\n"
                )
        
        opponent_section = ""
        if opponent and round_num > 1:
            opponent_section = f"""
## BEARISH ARGUMENT TO RESPOND TO

{opponent}

You MUST directly address these bearish points in your response.
"""
        
        prompt = f"""Construct a BULLISH investment case for {symbol}.

{chr(10).join(reports_text)}

{opponent_section}

## Instructions

Round: {round_num}
Construct the strongest possible bullish argument based on the research data.
{"Address and refute the bearish concerns directly." if opponent else "Anticipate potential bearish concerns and address them proactively."}

Provide your analysis in the specified JSON format."""
        
        return prompt


if __name__ == "__main__":
    print("Testing Bull Researcher...")
    
    researcher = BullResearcher()
    
    # 模拟测试
    test_reports = {
        "fundamental": AnalystReport(
            agent_type=AgentType.FUNDAMENTAL,
            stock_symbol="TEST",
            signal=TradingSignal.BUY,
            confidence=0.8,
            reasoning="Strong growth",
            key_metrics={"pe": 20}
        )
    }
    
    result = researcher.research(
        symbol="TEST",
        analyst_reports=test_reports,
        trace_id="test-001"
    )
    
    print(f"Bull View: {result['view']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Key Points: {result.get('key_points', [])}")
