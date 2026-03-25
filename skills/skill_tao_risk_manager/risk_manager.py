"""
风险管理 Skill
评估交易风险，给出风控建议
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
    RiskAssessment, RiskLevel, RiskFactor,
    ResearchSummary, TraderRecommendation
)
from shared.json_utils import safe_json_parse


RISK_MANAGER_PROMPT = """You are a professional risk manager responsible for assessing portfolio and position risks.

## Your Role

Evaluate the proposed trade across multiple risk dimensions and provide risk-adjusted recommendations.

## Risk Assessment Framework

1. **Market Risk**
   - Overall market volatility and trend
   - Correlation with broader market
   - Systemic risk factors

2. **Position Risk**
   - Concentration risk (position size relative to portfolio)
   - Volatility of the specific stock
   - Liquidity considerations

3. **Fundamental Risk**
   - Business model sustainability
   - Competitive threats
   - Regulatory risks

4. **Technical Risk**
   - Support/resistance levels
   - Trend strength
   - Volume patterns

5. **Sentiment Risk**
   - Crowded trade indicators
   - Extreme sentiment readings
   - News flow risks

## Risk Scoring (0-100)

- 0-30: LOW RISK - Standard position sizing appropriate
- 31-60: MEDIUM RISK - Reduced position sizing recommended
- 61-80: HIGH RISK - Small position or avoid
- 81-100: EXTREME RISK - Avoid or use hedging strategies

## Output Format

Respond in JSON format:
{
  "overall_risk": "low|medium|high|extreme",
  "risk_score": 65,
  "position_limit_pct": 10,
  "max_position_pct": 15,
  "risk_factors": [
    {
      "factor_name": "Market Volatility",
      "level": "high",
      "description": "VIX elevated above 30",
      "mitigation": "Reduce position size by 50%"
    }
  ],
  "warnings": ["Warning 1", "Warning 2"],
  "recommendations": ["Recommendation 1"],
  "approval": "approved|conditional|rejected"
}

Approval Guidelines:
- approved: Risk acceptable, proceed with recommendation
- conditional: Proceed with modifications (reduced size, tighter stops)
- rejected: Risk too high, do not proceed
"""


class RiskManager:
    """风险管理器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.llm_client = self._init_llm_client()
    
    def _init_llm_client(self):
        provider = self.config.get("llm_provider", "openai")
        if provider == "openai":
            from openai import OpenAI
            from shared import get_llm_client; return get_llm_client(provider)
        raise ValueError(f"Unsupported LLM provider: {provider}")
    
    def assess(self,
        symbol: str,
        research: ResearchSummary,
        trader_recommendations: List[TraderRecommendation],
        trace_id: str = ""
    ) -> RiskAssessment:
        """执行风险评估"""
        
        prompt = self._build_prompt(symbol, research, trader_recommendations)
        
        response = self.llm_client.chat.completions.create(
            model=self.config.get("model", "gpt-4o"),
            messages=[
                {"role": "system", "content": RISK_MANAGER_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            response_format={"type": "json_object"}
        )
        
        # 安全解析JSON
        response_text = response.choices[0].message.content
        result = safe_json_parse(response_text, default=None)
        
        if result is None:
            print(f"[{trace_id}] Failed to parse risk manager response")
            return RiskAssessment(
                overall_risk=RiskLevel.MEDIUM,
                risk_score=50,
                risk_factors=[],
                max_position_pct=0.20,
                recommendations=["Risk assessment failed"]
            )
        
        # 构建 RiskFactor 列表 (安全处理枚举值)
        risk_factors = []
        for rf in result.get("risk_factors", []):
            try:
                level = RiskLevel(rf.get("level", "medium"))
            except ValueError:
                level = RiskLevel.MEDIUM
            risk_factors.append(RiskFactor(
                factor_name=rf.get("factor_name", ""),
                level=level,
                description=rf.get("description", ""),
                mitigation=rf.get("mitigation", "")
            ))
        
        # 安全处理overall_risk枚举值
        try:
            overall_risk = RiskLevel(result.get("overall_risk", "medium"))
        except ValueError:
            overall_risk = RiskLevel.MEDIUM
        
        return RiskAssessment(
            overall_risk=overall_risk,
            risk_score=max(0, min(100, result.get("risk_score", 50))),
            risk_factors=risk_factors,
            position_size_recommendation=result.get("recommendations", ["medium"])[0],
            max_position_pct=result.get("max_position_pct", 10),
            warnings=result.get("warnings", [])
        )
    
    def _build_prompt(self, symbol: str, research: ResearchSummary, recommendations: List[TraderRecommendation]) -> str:
        """构建提示词"""
        
        # 整理交易员建议
        trader_text = []
        for rec in recommendations:
            trader_text.append(
                f"- {rec.trader_type.value}: {rec.action.value.upper()} "
                f"(confidence: {rec.confidence}, position: {rec.position_size})\n"
                f"  Reasoning: {rec.reasoning[:200]}..."
            )
        
        prompt = f"""Assess risk for trading {symbol}.

## Research Synthesis

Signal: {research.overall_signal.value}
Confidence: {research.confidence}
Consensus: {research.consensus_level}

Key Insights:
{chr(10).join(f"- {i}" for i in research.key_insights)}

Contradictions:
{chr(10).join(f"- {c}" for c in research.contradictions)}

## Trader Recommendations

{chr(10).join(trader_text)}

## Instructions

1. Evaluate risks across all dimensions
2. Calculate overall risk score (0-100)
3. Determine maximum appropriate position size
4. Identify key risk factors and mitigations
5. Provide approval recommendation

Provide your risk assessment in the specified JSON format."""
        
        return prompt


if __name__ == "__main__":
    print("Testing Risk Manager...")
    
    from shared.models import TradingSignal, AgentType, TradingAction
    
    research = ResearchSummary(
        overall_signal=TradingSignal.BUY,
        confidence=0.8,
        consensus_level=0.7,
        key_insights=["Strong growth"],
        contradictions=["High valuation"],
        reasoning="Growth justifies premium"
    )
    
    recommendations = [
        TraderRecommendation(
            trader_type=AgentType.BULL_TRADER,
            action=TradingAction.BUY,
            confidence=0.85,
            position_size="large",
            reasoning="Aggressive growth play"
        )
    ]
    
    manager = RiskManager()
    assessment = manager.assess("TEST", research, recommendations)
    
    print(f"Risk Level: {assessment.overall_risk.value}")
    print(f"Risk Score: {assessment.risk_score}")
    print(f"Max Position: {assessment.max_position_pct}%")
