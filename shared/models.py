"""
TradingAgents-OpenClaw 共享数据模型
定义系统中使用的所有数据模型
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ============== 枚举类型 ==============

class AnalysisStatus(str, Enum):
    """分析状态"""
    INITIAL = "initial"
    ANALYZING = "analyzing"
    RESEARCHING = "researching"
    DEBATING = "debating"
    RISK_ASSESSING = "risk_assessing"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    FAILED = "failed"


class TradingSignal(str, Enum):
    """交易信号"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    UNKNOWN = "unknown"


class TradingAction(str, Enum):
    """交易动作"""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


class RiskLevel(str, Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


class AgentType(str, Enum):
    """Agent类型"""
    FUNDAMENTAL = "fundamental"
    SENTIMENT = "sentiment"
    TECHNICAL = "technical"
    RESEARCHER = "researcher"
    BULL_TRADER = "bull_trader"
    NEUTRAL_TRADER = "neutral_trader"
    BEAR_TRADER = "bear_trader"
    RISK_MANAGER = "risk_manager"


# ============== 基础模型 ==============

class TokenUsage(BaseModel):
    """LLM Token使用情况"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0


# ============== 分析师相关模型 ==============

class AnalystInput(BaseModel):
    """分析师 Skill 输入"""
    trace_id: str
    stock_symbol: str
    analysis_date: str
    config: Dict[str, Any] = Field(default_factory=dict)


class AnalystOutput(BaseModel):
    """分析师 Skill 输出"""
    trace_id: str
    success: bool
    report: Optional["AnalystReport"] = None
    error: Optional[str] = None
    latency_ms: int = 0
    token_usage: TokenUsage = Field(default_factory=TokenUsage)


class AnalystReport(BaseModel):
    """分析师报告"""
    agent_type: AgentType
    stock_symbol: str
    signal: TradingSignal = TradingSignal.UNKNOWN
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    reasoning: str = ""
    key_metrics: Dict[str, Any] = Field(default_factory=dict)
    risks: List[str] = Field(default_factory=list)
    raw_output: str = ""
    created_at: datetime = Field(default_factory=datetime.now)


# ============== 研究相关模型 ==============

class ResearchSummary(BaseModel):
    """研究综合报告"""
    overall_signal: TradingSignal = TradingSignal.UNKNOWN
    consensus_level: float = Field(ge=0.0, le=1.0, default=0.0)
    key_insights: List[str] = Field(default_factory=list)
    contradictions: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    reasoning: str = ""


class DebateRound(BaseModel):
    """辩论轮次"""
    round_number: int
    bull_view: str = ""
    neutral_view: str = ""
    bear_view: str = ""
    consensus_reached: bool = False


class TraderRecommendation(BaseModel):
    """交易员建议"""
    trader_type: AgentType
    action: TradingAction
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    position_size: str = "medium"  # small/medium/large
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    reasoning: str = ""


# ============== 风险相关模型 ==============

class RiskFactor(BaseModel):
    """风险因子"""
    factor_name: str
    level: RiskLevel
    description: str
    mitigation: str = ""


class RiskAssessment(BaseModel):
    """风险评估报告"""
    overall_risk: RiskLevel = RiskLevel.MEDIUM
    risk_score: float = Field(ge=0.0, le=100.0, default=50.0)
    risk_factors: List[RiskFactor] = Field(default_factory=list)
    position_size_recommendation: str = "medium"
    max_position_pct: float = 10.0  # 最大仓位百分比
    warnings: List[str] = Field(default_factory=list)


# ============== 决策相关模型 ==============

class TradeDecision(BaseModel):
    """最终交易决策"""
    action: TradingAction = TradingAction.HOLD
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    position_size: str = "medium"
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    reasoning: str = ""
    risk_level: RiskLevel = RiskLevel.MEDIUM
    timeframe: str = "medium_term"  # short_term/medium_term/long_term
    analyst_signals: Dict[str, TradingSignal] = Field(default_factory=dict)


# ============== 完整分析状态 ==============

class AnalysisState(BaseModel):
    """单次分析的完整状态"""
    
    # 基本信息
    trace_id: str
    stock_symbol: str
    analysis_date: str
    status: AnalysisStatus = AnalysisStatus.INITIAL
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # 输入配置
    user_id: Optional[str] = None  # 飞书用户ID
    chat_id: Optional[str] = None  # 飞书会话ID
    config: Dict[str, Any] = Field(default_factory=dict)
    
    # 分析师报告
    fundamental_report: Optional[AnalystReport] = None
    sentiment_report: Optional[AnalystReport] = None
    technical_report: Optional[AnalystReport] = None
    
    # 研究整合
    research_summary: Optional[ResearchSummary] = None
    
    # 交易辩论
    trader_recommendations: List[TraderRecommendation] = Field(default_factory=list)
    debate_rounds: List[DebateRound] = Field(default_factory=list)
    
    # 风险评估
    risk_assessment: Optional[RiskAssessment] = None
    
    # 最终决策
    final_decision: Optional[TradeDecision] = None
    
    # 执行结果
    error_message: Optional[str] = None
    completed_at: Optional[datetime] = None
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def update_status(self, status: AnalysisStatus):
        """
        更新状态 (带状态机验证)
        
        Raises:
            ValueError: 非法状态转换
        """
        # 状态转换验证
        valid_transitions = {
            AnalysisStatus.INITIAL: {AnalysisStatus.ANALYZING, AnalysisStatus.FAILED},
            AnalysisStatus.ANALYZING: {AnalysisStatus.RESEARCHING, AnalysisStatus.FAILED},
            AnalysisStatus.RESEARCHING: {AnalysisStatus.DEBATING, AnalysisStatus.FAILED},
            AnalysisStatus.DEBATING: {AnalysisStatus.RISK_ASSESSING, AnalysisStatus.FAILED},
            AnalysisStatus.RISK_ASSESSING: {AnalysisStatus.FINALIZING, AnalysisStatus.FAILED},
            AnalysisStatus.FINALIZING: {AnalysisStatus.COMPLETED, AnalysisStatus.FAILED},
            AnalysisStatus.COMPLETED: set(),
            AnalysisStatus.FAILED: set(),
        }
        
        allowed = valid_transitions.get(self.status, set())
        if status not in allowed:
            raise ValueError(
                f"Invalid state transition: {self.status.value} → {status.value}. "
                f"Allowed: {[s.value for s in allowed]}"
            )
        
        self.status = status
        self.updated_at = datetime.now()
    
    def get_reports_summary(self) -> Dict[str, Any]:
        """获取报告摘要"""
        return {
            "fundamental": {
                "signal": self.fundamental_report.signal if self.fundamental_report else None,
                "confidence": self.fundamental_report.confidence if self.fundamental_report else 0
            },
            "sentiment": {
                "signal": self.sentiment_report.signal if self.sentiment_report else None,
                "confidence": self.sentiment_report.confidence if self.sentiment_report else 0
            },
            "technical": {
                "signal": self.technical_report.signal if self.technical_report else None,
                "confidence": self.technical_report.confidence if self.technical_report else 0
            }
        }


# ============== 飞书交互模型 ==============

class FeishuCommand(BaseModel):
    """飞书指令"""
    command: str  # analyze, analyze_batch, history, settings
    stock_symbols: List[str] = Field(default_factory=list)
    analysis_date: Optional[str] = None
    args: Dict[str, Any] = Field(default_factory=dict)
    user_id: str = ""
    chat_id: str = ""
    message_id: str = ""


class FeishuReportCard(BaseModel):
    """飞书报告卡片"""
    stock_symbol: str
    analysis_date: str
    final_signal: TradingAction
    confidence: float
    summary: str
    sections: List[Dict[str, Any]] = Field(default_factory=list)
    actions: List[Dict[str, Any]] = Field(default_factory=list)


# ============== 配置模型 ==============

class LLMConfig(BaseModel):
    """LLM配置"""
    provider: str = "openai"  # openai, anthropic, google, xai, ollama
    model: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: int = 4000
    timeout: int = 60


class DataVendorConfig(BaseModel):
    """数据供应商配置"""
    core_stock: str = "yfinance"
    technical: str = "yfinance"
    fundamental: str = "yfinance"
    news: str = "yfinance"


class TAOConfig(BaseModel):
    """TradingAgents-OpenClaw 全局配置"""
    # LLM配置
    deep_think_llm: LLMConfig = Field(default_factory=lambda: LLMConfig(model="gpt-4o"))
    quick_think_llm: LLMConfig = Field(default_factory=lambda: LLMConfig(model="gpt-4o-mini"))
    
    # 数据供应商
    data_vendors: DataVendorConfig = Field(default_factory=DataVendorConfig)
    
    # 辩论设置
    max_debate_rounds: int = 1
    max_risk_discuss_rounds: int = 1
    
    # 性能设置
    parallel_analysts: bool = True
    request_timeout: int = 120
    
    # 缓存设置
    cache_enabled: bool = True
    cache_ttl_minutes: int = 60
    
    # 成本限制
    max_cost_per_analysis_usd: float = 1.0
    
    # 飞书配置
    feishu_webhook_url: Optional[str] = None


# 导出所有模型
__all__ = [
    # 枚举
    "AnalysisStatus",
    "TradingSignal",
    "TradingAction",
    "RiskLevel",
    "AgentType",
    
    # 基础模型
    "TokenUsage",
    
    # 分析师
    "AnalystInput",
    "AnalystOutput",
    "AnalystReport",
    
    # 研究
    "ResearchSummary",
    "DebateRound",
    "TraderRecommendation",
    
    # 风险
    "RiskFactor",
    "RiskAssessment",
    
    # 决策
    "TradeDecision",
    
    # 状态
    "AnalysisState",
    
    # 飞书
    "FeishuCommand",
    "FeishuReportCard",
    
    # 配置
    "LLMConfig",
    "DataVendorConfig",
    "TAOConfig",
]
