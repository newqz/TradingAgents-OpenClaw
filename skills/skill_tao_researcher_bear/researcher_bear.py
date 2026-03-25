"""
看空研究员 Skill
从悲观角度分析投资风险
"""

import os
import json
from typing import Any, Dict, List, Optional
from datetime import datetime

import sys
sys.path.insert(0, '/root/.openclaw/workspace/TradingAgents-OpenClaw')
from shared.models import (
    AnalystReport, AgentType, TradingSignal
)


BEAR_RESEARCHER_PROMPT = """You are a bearish researcher with expertise in risk assessment and value preservation.

Your role is to analyze the provided research data from a BEARISH perspective and identify potential risks and overvaluation.

## Your Mindset

- Focus on risks, red flags, and potential downsides
- Emphasize valuation concerns and growth headwinds
- Acknowledge positives but explain why they are insufficient or temporary
- Use data to support pessimistic scenarios

## Analysis Framework

1. **Valuation Concerns**
   - Identify overvaluation metrics
   - Compare to historical norms and peers
   - Highlight stretched multiples

2. **Risk Factors**
   - Catalog all identified risks
   - Assess probability and impact
   - Note any emerging threats

3. **Growth Headwinds**
   - Identify slowing growth indicators
   - Note competitive pressures
   - Highlight market saturation risks

4. **Catalysts for Decline**
   - Identify potential negative triggers
   - Note technical breakdown levels
   - Highlight deteriorating sentiment

## If Opposing View Provided

You MUST directly respond to the bullish arguments:
- Address each optimistic point with counter-evidence
- Explain why the bullish view is overlooking critical risks
- Demonstrate why the downside scenario is more likely

## Output Format

Respond in the following JSON format:

```json
{
  "view": "bearish",
  "confidence": 0.75,
  "argument": "Your comprehensive bearish argument...",
  "key_points": [
    "Key risk 1 with specific data",
    "Key risk 2 with specific data",
    "Key risk 3 with specific data"
  ],
  "response_to_bull": "Direct response to bullish arguments...",
  "downside_target": "Price target or % downside",
  "time_horizon": "short_term|medium_term|long_term"
}
```

Be skeptical but grounded in data. Your goal is to protect capital by identifying risks."""


class BearResearcher:
    """看空研究员"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.llm_client = self._init_llm_client()
    
    def _init_llm_client(self):
        provider = self.config.get("llm_provider", "openai")
        if provider == "openai":
            from openai import OpenAI
            return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        raise ValueError(f"Unsupported LLM provider: {provider}")
    
    def research(self,
        symbol: str,
        analyst_reports: Dict[str, AnalystReport],
        opponent_argument: Optional[str] = None,
        round_num: int = 1,
        trace_id: str = ""
    ) -> Dict[str, Any]:
        """执行看空研究"""
        
        prompt = self._build_prompt(symbol, analyst_reports, opponent_argument, round_num)
        
        response = self.llm_client.chat.completions.create(
            model=self.config.get("model", "gpt-4o"),
            messages=[
                {"role": "system", "content": BEAR_RESEARCHER_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        result["trace_id"] = trace_id
        result["round"] = round_num
        
        return result
    
    def _build_prompt(self, symbol: str, reports: Dict, opponent: Optional[str], round_num: int) -> str:
        """构建提示词"""
        
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
## BULLISH ARGUMENT TO RESPOND TO

{opponent}

You MUST directly address these bullish points in your response.
"""
        
        prompt = f"""Construct a BEARISH risk assessment for {symbol}.

{chr(10).join(reports_text)}

{opponent_section}

## Instructions

Round: {round_num}
Construct the strongest possible bearish argument based on the research data.
{"Address and refute the bullish claims directly." if opponent else "Anticipate potential bullish claims and address them proactively."}

Provide your analysis in the specified JSON format."""
        
        return prompt


if __name__ == "__main__":
    print("Testing Bear Researcher...")
    
    researcher = BearResearcher()
    
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
    
    print(f"Bear View: {result['view']}")
    print(f"Confidence: {result['confidence']}")
