"""
TradingOrchestrator - Phase 3 完整版
包含完整流程：
Phase 1: 三分析师并行 (基本面/技术面/情绪面)
Phase 2: 多空研究员辩论
Phase 3: 三交易员辩论 + 风险管理 + 最终决策
"""

import asyncio
import uuid
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

# 使用共享配置模块设置路径
from shared import config
config.setup_paths()

from shared.models import (
    AnalysisState,
    AnalysisStatus,
    FeishuCommand,
    TAOConfig,
    TradingAction,
    TradeDecision,
    TradingSignal,
    TraderRecommendation,
    RiskAssessment,
)

# 导入所有 Skills
from fundamental_analyst import FundamentalAnalyst
from technical_analyst import TechnicalAnalyst
from sentiment_analyst import SentimentAnalyst
from researcher_bull import BullResearcher
from researcher_bear import BearResearcher
from research_manager import ResearchManager
from feishu_adapter import FeishuAdapter
from trader_debate_orchestrator import TraderDebateOrchestrator
from portfolio_manager import PortfolioManager


class TradingOrchestrator:
    """Phase 3 完整版交易分析编排器"""
    
    def __init__(self, config: Optional[TAOConfig] = None):
        self.config = config or TAOConfig()
        self.active_analyses: Dict[str, AnalysisState] = {}
        
        # 初始化分析师配置
        analyst_config = {
            "llm_provider": self.config.deep_think_llm.provider,
            "model": self.config.deep_think_llm.model,
            "temperature": 0.7
        }
        
        # 初始化 Phase 1: 三位分析师
        self.fundamental_analyst = FundamentalAnalyst(config=analyst_config)
        self.technical_analyst = TechnicalAnalyst(config=analyst_config)
        self.sentiment_analyst = SentimentAnalyst(config=analyst_config)
        
        # 初始化 Phase 2: 研究员辩论
        self.bull_researcher = BullResearcher(config=analyst_config)
        self.bear_researcher = BearResearcher(config=analyst_config)
        self.research_manager = ResearchManager(config=analyst_config)
        
        # 初始化 Phase 3: 交易员辩论 + 风险管理
        self.trader_debate = TraderDebateOrchestrator(config=analyst_config)
        self.portfolio_manager = PortfolioManager(config=analyst_config)
    
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
            import traceback
            traceback.print_exc()
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
        """执行完整三阶段分析流程"""
        
        # ========== Phase 1: 三分析师并行分析 ==========
        await self._run_analysts(state)
        
        # ========== Phase 2: 多空研究员辩论 ==========
        await self._run_researcher_debate(state)
        
        # ========== Phase 3: 交易员辩论 + 风险管理 + 最终决策 ==========
        await self._run_trader_debate_and_risk(state)
        
        state.update_status(AnalysisStatus.COMPLETED)
    
    # ==================== Phase 1: 三分析师 ====================
    
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
        
        print(f"[{state.trace_id}] Phase 1: Running 3 analysts in parallel...")
        
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
        self._process_analyst_result(state, "fundamental", results[0])
        self._process_analyst_result(state, "technical", results[1])
        self._process_analyst_result(state, "sentiment", results[2])
    
    def _process_analyst_result(self, state: AnalysisState, analyst_type: str, result):
        """处理单个分析师结果"""
        report_attr = f"{analyst_type}_report"
        
        if isinstance(result, Exception):
            print(f"[{state.trace_id}] ❌ {analyst_type.capitalize()} analysis failed: {result}")
        elif hasattr(result, 'success') and result.success:
            setattr(state, report_attr, result.report)
            signal = result.report.signal.value if result.report.signal else "unknown"
            conf = result.report.confidence if result.report else 0
            print(f"[{state.trace_id}] ✅ {analyst_type.capitalize()} completed: {signal} ({conf:.2f})")
        else:
            error_msg = getattr(result, 'error', 'Unknown error') if not isinstance(result, Exception) else str(result)
            print(f"[{state.trace_id}] ❌ {analyst_type.capitalize()} error: {error_msg}")
    
    # ==================== Phase 2: 研究员辩论 ====================
    
    async def _run_researcher_debate(self, state: AnalysisState):
        """运行多空研究员辩论"""
        state.update_status(AnalysisStatus.RESEARCHING)
        
        # 准备分析师报告
        analyst_reports = {
            "fundamental": state.fundamental_report,
            "technical": state.technical_report,
            "sentiment": state.sentiment_report
        }
        
        print(f"[{state.trace_id}] Phase 2: Running researcher debate...")
        
        debate_history = []
        max_rounds = self.config.max_debate_rounds
        
        for round_num in range(1, max_rounds + 1):
            print(f"[{state.trace_id}] Research Debate Round {round_num}/{max_rounds}")
            
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
            
            bull_conf = bull_view.get('confidence', 0) if isinstance(bull_view, dict) else 0
            bear_conf = bear_view.get('confidence', 0) if isinstance(bear_view, dict) else 0
            print(f"[{state.trace_id}] Bull confidence: {bull_conf:.2f}, Bear confidence: {bear_conf:.2f}")
        
        # 研究经理整合
        print(f"[{state.trace_id}] Synthesizing research...")
        state.research_summary = self.research_manager.synthesize(
            symbol=state.stock_symbol,
            debate_history=debate_history,
            analyst_reports=analyst_reports,
            trace_id=state.trace_id
        )
        
        signal = state.research_summary.overall_signal.value if state.research_summary else "unknown"
        conf = state.research_summary.confidence if state.research_summary else 0
        print(f"[{state.trace_id}] ✅ Research synthesis: {signal} ({conf:.2f})")
    
    # ==================== Phase 3: 交易员辩论 + 风险管理 ====================
    
    async def _run_trader_debate_and_risk(self, state: AnalysisState):
        """运行交易员辩论、风险评估，生成最终决策"""
        state.update_status(AnalysisStatus.RISK_ASSESSING)
        
        if not state.research_summary:
            print(f"[{state.trace_id}] ⚠️ No research summary, using fallback decision")
            await self._make_fallback_decision(state)
            return
        
        print(f"[{state.trace_id}] Phase 3: Trader debate + Risk assessment...")
        
        # Step 1: 三交易员辩论
        print(f"[{state.trace_id}] Running trader debate...")
        trader_recommendations = await asyncio.to_thread(
            self.trader_debate.run_trader_debate,
            symbol=state.stock_symbol,
            research=state.research_summary,
            trace_id=state.trace_id
        )
        state.trader_recommendations = trader_recommendations
        
        for rec in trader_recommendations:
            print(f"[{state.trace_id}] {rec.trader_type.value}: {rec.action.value.upper()} (conf: {rec.confidence:.2f})")
        
        # Step 2: 风险评估
        print(f"[{state.trace_id}] Running risk assessment...")
        risk_assessment = await asyncio.to_thread(
            self.trader_debate.assess_risk,
            symbol=state.stock_symbol,
            research=state.research_summary,
            trader_recommendations=trader_recommendations,
            trace_id=state.trace_id
        )
        state.risk_assessment = risk_assessment
        
        print(f"[{state.trace_id}] Risk: {risk_assessment.overall_risk.value} ({risk_assessment.risk_score:.0f}/100)")
        
        # Step 3: 最终决策
        state.update_status(AnalysisStatus.FINALIZING)
        print(f"[{state.trace_id}] Making final decision...")
        
        final_decision = await asyncio.to_thread(
            self.portfolio_manager.decide_simple,
            symbol=state.stock_symbol,
            research=state.research_summary,
            trader_recommendations=trader_recommendations,
            risk_assessment=risk_assessment
        )
        state.final_decision = final_decision
        
        print(f"[{state.trace_id}] ✅ Final decision: {final_decision.action.value.upper()} (conf: {final_decision.confidence:.2f})")
    
    async def _make_fallback_decision(self, state: AnalysisState):
        """当研究综合失败时的备用决策"""
        reports = [r for r in [state.fundamental_report, state.technical_report, state.sentiment_report] if r]
        
        if not reports:
            state.final_decision = TradeDecision(
                action=TradingAction.HOLD,
                confidence=0.0,
                reasoning="No analysis data available",
                analyst_signals={}
            )
            return
        
        buy_count = sum(1 for r in reports if r.signal == TradingSignal.BUY)
        sell_count = sum(1 for r in reports if r.signal == TradingSignal.SELL)
        avg_conf = sum(r.confidence for r in reports) / len(reports)
        
        if buy_count > sell_count:
            action = TradingAction.BUY
        elif sell_count > buy_count:
            action = TradingAction.SELL
        else:
            action = TradingAction.HOLD
        
        state.final_decision = TradeDecision(
            action=action,
            confidence=avg_conf * 0.8,  # 降低置信度因为没有完整流程
            reasoning=f"Fallback decision based on {len(reports)} analyst reports",
            analyst_signals={r.agent_type.value: r.signal for r in reports}
        )
    
    def generate_feishu_report(self, state: AnalysisState) -> Dict[str, Any]:
        """生成飞书报告"""
        return FeishuAdapter.generate_analysis_card(state)
    
    def get_analysis_status(self, trace_id: str) -> Optional[AnalysisState]:
        """获取分析状态"""
        return self.active_analyses.get(trace_id)


# ==================== 便捷函数 ====================

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
    print("=" * 70)
    print("TradingAgents-OpenClaw Phase 3 完整流程测试")
    print("=" * 70)
    
    config = TAOConfig()
    config.max_debate_rounds = 2
    
    print("\n开始分析 NVDA...")
    result = await analyze_stock(symbol="NVDA", config=config)
    
    print("\n" + "=" * 70)
    print("分析完成")
    print("=" * 70)
    print(f"股票: {result.stock_symbol}")
    print(f"状态: {result.status.value}")
    
    # Phase 1 结果
    if result.fundamental_report:
        print(f"\n📊 基本面: {result.fundamental_report.signal.value} ({result.fundamental_report.confidence:.2f})")
    if result.technical_report:
        print(f"📈 技术面: {result.technical_report.signal.value} ({result.technical_report.confidence:.2f})")
    if result.sentiment_report:
        print(f"💬 情绪面: {result.sentiment_report.signal.value} ({result.sentiment_report.confidence:.2f})")
    
    # Phase 2 结果
    if result.research_summary:
        print(f"\n🔬 研究综合: {result.research_summary.overall_signal.value} ({result.research_summary.confidence:.2f})")
    
    # Phase 3 结果
    if result.trader_recommendations:
        print(f"\n📋 交易员建议:")
        for rec in result.trader_recommendations:
            print(f"   {rec.trader_type.value}: {rec.action.value.upper()} (conf: {rec.confidence:.2f})")
    
    if result.risk_assessment:
        print(f"\n⚠️ 风险评估: {result.risk_assessment.overall_risk.value} ({result.risk_assessment.risk_score:.0f}/100)")
    
    # 最终决策
    if result.final_decision:
        print(f"\n🎯 最终决策: {result.final_decision.action.value.upper()}")
        print(f"   置信度: {result.final_decision.confidence:.2f}")
        print(f"   仓位: {result.final_decision.position_size}")
        print(f"   风险等级: {result.final_decision.risk_level.value}")
        print(f"   理由: {result.final_decision.reasoning[:200]}...")
    
    if result.error_message:
        print(f"\n❌ 错误: {result.error_message}")


if __name__ == "__main__":
    asyncio.run(main())