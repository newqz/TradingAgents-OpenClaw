# -*- coding: utf-8 -*-
"""
共享接口定义
抽象基类定义，确保系统架构一致性
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from .models import (
    AnalystInput, AnalystOutput, 
    ResearchSummary, RiskAssessment,
    TraderRecommendation, TradingAction,
    TradeDecision, TradingSignal
)


class BaseAnalyst(ABC):
    """
    分析师抽象基类
    
    所有分析师 (基本面/技术面/情绪面) 应继承此基类
    """
    
    @abstractmethod
    def analyze(self, input_data: AnalystInput) -> AnalystOutput:
        """
        执行分析
        
        Args:
            input_data: 分析输入
            
        Returns:
            AnalystOutput: 分析结果
        """
        pass
    
    @abstractmethod
    def get_agent_type(self) -> str:
        """获取分析师类型"""
        pass
    
    @property
    @abstractmethod
    def config(self) -> Dict[str, Any]:
        """获取配置"""
        pass


class BaseResearcher(ABC):
    """
    研究员抽象基类
    
    所有研究员 (Bull/Bear) 应继承此基类
    """
    
    @abstractmethod
    def conduct_research(self, symbol: str, analyst_reports: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行研究
        
        Args:
            symbol: 股票代码
            analyst_reports: 分析师报告
            
        Returns:
            研究结果字典
        """
        pass
    
    @abstractmethod
    def get_agent_type(self) -> str:
        """获取研究员类型"""
        pass


class BaseTrader(ABC):
    """
    交易员抽象基类
    
    所有交易员 (Bull/Neutral/Bear) 应继承此基类
    """
    
    @abstractmethod
    def make_recommendation(self, symbol: str, research: ResearchSummary) -> TraderRecommendation:
        """
        生成交易建议
        
        Args:
            symbol: 股票代码
            research: 研究摘要
            
        Returns:
            交易员建议
        """
        pass
    
    @abstractmethod
    def get_agent_type(self) -> str:
        """获取交易员类型"""
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        pass


class BaseRiskManager(ABC):
    """
    风险管理器抽象基类
    """
    
    @abstractmethod
    def assess_risk(
        self,
        symbol: str,
        trade_recommendation: TraderRecommendation,
        research_summary: ResearchSummary
    ) -> RiskAssessment:
        """
        评估风险
        
        Args:
            symbol: 股票代码
            trade_recommendation: 交易建议
            research_summary: 研究摘要
            
        Returns:
            风险评估
        """
        pass


class BaseDataProvider(ABC):
    """
    数据提供器抽象基类
    
    所有数据提供器 (YFinance/AlphaVantage/Finnhub/TuShare) 应继承此基类
    """
    
    @abstractmethod
    def get_stock_price(self, symbol: str) -> Dict[str, Any]:
        """获取股票价格"""
        pass
    
    @abstractmethod
    def get_company_info(self, symbol: str) -> Dict[str, Any]:
        """获取公司信息"""
        pass
    
    @abstractmethod
    def get_financial_data(self, symbol: str) -> Dict[str, Any]:
        """获取财务数据"""
        pass
    
    @abstractmethod
    def get_market_news(self, symbol: str) -> list:
        """获取市场新闻"""
        pass


# 接口验证函数
def validate_analyst(analyst: BaseAnalyst) -> bool:
    """验证分析师实现完整性"""
    required_methods = ['analyze', 'get_agent_type']
    for method in required_methods:
        if not hasattr(analyst, method):
            return False
        if not callable(getattr(analyst, method)):
            return False
    return True


def validate_trader(trader: BaseTrader) -> bool:
    """验证交易员实现完整性"""
    required_methods = ['make_recommendation', 'get_agent_type', 'get_system_prompt']
    for method in required_methods:
        if not hasattr(trader, method):
            return False
        if not callable(getattr(trader, method)):
            return False
    return True
