"""
TradingOrchestrator - Master Agent 核心编排逻辑
负责调度所有 sub-agents，管理分析流程
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
    TradingSignal
)
from master_agent.feishu_adapter import FeishuAdapter

# 导入 Analysts
from skill_tao_fundamental.fundamental_analyst import FundamentalAnalyst
from skill_tao_technical.technical_analyst import TechnicalAnalyst


class TradingOrchestrator:
    """
    交易分析编排器
    
    职责：
    1. 解析用户指令
    2. 初始化分析状态
    3. 并行调度 Analyst Skills
    4. 生成最终报告
    5. 发布到飞书
    """
    
    def __init__(self, config: Optional[TAOConfig] = None):
        self.config = config or TAOConfig()
        self.active_analyses: Dict[str, AnalysisState] = {}
        
        # 初始化 Analysts
        analyst_config = {
            "llm_provider": self.config.deep_think_llm.provider,
            "model": self.config.deep_think_llm.model,
            "temperature": self.config.deep_think_llm.temperature
        }
        
        self.fundamental_analyst = FundamentalAnalyst(config=analyst_config)
        self.technical_analyst = TechnicalAnalyst(config=analyst_config)
    
    async def process_command(self, command: FeishuCommand) -> AnalysisState:
        """
        处理飞书指令
        
        Args:
            command: 解析后的飞书指令
            
        Returns:
            AnalysisState: 完整的分析状态
        """
        # 1. 创建分析状态
        state = self._create_analysis_state(command)
        self.active_analyses[state.trace_id] = state
        
        try:
            # 2. 执行分析流程 (Phase 1 MVP: 基本面 + 技术面)
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
        """执行完整分析流程 (Phase 1 MVP)"""
        
        # Phase 1: 并行分析师分析 (基本面 + 技术面)
        await self._run_analysts(state)
        
        # Phase 2: 简化版最终决策 (Phase 1 暂不包括研究员、交易员辩论、风险管理)
        await self._make_simple_decision(state)
        
        state.update_status(AnalysisStatus.COMPLETED)
    
    async def _run_analysts(self, state: AnalysisState):
        """
        并行运行分析师
        
        Phase 1 MVP: 基本面 + 技术面
        Phase 2: 增加情绪面、研究员、交易员辩论、风险管理
        """
        state.update_status(AnalysisStatus.ANALYZING)
        
        from shared.models import AnalystInput
        
        # 准备输入
        fundamental_input = AnalystInput(
            trace_id=state.trace_id,
            stock_symbol=state.stock_symbol,
            analysis_date=state.analysis_date,
            config={
                "llm_provider": self.config.deep_think_llm.provider,
                "model": self.config.deep_think_llm.model,
                "temperature": 0.7
            }
        )
        
        technical_input = AnalystInput(
            trace_id=state.trace_id,
            stock_symbol=state.stock_symbol,
            analysis_date=state.analysis_date,
            config={
                "llm_provider": self.config.deep_think_llm.provider,
                "model": self.config.deep_think_llm.model,
                "temperature": 0.7,
                "indicators": ["rsi", "macd", "bollinger_bands", "sma", "ema"]
            }
        )
        
        print(f"[{state.trace_id}] Running parallel analysts...")
        
        # 并行运行两位分析师
        fundamental_task = asyncio.create_task(
            asyncio.to_thread(self.fundamental_analyst.analyze, fundamental_input)
        )
        technical_task = asyncio.create_task(
            asyncio.to_thread(self.technical_analyst.analyze, technical_input)
        )
        
        # 等待全部完成
        results = await asyncio.gather(
            fundamental_task, technical_task,
            return_exceptions=True
        )
        
        # 处理结果
        if isinstance(results[0], Exception):
            print(f"[{state.trace_id}] Fundamental analysis failed: {results[0]}")
        else:
            fundamental_output = results[0]
            if fundamental_output.success:
                state.fundamental_report = fundamental_output.report
                print(f"[{state.trace_id}] Fundamental analysis completed")
            else:
                print(f"[{state.trace_id}] Fundamental analysis error: {fundamental_output.error}")
        
        if isinstance(results[1], Exception):
            print(f"[{state.trace_id}] Technical analysis failed: {results[1]}")
        else:
            technical_output = results[1]
            if technical_output.success:
                state.technical_report = technical_output.report
                print(f"[{state.trace_id}] Technical analysis completed")
            else:
                print(f"[{state.trace_id}] Technical analysis error: {technical_output.error}")
    
    async def _make_simple_decision(self, state: AnalysisState):
        """
        简化版决策逻辑 (Phase 1)
        
        综合基本面和技术面信号，生成最终决策
        Phase 2 将替换为完整的辩论和风险管理流程
        """
        state.update_status(AnalysisStatus.FINALIZING)
        
        reports = []
        if state.fundamental_report:
            reports.append(state.fundamental_report)
        if state.technical_report:
            reports.append(state.technical_report)
        
        if not reports:
            state.final_decision = TradeDecision(
                action=TradingAction.HOLD,
                confidence=0.0,
                reasoning="分析失败，无法生成决策",
                analyst_signals={}
            )
            return
        
        # 计算加权信号
        buy_count = sum(1 for r in reports if r.signal == TradingSignal.BUY)
        sell_count = sum(1 for r in reports if r.signal == TradingSignal.SELL)
        hold_count = len(reports) - buy_count - sell_count
        
        # 平均置信度
        avg_confidence = sum(r.confidence for r in reports) / len(reports)
        
        # 简单决策逻辑
        if buy_count > sell_count and buy_count >= hold_count:
            action = TradingAction.BUY if buy_count == len(reports) else TradingAction.BUY
        elif sell_count > buy_count and sell_count >= hold_count:
            action = TradingAction.SELL
        else:
            action = TradingAction.HOLD
        
        # 构建理由
        reasons = []
        for r in reports:
            reasons.append(f"{r.agent_type.value}: {r.signal.value} (置信度 {int(r.confidence * 100)}%)")
        
        reasoning = "基于以下分析师报告:\n" + "\n".join(reasons)
        
        # 记录各分析师信号
        analyst_signals = {
            r.agent_type.value: r.signal for r in reports
        }
        
        state.final_decision = TradeDecision(
            action=action,
            confidence=avg_confidence,
            reasoning=reasoning,
            analyst_signals=analyst_signals,
            risk_level="medium"  # Phase 1 简化处理
        )
        
        print(f"[{state.trace_id}] Final decision: {action.value} (confidence: {avg_confidence:.2f})")
    
    def generate_feishu_report(self, state: AnalysisState) -> Dict[str, Any]:
        """生成飞书报告卡片"""
        return FeishuAdapter.generate_analysis_card(state)
    
    def get_analysis_status(self, trace_id: str) -> Optional[AnalysisState]:
        """获取分析状态"""
        return self.active_analyses.get(trace_id)


# 便捷函数
async def analyze_stock(
    symbol: str,
    date: Optional[str] = None,
    config: Optional[TAOConfig] = None,
    user_id: str = "",
    chat_id: str = ""
) -> AnalysisState:
    """
    分析单只股票
    
    使用示例:
        result = await analyze_stock("NVDA", "2026-03-24")
    """
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
    print("=" * 50)
    print("TradingAgents-OpenClaw Phase 1 Test")
    print("=" * 50)
    
    # 测试分析
    result = await analyze_stock(
        symbol="NVDA",
        config=TAOConfig()
    )
    
    print("\n" + "=" * 50)
    print("Analysis Result:")
    print("=" * 50)
    print(f"Trace ID: {result.trace_id}")
    print(f"Symbol: {result.stock_symbol}")
    print(f"Status: {result.status.value}")
    
    if result.final_decision:
        print(f"\nFinal Decision: {result.final_decision.action.value}")
        print(f"Confidence: {result.final_decision.confidence:.2f}")
        print(f"Reasoning: {result.final_decision.reasoning}")
    
    if result.error_message:
        print(f"\nError: {result.error_message}")
    
    # 生成飞书报告
    orchestrator = TradingOrchestrator()
    feishu_card = orchestrator.generate_feishu_report(result)
    print("\nFeishu Card Generated Successfully!")


if __name__ == "__main__":
    asyncio.run(main())
