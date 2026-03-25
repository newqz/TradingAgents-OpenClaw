"""
TradingOrchestrator - 完整版
支持三分析师 + 多空辩论
"""

import asyncio
import uuid
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

sys.path.insert(0, '/root/.openclaw/workspace/TradingAgents-OpenClaw')

from shared.models import (
    AnalysisState, AnalysisStatus, FeishuCommand, TAOConfig,
    TradingAction, TradeDecision, TradingSignal
)

# 导入 Skills
sys.path.insert(0, '/root/.openclaw/workspace/TradingAgents-OpenClaw/skills/skill-tao-fundamental')
sys.path.insert(0, '/root/.openclaw/workspace/TradingAgents-OpenClaw/skills/skill-tao-technical')
sys.path.insert(0, '/root/.openclaw/workspace/TradingAgents-OpenClaw/skills/skill-tao-sentiment')
sys.path.insert(0, '/root/.openclaw/workspace/TradingAgents-OpenClaw/skills/skill-tao-researcher-bull')
sys.path.insert(0, '/root/.openclaw/workspace/TradingAgents-OpenClaw/skills/skill-tao-researcher-bear')
sys.path.insert(0, '/root/.openclaw/workspace/TradingAgents-OpenClaw/skills/skill-tao-research-manager')
sys.path.insert(0, '/root/.openclaw/workspace/TradingAgents-OpenClaw/master-agent')

from fundamental_analyst import FundamentalAnalyst
from technical_analyst import TechnicalAnalyst
from sentiment_analyst import SentimentAnalyst
from researcher_bull import BullResearcher
from researcher_bear import BearResearcher
from research_manager import ResearchManager
from feishu_adapter import FeishuAdapter


class TradingOrchestrator:
    """完整版交易分析编排器"""
    
    def __init__(self, config: Optional[TAOConfig] = None):
        self.config = config or TAOConfig()
        self.active_analyses: Dict[str, AnalysisState] = {}
        
        # 初始化所有 Analysts
        analyst_config = {
            "llm_provider": self.config.deep_think_llm.provider,
            "model": self.config.deep_think_llm.model,
            "temperature": 0.7
        }
        
        self.fundamental_analyst = FundamentalAnalyst(config=analyst_config)
        self.technical_analyst = TechnicalAnalyst(config=analyst_config)
        self.sentiment_analyst = SentimentAnalyst(config=analyst_config)
        
        # 初始化 Researchers
        self.bull_researcher = BullResearcher(config=analyst_config)
        self.bear_researcher = BearResearcher(config=analyst_config)
        self.research_manager = ResearchManager(config=analyst_config)
    
    async def process_command(self, command: FeishuCommand) -> AnalysisState:
        """处理飞书指令"""
        state = self._create_analysis_state(command)
        self.active_analyses[state.trace_id] = state
        
        try:
            await self._execute_analysis(state)
        except Exception as e:
            state.update_status(AnalysisStatus.FAILED)
            state.error_message = str(e)
            print(f"[{state.trace_id}] Analysis failed: {e}")
        finally:
            state.completed_at = datetime.now()
            
        return state
    
    def _create_analysis_state(self, command: FeishuCommand) -> AnalysisState:
        """创建初始分析状态"""
        trace_id = str(uuid.uuid4())[:8]
        
        return AnalysisState(
            trace_id=trace_id,
            stock_symbol=command.stock_symbols[0] if command.stock_symbols else "",
            analysis_date=command.analysis_date or datetime.now().strftime("%Y-%m-%d"),
            status=AnalysisStatus.INITIAL,
            user_id=command.user_id,
            chat_id=command.chat_id,
            config=self.config.dict()
        )
    
    async def _execute_analysis(self, state: AnalysisState):
        """执行完整分析流程"""
        
        # Phase 1: 三分析师并行分析
        await self._run_analysts(state)
        
        # Phase 2: 多空研究员辩论
        await self._run_researcher_debate(state)
        
        # Phase 3: 生成最终决策
        await self._make_final_decision(state)
        
        state.update_status(AnalysisStatus.COMPLETED)
    
    async def _run_analysts(self, state: AnalysisState):
        """并行运行三位分析师"""
        state.update_status(AnalysisStatus.ANALYZING)
        
        from shared.models import AnalystInput
        
        base_input = {
            "trace_id": state.trace_id,
            "stock_symbol": state.stock_symbol,
            "analysis_date": state.analysis_date,
            "config": {
                "llm_provider": self.config.deep_think_llm.provider,
                "model": self.config.deep_think_llm.model,
                "temperature": 0.7
            }
        }
        
        print(f"[{state.trace_id}] Running parallel analysts...")
        
        # 并行启动三位分析师
        fundamental_task = asyncio.create_task(
            asyncio.to_thread(
                self.fundamental_analyst.analyze,
                AnalystInput(**base_input)
            )
        )
        technical_task = asyncio.create_task(
            asyncio.to_thread(
                self.technical_analyst.analyze,
                AnalystInput(**{**base_input, "config": {**base_input["config"], "indicators": ["rsi", "macd", "bollinger_bands"]}})
            )
        )
        sentiment_task = asyncio.create_task(
            asyncio.to_thread(
                self.sentiment_analyst.analyze,
                AnalystInput(**base_input)
            )
        )
        
        results = await asyncio.gather(
            fundamental_task, technical_task, sentiment_task,
            return_exceptions=True
        )
        
        # 处理结果
        if not isinstance(results[0], Exception) and results[0].success:
            state.fundamental_report = results[0].report
            print(f"[{state.trace_id}] ✅ Fundamental analysis completed")
        else:
            print(f"[{state.trace_id}] ❌ Fundamental analysis failed: {results[0] if isinstance(results[0], Exception) else results[0].error}")
        
        if not isinstance(results[1], Exception) and results[1].success:
            state.technical_report = results[1].report
            print(f"[{state.trace_id}] ✅ Technical analysis completed")
        else:
            print(f"[{state.trace_id}] ❌ Technical analysis failed: {results[1] if isinstance(results[1], Exception) else results[1].error}")
        
        if not isinstance(results[2], Exception) and results[2].success:
            state.sentiment_report = results[2].report
            print(f"[{state.trace_id}] ✅ Sentiment analysis completed")
        else:
            print(f"[{state.trace_id}] ❌ Sentiment analysis failed: {results[2] if isinstance(results[2], Exception) else results[2].error}")
    
    async def _run_researcher_debate(self, state: AnalysisState):
        """运行多空研究员辩论"""
        state.update_status(AnalysisStatus.RESEARCHING)
        
        # 准备分析师报告
        analyst_reports = {
            "fundamental": state.fundamental_report,
            "technical": state.technical_report,
            "sentiment": state.sentiment_report
        }
        
        print(f"[{state.trace_id}] Starting researcher debate...")
        
        debate_history = []
        max_rounds = self.config.max_debate_rounds
        
        for round_num in range(1, max_rounds + 1):
            print(f"[{state.trace_id}] Debate Round {round_num}/{max_rounds}")
            
            # 获取上一轮的观点（如果有）
            prev_bull = debate_history[-1].get("bull_view", {}).get("argument") if debate_history else None
            prev_bear = debate_history[-1].get("bear_view", {}).get("argument") if debate_history else None
            
            # 并行获取双方观点
            bull_task = asyncio.create_task(
                asyncio.to_thread(
                    self.bull_researcher.research,
                    symbol=state.stock_symbol,
                    analyst_reports=analyst_reports,
                    opponent_argument=prev_bear,
                    round_num=round_num,
                    trace_id=state.trace_id
                )
            )
            bear_task = asyncio.create_task(
                asyncio.to_thread(
                    self.bear_researcher.research,
                    symbol=state.stock_symbol,
                    analyst_reports=analyst_reports,
                    opponent_argument=prev_bull,
                    round_num=round_num,
                    trace_id=state.trace_id
                )
            )
            
            bull_view, bear_view = await asyncio.gather(bull_task, bear_task)
            
            debate_history.append({
                "round": round_num,
                "bull_view": bull_view,
                "bear_view": bear_view
            })
            
            print(f"[{state.trace_id}] Bull confidence: {bull_view.get('confidence')}, Bear confidence: {bear_view.get('confidence')}")
        
        # 研究经理整合
        print(f"[{state.trace_id}] Synthesizing research...")
        state.research_summary = self.research_manager.synthesize(
            symbol=state.stock_symbol,
            debate_history=debate_history,
            analyst_reports=analyst_reports,
            trace_id=state.trace_id
        )
        
        print(f"[{state.trace_id}] ✅ Research synthesis completed: {state.research_summary.overall_signal.value}")
    
    async def _make_final_decision(self, state: AnalysisState):
        """生成最终决策"""
        state.update_status(AnalysisStatus.FINALIZING)
        
        research = state.research_summary
        
        # 根据研究综合生成交易决策
        signal_map = {
            TradingSignal.BUY: TradingAction.BUY,
            TradingSignal.SELL: TradingAction.SELL,
            TradingSignal.HOLD: TradingAction.HOLD
        }
        
        action = signal_map.get(research.overall_signal, TradingAction.HOLD)
        
        # 收集分析师信号
        analyst_signals = {}
        if state.fundamental_report:
            analyst_signals["fundamental"] = state.fundamental_report.signal
        if state.technical_report:
            analyst_signals["technical"] = state.technical_report.signal
        if state.sentiment_report:
            analyst_signals["sentiment"] = state.sentiment_report.signal
        
        state.final_decision = TradeDecision(
            action=action,
            confidence=research.confidence,
            reasoning=research.reasoning,
            analyst_signals=analyst_signals,
            risk_level="medium"  # 可在后续加入风险管理
        )
        
        print(f"[{state.trace_id}] ✅ Final decision: {action.value} (confidence: {research.confidence:.2f})")
    
    def generate_feishu_report(self, state: AnalysisState) -> Dict[str, Any]:
        """生成飞书报告"""
        return FeishuAdapter.generate_analysis_card(state)


# 便捷函数
async def analyze_stock(
    symbol: str,
    date: Optional[str] = None,
    config: Optional[TAOConfig] = None,
    user_id: str = "",
    chat_id: str = ""
) -> AnalysisState:
    """分析单只股票"""
    orchestrator = TradingOrchestrator(config)
    
    command = FeishuCommand(
        command="analyze",
        stock_symbols=[symbol],
        analysis_date=date,
        user_id=user_id,
        chat_id=chat_id
    )
    
    return await orchestrator.process_command(command)


async def main():
    """测试主函数"""
    print("=" * 60)
    print("TradingAgents-OpenClaw 完整版测试")
    print("=" * 60)
    
    config = TAOConfig()
    config.max_debate_rounds = 2
    
    result = await analyze_stock(
        symbol="NVDA",
        config=config
    )
    
    print("\n" + "=" * 60)
    print("分析完成")
    print("=" * 60)
    print(f"股票: {result.stock_symbol}")
    print(f"状态: {result.status.value}")
    
    if result.final_decision:
        print(f"\n最终决策: {result.final_decision.action.value.upper()}")
        print(f"置信度: {result.final_decision.confidence:.2f}")
        print(f"理由: {result.final_decision.reasoning[:200]}...")
    
    if result.error_message:
        print(f"\n错误: {result.error_message}")


if __name__ == "__main__":
    asyncio.run(main())
