"""
TraderDebateOrchestrator - 交易员辩论编排器
调度三位交易员进行辩论，并进行风险评估
"""

import os
import json
from typing import Any, Dict, List, Optional
from datetime import datetime

import sys

# 使用共享配置模块设置路径
from shared import config
config.setup_paths()

from shared.models import (
    AgentType,
    ResearchSummary,
    RiskAssessment,
    RiskLevel,
    TraderRecommendation,
    TradingAction,
)


TRADER_PROMPTS = {
    AgentType.BULL_TRADER: """You are an AGGRESSIVE BULL Trader focused on maximizing returns.

Your profile:
- High risk tolerance
- Believe in growth and momentum
- Prefer large positions when confident
- Target ambitious entry/exit levels
- Focus on catalysts and upside potential

When analyzing:
1. Emphasize growth prospects and market opportunities
2. Minimize or rationalize risks
3. Recommend larger position sizes
4. Set wider stop losses
5. Focus on momentum and trend

Output JSON format:
{
  "action": "buy|strong_buy",
  "target_price": 180.00,
  "stop_loss": 140.00,
  "position_size": "large",
  "confidence": 0.85,
  "reasoning": "...",
  "key_catalysts": ["catalyst1", "catalyst2"],
  "risk_factors": ["risk1"]
}""",

    AgentType.NEUTRAL_TRADER: """You are a BALANCED NEUTRAL Trader focused on risk-adjusted returns.

Your profile:
- Moderate risk tolerance
- Seek clear entry signals
- Prefer medium positions
- Use tighter stop losses
- Consider both sides before deciding

When analyzing:
1. Weigh bull and bear arguments equally
2. Wait for clear signals before committing
3. Recommend moderate position sizes
4. Use disciplined stop losses
5. Focus on uncertainty and wait for clarity

Output JSON format:
{
  "action": "hold|buy|sell",
  "target_price": 160.00,
  "stop_loss": 145.00,
  "position_size": "medium",
  "confidence": 0.65,
  "reasoning": "...",
  "key_catalysts": [],
  "risk_factors": []
}""",

    AgentType.BEAR_TRADER: """You are a CONSERVATIVE BEAR Trader focused on capital preservation.

Your profile:
- Low risk tolerance
- Focus on downside protection
- Prefer smaller positions or cash
- Use tight stop losses
- Skeptical of hype and momentum

When analyzing:
1. Emphasize risks and overvaluation
2. Question bull thesis critically
3. Recommend smaller positions
4. Use very tight stop losses
5. Focus on value and risk/reward

Output JSON format:
{
  "action": "sell|hold|avoid",
  "target_price": 140.00,
  "stop_loss": 155.00,
  "position_size": "small",
  "confidence": 0.75,
  "reasoning": "...",
  "key_catalysts": [],
  "risk_factors": ["risk1", "risk2"]
}"""
}


RISK_MANAGER_PROMPT = """You are a RISK MANAGER responsible for assessing portfolio and position risks.

Your role: Evaluate the proposed trade across multiple risk dimensions and provide risk-adjusted recommendations.

Risk Scoring (0-100):
- 0-30: LOW - Standard position sizing
- 31-60: MEDIUM - Reduced position recommended
- 61-80: HIGH - Small position or avoid
- 81-100: EXTREME - Avoid or hedge

Output JSON format:
{
  "overall_risk": "low|medium|high|extreme",
  "risk_score": 55,
  "risk_factors": [
    {"factor_name": "Market Volatility", "level": "medium", "description": "...", "mitigation": "..."}
  ],
  "warnings": ["Warning 1"],
  "max_position_pct": 10,
  "approval": "approved|conditional|rejected"
}"""


class TraderDebateOrchestrator:
    """交易员辩论编排器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._llm_client = None  # 延迟初始化
    
    @property
    def llm_client(self):
        if self._llm_client is None:
            self._llm_client = self._init_llm_client()
        return self._llm_client
    
    def _init_llm_client(self):
        provider = self.config.get("llm_provider", "openai")
        if provider == "openai":
            try:
                from openai import OpenAI
                from shared import get_llm_client; return get_llm_client(provider)
            except ImportError:
                return None
        return None
    
    def run_trader_debate(
        self,
        symbol: str,
        research: ResearchSummary,
        trace_id: str = ""
    ) -> List[TraderRecommendation]:
        """
        运行交易员辩论，获取三位交易员的建议
        
        Args:
            symbol: 股票代码
            research: 研究综合报告
            trace_id: 追踪ID
            
        Returns:
            List[TraderRecommendation]: 三位交易员的建议
        """
        # 构建研究背景
        research_context = self._build_research_context(symbol, research)
        
        # 并行获取三位交易员的建议
        traders = [
            (AgentType.BULL_TRADER, "aggressive bull"),
            (AgentType.NEUTRAL_TRADER, "balanced neutral"),
            (AgentType.BEAR_TRADER, "conservative bear")
        ]
        
        recommendations = []
        
        for agent_type, style_desc in traders:
            try:
                rec = self._get_trader_recommendation(
                    symbol=symbol,
                    research_context=research_context,
                    agent_type=agent_type,
                    style_desc=style_desc,
                    trace_id=trace_id
                )
                recommendations.append(rec)
                print(f"[{trace_id}] {agent_type.value}: {rec.action.value.upper()} (confidence: {rec.confidence:.2f})")
            except Exception as e:
                print(f"[{trace_id}] {agent_type.value} failed: {e}")
                # 失败时返回默认建议
                recommendations.append(TraderRecommendation(
                    trader_type=agent_type,
                    action=TradingAction.HOLD,
                    confidence=0.3,
                    reasoning=f"Failed to generate recommendation: {e}"
                ))
        
        return recommendations
    
    def assess_risk(
        self,
        symbol: str,
        research: ResearchSummary,
        trader_recommendations: List[TraderRecommendation],
        trace_id: str = ""
    ) -> RiskAssessment:
        """
        进行风险评估
        
        Args:
            symbol: 股票代码
            research: 研究综合报告
            trader_recommendations: 交易员建议
            trace_id: 追踪ID
            
        Returns:
            RiskAssessment: 风险评估报告
        """
        prompt = self._build_risk_prompt(symbol, research, trader_recommendations)
        
        response = self.llm_client.chat.completions.create(
            model=self.config.get("model", "gpt-4o"),
            messages=[
                {"role": "system", "content": RISK_MANAGER_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        from shared.models import RiskFactor
        
        risk_factors = []
        for rf in result.get("risk_factors", []):
            risk_factors.append(RiskFactor(
                factor_name=rf.get("factor_name", ""),
                level=RiskLevel(rf.get("level", "medium")),
                description=rf.get("description", ""),
                mitigation=rf.get("mitigation", "")
            ))
        
        return RiskAssessment(
            overall_risk=RiskLevel(result.get("overall_risk", "medium")),
            risk_score=result.get("risk_score", 50.0),
            risk_factors=risk_factors,
            position_size_recommendation=result.get("position_size_recommendation", "medium"),
            max_position_pct=result.get("max_position_pct", 10.0),
            warnings=result.get("warnings", [])
        )
    
    def _get_trader_recommendation(
        self,
        symbol: str,
        research_context: str,
        agent_type: AgentType,
        style_desc: str,
        trace_id: str
    ) -> TraderRecommendation:
        """获取单个交易员的建议"""
        
        prompt = f"""Analyze {symbol} and provide your trading recommendation as a {style_desc} trader.

## Research Context

{research_context}

## Your Task

1. Review the research synthesis carefully
2. Apply your trading style ({style_desc})
3. Provide a specific entry/exit strategy
4. Include position sizing recommendation

Output your recommendation in the specified JSON format."""

        response = self.llm_client.chat.completions.create(
            model=self.config.get("model", "gpt-4o"),
            messages=[
                {"role": "system", "content": TRADER_PROMPTS.get(agent_type, TRADER_PROMPTS[AgentType.NEUTRAL_TRADER])},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        return TraderRecommendation(
            trader_type=agent_type,
            action=TradingAction(result.get("action", "hold")),
            target_price=result.get("target_price"),
            stop_loss=result.get("stop_loss"),
            position_size=result.get("position_size", "medium"),
            confidence=result.get("confidence", 0.5),
            reasoning=result.get("reasoning", "")
        )
    
    def _build_research_context(self, symbol: str, research: ResearchSummary) -> str:
        """构建研究背景"""
        
        insights = "\n".join(f"- {i}" for i in research.key_insights) if research.key_insights else "No key insights available"
        contradictions = "\n".join(f"- {c}" for c in research.contradictions) if research.contradictions else "No contradictions noted"
        
        return f"""
## Stock: {symbol}

### Research Signal
- Overall Signal: {research.overall_signal.value.upper()}
- Confidence: {research.confidence:.2f}
- Consensus Level: {research.consensus_level:.2f}

### Key Insights (Bullish Factors):
{insights}

### Contradictions (Bearish Factors):
{contradictions}

### Research Reasoning:
{research.reasoning}
"""
    
    def _build_risk_prompt(
        self,
        symbol: str,
        research: ResearchSummary,
        trader_recommendations: List[TraderRecommendation]
    ) -> str:
        """构建风险评估提示词"""
        
        trader_text = []
        for rec in trader_recommendations:
            trader_text.append(
                f"- {rec.trader_type.value.upper()}: {rec.action.value.upper()} "
                f"(confidence: {rec.confidence:.2f}, position: {rec.position_size})\n"
                f"  Reasoning: {rec.reasoning[:200]}..."
            )
        
        return f"""Assess risk for trading {symbol}.

## Research Summary
Signal: {research.overall_signal.value}
Confidence: {research.confidence:.2f}

Key Insights: {', '.join(research.key_insights[:3]) if research.key_insights else 'None'}
Contradictions: {', '.join(research.contradictions[:3]) if research.contradictions else 'None'}

## Trader Recommendations
{chr(10).join(trader_text)}

## Instructions

1. Evaluate risks across market, position, fundamental, technical, and sentiment dimensions
2. Score overall risk (0-100)
3. Identify key risk factors and mitigations
4. Determine maximum appropriate position size
5. Provide approval recommendation

Output in specified JSON format."""


if __name__ == "__main__":
    print("Testing Trader Debate Orchestrator...")
    
    from shared.models import TradingSignal
    
    research = ResearchSummary(
        overall_signal=TradingSignal.BUY,
        confidence=0.8,
        consensus_level=0.75,
        key_insights=["Strong growth", "AI leadership"],
        contradictions=["High valuation"],
        reasoning="Growth prospects justify premium"
    )
    
    orchestrator = TraderDebateOrchestrator()
    
    # 测试交易员辩论
    print("\n📊 Running trader debate...")
    recommendations = orchestrator.run_trader_debate("NVDA", research, "test-001")
    
    print("\n📊 Trader Recommendations:")
    for rec in recommendations:
        print(f"  {rec.trader_type.value}: {rec.action.value.upper()} (confidence: {rec.confidence:.2f})")
    
    # 测试风险评估
    print("\n📊 Running risk assessment...")
    risk = orchestrator.assess_risk("NVDA", research, recommendations, "test-001")
    
    print(f"\n📊 Risk Assessment:")
    print(f"  Overall Risk: {risk.overall_risk.value}")
    print(f"  Risk Score: {risk.risk_score:.0f}/100")
    print(f"  Max Position: {risk.max_position_pct}%")