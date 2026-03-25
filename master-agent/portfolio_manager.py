"""
PortfolioManager - 投资组合经理
整合交易员辩论和风险评估，生成最终交易决策
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
    AnalysisState,
    AgentType,
    DebateRound,
    ResearchSummary,
    RiskAssessment,
    RiskLevel,
    TraderRecommendation,
    TradeDecision,
    TradingAction,
    TradingSignal,
)


PORTFOLIO_MANAGER_PROMPT = """You are the Portfolio Manager responsible for making the final investment decision.

## Your Role

After bull, neutral, and bear traders have made their recommendations, and risk assessment has been completed,
you must synthesize all inputs to produce the FINAL trading decision.

## Input Summary

You will receive:
1. Research Summary (bullish/bearish signal from researchers)
2. Three Trader Recommendations (bull/neutral/bear)
3. Risk Assessment (overall risk level and score)

## Decision Framework

### Step 1: Analyze Trader Consensus
- Do all three traders agree? → High confidence decision
- Do two out of three agree? → Moderate confidence, lean toward majority
- Are they split? → Lower confidence, prioritize risk management

### Step 2: Consider Risk Assessment
- LOW risk (0-30): Full position size acceptable
- MEDIUM risk (31-60): Reduce position by 25%
- HIGH risk (61-80): Reduce position by 50%
- EXTREME risk (81-100): Minimal position or avoid

### Step 3: Factor in Research Signal
- Strong consensus from research → Increase confidence
- Divergent analyst views → Decrease confidence, favor caution

### Step 4: Make Final Decision

Output Format (JSON):
{
  "action": "strong_buy|buy|hold|sell|strong_sell|avoid",
  "confidence": 0.75,
  "target_price": 150.00,
  "stop_loss": 135.00,
  "position_size": "large|medium|small|minimal|none",
  "position_pct": 10,
  "timeframe": "short_term|medium_term|long_term",
  "risk_adjusted": true,
  "reasoning": "Detailed final reasoning...",
  "key_factors": ["Factor 1", "Factor 2", "Factor 3"],
  "warnings": ["Warning if any"]
}

Action Guidelines:
- strong_buy: All signals bullish, low risk, high confidence
- buy: Majority bullish, acceptable risk
- hold: Mixed signals or moderate confidence
- sell: Majority bearish or high risk
- strong_sell: All signals bearish, high confidence
- avoid: Extreme risk or overwhelming bearish signals

Position Size Guidelines:
- large: 15-20% of portfolio
- medium: 8-12% of portfolio
- small: 3-7% of portfolio
- minimal: 1-2% of portfolio
- none: No position recommended
"""


class PortfolioManager:
    """投资组合管理器 - 最终决策者"""
    
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
                return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            except ImportError:
                return None
        return None
    
    def decide(
        self,
        symbol: str,
        research: ResearchSummary,
        trader_recommendations: List[TraderRecommendation],
        risk_assessment: RiskAssessment,
        trace_id: str = ""
    ) -> TradeDecision:
        """
        生成最终交易决策
        
        Args:
            symbol: 股票代码
            research: 研究综合报告
            trader_recommendations: 三位交易员的建议
            risk_assessment: 风险评估报告
            trace_id: 追踪ID
            
        Returns:
            TradeDecision: 最终交易决策
        """
        prompt = self._build_prompt(symbol, research, trader_recommendations, risk_assessment)
        
        response = self.llm_client.chat.completions.create(
            model=self.config.get("model", "gpt-4o"),
            messages=[
                {"role": "system", "content": PORTFOLIO_MANAGER_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # 映射动作
        action_map = {
            "strong_buy": TradingAction.STRONG_BUY,
            "buy": TradingAction.BUY,
            "hold": TradingAction.HOLD,
            "sell": TradingAction.SELL,
            "strong_sell": TradingAction.STRONG_SELL,
            "avoid": TradingAction.SELL,  # avoid 映射为 SELL
        }
        
        return TradeDecision(
            action=action_map.get(result.get("action", "hold"), TradingAction.HOLD),
            target_price=result.get("target_price"),
            stop_loss=result.get("stop_loss"),
            position_size=result.get("position_size", "medium"),
            confidence=result.get("confidence", 0.5),
            reasoning=result.get("reasoning", ""),
            risk_level=risk_assessment.overall_risk,
            timeframe=result.get("timeframe", "medium_term"),
            analyst_signals={
                "research": research.overall_signal,
                "risk_level": risk_assessment.overall_risk
            }
        )
    
    def decide_simple(
        self,
        symbol: str,
        research: ResearchSummary,
        trader_recommendations: List[TraderRecommendation],
        risk_assessment: RiskAssessment,
    ) -> TradeDecision:
        """
        简化版决策逻辑（不调用LLM，直接基于规则）
        用于快速决策或备用
        
        Args:
            symbol: 股票代码
            research: 研究综合报告
            trader_recommendations: 三位交易员的建议
            risk_assessment: 风险评估报告
            
        Returns:
            TradeDecision: 最终交易决策
        """
        # 1. 统计交易员信号
        buy_count = sum(1 for r in trader_recommendations if r.action in [TradingAction.BUY, TradingAction.STRONG_BUY])
        sell_count = sum(1 for r in trader_recommendations if r.action in [TradingAction.SELL, TradingAction.STRONG_SELL])
        hold_count = len(trader_recommendations) - buy_count - sell_count
        
        # 2. 计算加权置信度
        avg_trader_confidence = sum(r.confidence for r in trader_recommendations) / len(trader_recommendations) if trader_recommendations else 0.5
        combined_confidence = (research.confidence + avg_trader_confidence) / 2
        
        # 3. 根据风险等级调整
        risk_multiplier = {
            RiskLevel.LOW: 1.0,
            RiskLevel.MEDIUM: 0.85,
            RiskLevel.HIGH: 0.7,
            RiskLevel.EXTREME: 0.5
        }.get(risk_assessment.overall_risk, 1.0)
        
        adjusted_confidence = combined_confidence * risk_multiplier
        
        # 4. 决定动作
        if buy_count > sell_count and buy_count >= 2:
            action = TradingAction.BUY if buy_count == 3 else TradingAction.BUY
        elif sell_count > buy_count and sell_count >= 2:
            action = TradingAction.SELL
        elif buy_count > sell_count:
            action = TradingAction.HOLD if risk_assessment.overall_risk in [RiskLevel.HIGH, RiskLevel.EXTREME] else TradingAction.BUY
        elif sell_count > buy_count:
            action = TradingAction.SELL
        else:
            action = TradingAction.HOLD
        
        # 5. 决定仓位
        position_map = {
            RiskLevel.LOW: "large" if buy_count > sell_count else "small",
            RiskLevel.MEDIUM: "medium",
            RiskLevel.HIGH: "small",
            RiskLevel.EXTREME: "minimal"
        }
        
        # 如果是卖出信号，仓位应该小
        if action in [TradingAction.SELL, TradingAction.STRONG_SELL]:
            position_map = {
                RiskLevel.LOW: "small",
                RiskLevel.MEDIUM: "small",
                RiskLevel.HIGH: "minimal",
                RiskLevel.EXTREME: "none"
            }
        
        # 6. 构建理由
        trader_signals = [f"{r.trader_type.value}: {r.action.value}" for r in trader_recommendations]
        reasoning = (
            f"研究信号: {research.overall_signal.value} (置信度 {research.confidence:.2f})\n"
            f"交易员信号: {', '.join(trader_signals)}\n"
            f"风险等级: {risk_assessment.overall_risk.value} (评分 {risk_assessment.risk_score:.0f}/100)"
        )
        
        return TradeDecision(
            action=action,
            target_price=None,  # 简化版不计算目标价
            stop_loss=None,
            position_size=position_map.get(risk_assessment.overall_risk, "medium"),
            confidence=adjusted_confidence,
            reasoning=reasoning,
            risk_level=risk_assessment.overall_risk,
            timeframe="medium_term",
            analyst_signals={
                "research": research.overall_signal,
                "risk_level": TradingSignal.UNKNOWN  # 风险等级单独存储
            }
        )
    
    def _build_prompt(
        self,
        symbol: str,
        research: ResearchSummary,
        trader_recommendations: List[TraderRecommendation],
        risk_assessment: RiskAssessment
    ) -> str:
        """构建决策提示词"""
        
        # 整理交易员建议
        trader_text = []
        for rec in trader_recommendations:
            trader_text.append(
                f"## {rec.trader_type.value.upper()} Trader\n"
                f"- Action: {rec.action.value.upper()}\n"
                f"- Confidence: {rec.confidence:.2f}\n"
                f"- Position Size: {rec.position_size}\n"
                f"- Target Price: {rec.target_price or 'N/A'}\n"
                f"- Stop Loss: {rec.stop_loss or 'N/A'}\n"
                f"- Reasoning: {rec.reasoning[:300]}..."
            )
        
        # 整理风险因素
        risk_text = []
        for rf in risk_assessment.risk_factors:
            risk_text.append(f"- {rf.factor_name}: {rf.level.value} - {rf.description}")
        
        prompt = f"""Make the FINAL trading decision for {symbol}.

## Research Summary

Signal: {research.overall_signal.value}
Confidence: {research.confidence:.2f}
Consensus Level: {research.consensus_level:.2f}

Key Insights:
{chr(10).join(f"- {i}" for i in research.key_insights)}

Contradictions:
{chr(10).join(f"- {c}" for c in research.contradictions)}

Reasoning:
{research.reasoning}

## Trader Recommendations

{chr(10).join(trader_text)}

## Risk Assessment

Overall Risk: {risk_assessment.overall_risk.value}
Risk Score: {risk_assessment.risk_score:.0f}/100

Risk Factors:
{chr(10).join(risk_text) if risk_text else "- No significant risk factors"}

Warnings:
{chr(10).join(f"- {w}" for w in risk_assessment.warnings) if risk_assessment.warnings else "- No warnings"}

## Your Task

1. Analyze consensus among traders
2. Factor in risk assessment
3. Consider research signal strength
4. Make the FINAL decision

Provide your decision in the specified JSON format."""
        
        return prompt


if __name__ == "__main__":
    print("Testing Portfolio Manager...")
    
    from shared.models import AgentType, TradingSignal
    
    # 创建模拟输入
    research = ResearchSummary(
        overall_signal=TradingSignal.BUY,
        confidence=0.8,
        consensus_level=0.75,
        key_insights=["Strong growth potential", "Market leader in AI"],
        contradictions=["High valuation", "Competitive pressures"],
        reasoning="Despite high valuation, growth prospects are compelling"
    )
    
    traders = [
        TraderRecommendation(
            trader_type=AgentType.BULL_TRADER,
            action=TradingAction.BUY,
            target_price=180.0,
            stop_loss=140.0,
            position_size="large",
            confidence=0.85,
            reasoning="Aggressive growth play with high conviction"
        ),
        TraderRecommendation(
            trader_type=AgentType.NEUTRAL_TRADER,
            action=TradingAction.HOLD,
            target_price=160.0,
            stop_loss=145.0,
            position_size="medium",
            confidence=0.6,
            reasoning="Wait for better entry point"
        ),
        TraderRecommendation(
            trader_type=AgentType.BEAR_TRADER,
            action=TradingAction.SELL,
            target_price=140.0,
            stop_loss=155.0,
            position_size="small",
            confidence=0.7,
            reasoning="Valuation too high, risk/reward unfavorable"
        )
    ]
    
    risk = RiskAssessment(
        overall_risk=RiskLevel.MEDIUM,
        risk_score=55.0,
        position_size_recommendation="medium",
        max_position_pct=10.0,
        warnings=["Elevated volatility", "High PE ratio"]
    )
    
    # 测试简化版
    pm = PortfolioManager()
    decision = pm.decide_simple("NVDA", research, traders, risk)
    
    print(f"\n📊 Portfolio Manager Decision:")
    print(f"   Action: {decision.action.value.upper()}")
    print(f"   Confidence: {decision.confidence:.2f}")
    print(f"   Position: {decision.position_size}")
    print(f"   Risk Level: {decision.risk_level.value}")
    print(f"\n📝 Reasoning:")
    print(f"   {decision.reasoning}")