"""
交易员基类和三位交易员实现
Bull / Neutral / Bear
"""

import os
import json
from typing import Any, Dict, Optional
from abc import ABC, abstractmethod

import sys
sys.path.insert(0, '/root/.openclaw-coding/workspace/TradingAgents-OpenClaw')
from shared.models import TraderRecommendation, TradingAction, ResearchSummary


TRADER_BASE_PROMPT = """You are a professional trader with expertise in position sizing and risk management.

Your task is to develop a specific trading strategy based on the provided research synthesis.

## Output Format

Respond in JSON format:
{
  "action": "buy|sell|hold",
  "confidence": 0.85,
  "target_price": 150.00,
  "stop_loss": 135.00,
  "position_size": "large|medium|small",
  "position_pct": 15,
  "timeframe": "short_term|medium_term|long_term",
  "reasoning": "Detailed trading rationale...",
  "key_catalysts": ["catalyst1", "catalyst2"],
  "risk_factors": ["risk1", "risk2"]
}

Position Size Guidelines:
- large: 10-20% of portfolio (high conviction)
- medium: 5-10% of portfolio (moderate conviction)
- small: 2-5% of portfolio (low conviction or high risk)
"""


class BaseTrader(ABC):
    """交易员基类"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.llm_client = self._init_llm_client()
        self.trader_type = "base"
    
    def _init_llm_client(self):
        provider = self.config.get("llm_provider", "openai")
        if provider == "openai":
            from openai import OpenAI
            return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        raise ValueError(f"Unsupported LLM provider: {provider}")
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        pass
    
    def trade(self, symbol: str, research: ResearchSummary, trace_id: str = "") -> TraderRecommendation:
        """生成交易建议"""
        
        prompt = self._build_prompt(symbol, research)
        
        response = self.llm_client.chat.completions.create(
            model=self.config.get("model", "gpt-4o"),
            messages=[
                {"role": "system", "content": self.get_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        return TraderRecommendation(
            trader_type=self._get_agent_type(),
            action=TradingAction(result.get("action", "hold")),
            target_price=result.get("target_price"),
            stop_loss=result.get("stop_loss"),
            position_size=result.get("position_size", "medium"),
            confidence=result.get("confidence", 0.5),
            reasoning=result.get("reasoning", "")
        )
    
    def _build_prompt(self, symbol: str, research: ResearchSummary) -> str:
        return f"""Develop a trading strategy for {symbol}.

## Research Synthesis

Signal: {research.overall_signal.value}
Confidence: {research.confidence}
Consensus Level: {research.consensus_level}

Key Insights:
{chr(10).join(f"- {i}" for i in research.key_insights)}

Contradictions:
{chr(10).join(f"- {c}" for c in research.contradictions)}

Reasoning:
{research.reasoning}

## Instructions

Develop a specific trading plan with:
1. Clear action (buy/sell/hold)
2. Target price and stop loss
3. Position size recommendation
4. Investment timeframe
5. Key catalysts to watch
6. Risk factors

Provide your trading plan in the specified JSON format."""
    
    @abstractmethod
    def _get_agent_type(self):
        pass


class BullTrader(BaseTrader):
    """激进交易员 - 积极做多"""
    
    def __init__(self, config=None):
        super().__init__(config)
        self.trader_type = "bull"
    
    def get_system_prompt(self) -> str:
        return TRADER_BASE_PROMPT + """

## Your Trading Style: AGGRESSIVE / BULLISH

You are an aggressive trader focused on maximizing upside.

Characteristics:
- Prefer larger position sizes when conviction is high
- Set ambitious target prices
- Use wider stop losses to avoid being stopped out by noise
- Focus on momentum and growth catalysts
- Willing to accept higher risk for higher returns

Bias: You naturally lean toward BUY actions unless risks are overwhelming.
"""
    
    def _get_agent_type(self):
        from shared.models import AgentType
        return AgentType.BULL_TRADER


class NeutralTrader(BaseTrader):
    """中性交易员 - 观望等待"""
    
    def __init__(self, config=None):
        super().__init__(config)
        self.trader_type = "neutral"
    
    def get_system_prompt(self) -> str:
        return TRADER_BASE_PROMPT + """

## Your Trading Style: NEUTRAL / BALANCED

You are a balanced trader focused on risk-adjusted returns.

Characteristics:
- Prefer medium position sizes
- Wait for clear entry signals
- Use tight stop losses to protect capital
- Focus on uncertainty and conflicting signals
- Prioritize capital preservation over aggressive gains

Bias: You naturally lean toward HOLD actions unless there's clear direction.
"""
    
    def _get_agent_type(self):
        from shared.models import AgentType
        return AgentType.NEUTRAL_TRADER


class BearTrader(BaseTrader):
    """保守交易员 - 防御减仓"""
    
    def __init__(self, config=None):
        super().__init__(config)
        self.trader_type = "bear"
    
    def get_system_prompt(self) -> str:
        return TRADER_BASE_PROMPT + """

## Your Trading Style: CONSERVATIVE / BEARISH

You are a defensive trader focused on protecting capital.

Characteristics:
- Prefer smaller position sizes or no position
- Focus on downside risks and overvaluation
- Use tight stop losses and early exit strategies
- Skeptical of hype and momentum
- Prioritize avoiding losses over capturing gains

Bias: You naturally lean toward SELL or AVOID actions unless value is compelling.
"""
    
    def _get_agent_type(self):
        from shared.models import AgentType
        return AgentType.BEAR_TRADER


if __name__ == "__main__":
    print("Testing Traders...")
    
    from shared.models import ResearchSummary, TradingSignal
    
    research = ResearchSummary(
        overall_signal=TradingSignal.BUY,
        confidence=0.8,
        consensus_level=0.7,
        key_insights=["Strong growth", "Market leader"],
        contradictions=["Valuation high"],
        reasoning="Growth outweighs valuation concerns"
    )
    
    # 测试三位交易员
    for TraderClass, name in [(BullTrader, "Bull"), (NeutralTrader, "Neutral"), (BearTrader, "Bear")]:
        trader = TraderClass()
        rec = trader.trade("TEST", research)
        print(f"\n{name} Trader:")
        print(f"  Action: {rec.action.value}")
        print(f"  Confidence: {rec.confidence}")
        print(f"  Position: {rec.position_size}")
