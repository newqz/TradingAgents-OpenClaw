"""
飞书适配器
处理飞书消息解析、报告生成和消息发送
"""

import re
from typing import Any, Dict, List, Optional
from datetime import datetime

from shared.models import (
    FeishuCommand,
    AnalysisState,
    TradingAction,
    FeishuReportCard
)


class FeishuAdapter:
    """飞书消息适配器"""
    
    # 指令正则表达式 - 支持美股、A股、港股
    COMMAND_PATTERNS = {
        # 美股: NVDA, AAPL
        # A股: 000001.SZ, 600000.SH, 000001 (纯数字默认深交所)
        # 港股: 0700.HK, 3690.HK
        "analyze": r'^[/!]分析\s+([\w.]+)(?:\s+(\d{4}-\d{2}-\d{2}))?$',
        "analyze_batch": r'^[/!]分析多股\s+([\w.,]+)$',
        "history": r'^[/!]历史\s+([\w.]+)$',
        "settings": r'^[/!]设置(?:\s+(\w+)=(\w+))?$',
        "help": r'^[/!](?:帮助|help)$'
    }
    
    @classmethod
    def parse_command(cls, text: str, user_id: str = "", chat_id: str = "", message_id: str = "") -> Optional[FeishuCommand]:
        """
        解析飞书消息文本
        
        Args:
            text: 消息文本
            user_id: 用户ID
            chat_id: 会话ID
            message_id: 消息ID
            
        Returns:
            FeishuCommand 或 None
        """
        text = text.strip()
        
        # 分析单股
        match = re.match(cls.COMMAND_PATTERNS["analyze"], text)
        if match:
            symbol = match.group(1).upper()
            date = match.group(2)
            
            return FeishuCommand(
                command="analyze",
                stock_symbols=[symbol],
                analysis_date=date,
                user_id=user_id,
                chat_id=chat_id,
                message_id=message_id
            )
        
        # 分析多股
        match = re.match(cls.COMMAND_PATTERNS["analyze_batch"], text)
        if match:
            symbols = [s.strip().upper() for s in match.group(1).split(",")]
            
            return FeishuCommand(
                command="analyze_batch",
                stock_symbols=symbols,
                user_id=user_id,
                chat_id=chat_id,
                message_id=message_id
            )
        
        # 历史记录
        match = re.match(cls.COMMAND_PATTERNS["history"], text)
        if match:
            symbol = match.group(1).upper()
            
            return FeishuCommand(
                command="history",
                stock_symbols=[symbol],
                user_id=user_id,
                chat_id=chat_id,
                message_id=message_id
            )
        
        # 设置
        match = re.match(cls.COMMAND_PATTERNS["settings"], text)
        if match:
            key = match.group(1)
            value = match.group(2)
            args = {key: value} if key and value else {}
            
            return FeishuCommand(
                command="settings",
                args=args,
                user_id=user_id,
                chat_id=chat_id,
                message_id=message_id
            )
        
        # 帮助
        match = re.match(cls.COMMAND_PATTERNS["help"], text)
        if match:
            return FeishuCommand(
                command="help",
                user_id=user_id,
                chat_id=chat_id,
                message_id=message_id
            )
        
        return None
    
    @classmethod
    def generate_help_message(cls) -> str:
        """生成帮助消息"""
        return """🚀 **TradingAgents-OpenClaw 使用指南**

📊 **分析指令**
• `/分析 {股票代码}` - 分析单只股票
  例: `/分析 NVDA` (美股)
  例: `/分析 000001.SZ` (A股)
  例: `/分析 0700.HK` (港股)
• `/分析 {股票代码} {日期}` - 指定日期分析
  例: `/分析 AAPL 2025-12-01`
• `/分析多股 {代码1},{代码2}` - 批量分析
  例: `/分析多股 NVDA,AAPL,TSLA`

📈 **查询指令**
• `/历史 {股票代码}` - 查看历史分析
  例: `/历史 NVDA`

⚙️ **设置指令**
• `/设置` - 查看当前配置
• `/设置 {参数名}={值}` - 修改配置
  例: `/设置 llm_provider=anthropic`

💡 **支持的市场**
• **美股**: NVDA, AAPL, TSLA (字母代码)
• **A股**: 000001.SZ, 600000.SH (深交所/上交所)
• **港股**: 0700.HK, 3690.HK (香港交易所)

⚠️ **提示**
• 分析需要 30-60 秒，请耐心等待
• 分析结果仅供参考，不构成投资建议
"""
    
    @classmethod
    def generate_analysis_card(cls, state: AnalysisState) -> Dict[str, Any]:
        """
        生成飞书分析报告卡片
        
        Args:
            state: 分析状态
            
        Returns:
            飞书卡片 JSON
        """
        if not state.final_decision:
            return cls._generate_error_card("分析未完成或失败")
        
        decision = state.final_decision
        
        # 信号图标映射
        signal_icons = {
            TradingAction.STRONG_BUY: "🚀 强烈买入",
            TradingAction.BUY: "📈 买入",
            TradingAction.HOLD: "➖ 观望",
            TradingAction.SELL: "📉 卖出",
            TradingAction.STRONG_SELL: "🔻 强烈卖出"
        }
        
        signal_text = signal_icons.get(decision.action, "❓ 未知")
        confidence_stars = "⭐" * int(decision.confidence * 5)
        
        # 分析师信号
        analyst_signals = []
        for agent_type, signal in decision.analyst_signals.items():
            icon = "🟢" if signal.value == "buy" else "🔴" if signal.value == "sell" else "⚪"
            analyst_signals.append(f"{icon} {agent_type}: {signal.value.upper()}")
        
        # 构建卡片
        card = {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {
                    "content": f"📊 {state.stock_symbol} 分析报告",
                    "tag": "plain_text"
                },
                "sub_title": {
                    "content": f"分析日期: {state.analysis_date}",
                    "tag": "plain_text"
                },
                "template": "blue"
            },
            "elements": [
                # 最终建议
                {
                    "tag": "div",
                    "text": {
                        "content": f"**最终建议**: {signal_text}\n**置信度**: {confidence_stars} ({int(decision.confidence * 100)}%)",
                        "tag": "lark_md"
                    }
                },
                {"tag": "hr"},
                
                # 分析师信号汇总
                {
                    "tag": "div",
                    "text": {
                        "content": "**分析师信号**:\n" + "\n".join(analyst_signals),
                        "tag": "lark_md"
                    }
                },
                {"tag": "hr"},
                
                # 各分析师详细报告
                cls._generate_analyst_section(state),
                
                # 决策理由
                {
                    "tag": "div",
                    "text": {
                        "content": f"**决策理由**:\n{decision.reasoning}",
                        "tag": "lark_md"
                    }
                },
                {"tag": "hr"},
                
                # 风险等级
                {
                    "tag": "div",
                    "text": {
                        "content": f"**风险等级**: {decision.risk_level.value.upper()}",
                        "tag": "lark_md"
                    }
                },
                {"tag": "hr"},
                
                # 免责声明
                {
                    "tag": "note",
                    "elements": [
                        {
                            "tag": "plain_text",
                            "content": "⚠️ 免责声明：本分析仅供参考，不构成投资建议。投资有风险，入市需谨慎。"
                        }
                    ]
                }
            ]
        }
        
        # 添加操作按钮
        card["elements"].append({
            "tag": "action",
            "actions": [
                {
                    "tag": "button",
                    "text": {"tag": "plain_text", "content": "🔄 重新分析"},
                    "type": "primary",
                    "value": {"action": "reanalyze", "symbol": state.stock_symbol}
                },
                {
                    "tag": "button",
                    "text": {"tag": "plain_text", "content": "📈 查看历史"},
                    "value": {"action": "history", "symbol": state.stock_symbol}
                }
            ]
        })
        
        return card
    
    @classmethod
    def _generate_analyst_section(cls, state: AnalysisState) -> Dict[str, Any]:
        """生成分析师报告部分"""
        sections = []
        
        # 基本面
        if state.fundamental_report:
            report = state.fundamental_report
            signal_emoji = "🟢" if report.signal.value == "buy" else "🔴" if report.signal.value == "sell" else "⚪"
            sections.append(f"**基本面**: {signal_emoji} {report.signal.value.upper()} (置信度: {int(report.confidence * 100)}%)")
        
        # 技术面
        if state.technical_report:
            report = state.technical_report
            signal_emoji = "🟢" if report.signal.value == "buy" else "🔴" if report.signal.value == "sell" else "⚪"
            sections.append(f"**技术面**: {signal_emoji} {report.signal.value.upper()} (置信度: {int(report.confidence * 100)}%)")
        
        # 情绪面
        if state.sentiment_report:
            report = state.sentiment_report
            signal_emoji = "🟢" if report.signal.value == "buy" else "🔴" if report.signal.value == "sell" else "⚪"
            sections.append(f"**情绪面**: {signal_emoji} {report.signal.value.upper()} (置信度: {int(report.confidence * 100)}%)")
        
        return {
            "tag": "div",
            "text": {
                "content": "**详细分析**:\n" + "\n".join(sections),
                "tag": "lark_md"
            }
        }
    
    @classmethod
    def _generate_error_card(cls, error_message: str) -> Dict[str, Any]:
        """生成错误卡片"""
        return {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"content": "❌ 分析失败", "tag": "plain_text"},
                "template": "red"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "content": f"**错误信息**: {error_message}",
                        "tag": "lark_md"
                    }
                },
                {
                    "tag": "note",
                    "elements": [
                        {
                            "tag": "plain_text",
                            "content": "请检查股票代码是否正确，或稍后重试。"
                        }
                    ]
                }
            ]
        }
    
    @classmethod
    def generate_loading_message(cls, symbol: str) -> str:
        """生成加载中消息"""
        return f"⏳ 正在分析 **{symbol}**，请稍候...\n\n分析流程：基本面 → 技术面 → 风险评估 → 最终决策\n预计耗时 30-60 秒"
    
    @classmethod
    def generate_simple_text_report(cls, state: AnalysisState) -> str:
        """生成纯文本报告（用于超长内容）"""
        if not state.final_decision:
            return "分析失败"
        
        decision = state.final_decision
        
        lines = [
            f"📊 {state.stock_symbol} 分析报告",
            f"分析日期: {state.analysis_date}",
            "",
            f"最终建议: {decision.action.value.upper()}",
            f"置信度: {int(decision.confidence * 100)}%",
            "",
            "决策理由:",
            decision.reasoning[:500] + "..." if len(decision.reasoning) > 500 else decision.reasoning,
            "",
            "⚠️ 免责声明：本分析仅供参考，不构成投资建议。"
        ]
        
        return "\n".join(lines)


# 便捷函数
def parse_feishu_message(
    text: str,
    user_id: str = "",
    chat_id: str = "",
    message_id: str = ""
) -> Optional[FeishuCommand]:
    """解析飞书消息"""
    return FeishuAdapter.parse_command(text, user_id, chat_id, message_id)


def generate_feishu_report(state: AnalysisState) -> Dict[str, Any]:
    """生成飞书报告"""
    return FeishuAdapter.generate_analysis_card(state)
