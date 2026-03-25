"""
研究经理 Skill
整合多空辩论，输出综合研判
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
    ResearchSummary, TradingSignal
)
from shared.json_utils import safe_json_parse


RESEARCH_MANAGER_PROMPT = """You are a neutral research manager responsible for synthesizing conflicting viewpoints into a balanced investment recommendation.

## Your Role

- Objectively evaluate both bullish and bearish arguments
- Assess the strength of evidence on both sides
- Identify areas of consensus and disagreement
- Make a final recommendation based on the preponderance of evidence

## Analysis Framework

1. **Argument Assessment**
   - Evaluate the strength of bullish arguments
   - Evaluate the strength of bearish arguments
   - Identify which side has stronger evidence

2. **Consensus Identification**
   - Find points both sides agree on
   - Note areas of factual agreement
   - Identify shared concerns or opportunities

3. **Contradiction Analysis**
   - Catalog key disagreements
   - Assess which side's interpretation is more likely correct
   - Identify information gaps

4. **Confidence Assessment**
   - Rate overall conviction in the recommendation
   - Note key uncertainties
   - Identify catalysts that could change the view

## Output Format

Respond in the following JSON format:

```json
{
  "overall_signal": "buy|sell|hold",
  "confidence": 0.78,
  "consensus_level": 0.6,
  "key_insights": [
    "Key insight 1",
    "Key insight 2"
  ],
  "contradictions": [
    "Contradiction 1: Bull says X, Bear says Y",
    "Contradiction 2: Bull says X, Bear says Y"
  ],
  "reasoning": "Comprehensive synthesis explaining your recommendation...",
  "primary_bull_argument": "Strongest bullish point",
  "primary_bear_argument": "Strongest bearish point",
  "decisive_factors": ["Factor that tipped the decision"]
}
```

Signal Guidelines:
- BUY: Bullish arguments significantly stronger
- SELL: Bearish arguments significantly stronger
- HOLD: Arguments roughly balanced, or insufficient conviction

Be objective and balanced. Your goal is truth, not advocacy."""


class ResearchManager:
    """研究经理"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.llm_client = self._init_llm_client()
    
    def _init_llm_client(self):
        provider = self.config.get("llm_provider", "openai")
        if provider == "openai":
            from openai import OpenAI
            from shared import get_llm_client; return get_llm_client(provider)
        raise ValueError(f"Unsupported LLM provider: {provider}")
    
    def synthesize(self,
        symbol: str,
        debate_history: List[Dict],
        analyst_reports: Dict,
        trace_id: str = ""
    ) -> ResearchSummary:
        """整合辩论结果"""
        
        prompt = self._build_prompt(symbol, debate_history, analyst_reports)
        
        response = self.llm_client.chat.completions.create(
            model=self.config.get("model", "gpt-4o"),
            messages=[
                {"role": "system", "content": RESEARCH_MANAGER_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,  # 更低的温度，更客观
            response_format={"type": "json_object"}
        )
        
        # 安全解析JSON
        response_text = response.choices[0].message.content
        result = safe_json_parse(response_text, default=None)
        
        if result is None:
            print(f"[{trace_id}] Failed to parse research manager response")
            return ResearchSummary(
                overall_signal=TradingSignal.HOLD,
                consensus_level=0.5,
                key_insights=["Research synthesis failed"],
                contradictions=[],
                reasoning="Error: JSON parse failed"
            )
        
        # 安全处理signal枚举值
        try:
            signal = TradingSignal(result.get("overall_signal", "hold"))
        except ValueError:
            signal = TradingSignal.HOLD
        
        return ResearchSummary(
            overall_signal=signal,
            consensus_level=max(0.0, min(1.0, result.get("consensus_level", 0.5))),
            key_insights=result.get("key_insights", []),
            contradictions=result.get("contradictions", []),
            confidence=result.get("confidence", 0.5),
            reasoning=result.get("reasoning", "")
        )
    
    def _build_prompt(self, symbol: str, debate_history: List[Dict], analyst_reports: Dict) -> str:
        """构建提示词"""
        
        # 格式化辩论历史
        debate_text = []
        for round_data in debate_history:
            round_num = round_data.get("round", 1)
            bull = round_data.get("bull_view", {})
            bear = round_data.get("bear_view", {})
            
            debate_text.append(f"""
## Round {round_num}

### BULLISH VIEW
Confidence: {bull.get('confidence', 'N/A')}
Argument: {bull.get('argument', 'N/A')[:500]}...
Key Points: {bull.get('key_points', [])}
{"Response to Bear: " + bull.get('response_to_bear', '')[:300] if bull.get('response_to_bear') else ''}

### BEARISH VIEW
Confidence: {bear.get('confidence', 'N/A')}
Argument: {bear.get('argument', 'N/A')[:500]}...
Key Points: {bear.get('key_points', [])}
{"Response to Bull: " + bear.get('response_to_bull', '')[:300] if bear.get('response_to_bull') else ''}
""")
        
        prompt = f"""Synthesize the following research debate for {symbol}.

## DEBATE HISTORY

{chr(10).join(debate_text)}

## ORIGINAL ANALYST REPORTS

{self._format_analyst_reports(analyst_reports)}

## Instructions

1. Objectively assess both sides' arguments
2. Identify the strongest points from each side
3. Determine which side has the stronger case
4. Provide a clear recommendation with confidence level

Provide your synthesis in the specified JSON format."""
        
        return prompt
    
    def _format_analyst_reports(self, reports: Dict) -> str:
        """格式化分析师报告"""
        text = []
        for agent_type, report in reports.items():
            if report:
                text.append(
                    f"{agent_type.upper()}: {report.signal.value} "
                    f"(confidence: {report.confidence})"
                )
        return "\n".join(text)


if __name__ == "__main__":
    print("Testing Research Manager...")
    
    manager = ResearchManager()
    
    # 模拟辩论历史
    test_debate = [
        {
            "round": 1,
            "bull_view": {
                "confidence": 0.85,
                "argument": "Strong growth potential",
                "key_points": ["Revenue growing 50%", "Market leader"]
            },
            "bear_view": {
                "confidence": 0.70,
                "argument": "Valuation too high",
                "key_points": ["P/E over 50", "Competition increasing"]
            }
        }
    ]
    
    result = manager.synthesize(
        symbol="TEST",
        debate_history=test_debate,
        analyst_reports={},
        trace_id="test-001"
    )
    
    print(f"Signal: {result.overall_signal.value}")
    print(f"Confidence: {result.confidence}")
    print(f"Consensus: {result.consensus_level}")
