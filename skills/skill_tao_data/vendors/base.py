"""
Base Vendor Class
所有数据供应商客户端的基类
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseVendor(ABC):
    """
    数据供应商基类
    
    所有具体供应商客户端应继承此类并实现相应方法
    """
    
    @abstractmethod
    def get_stock_data(
        self,
        symbol: str,
        period: str = "1y",
        interval: str = "1d",
        start: Optional[str] = None,
        end: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        获取股票历史价格数据
        
        Args:
            symbol: 股票代码
            period: 时间周期
            interval: 数据间隔
            start: 开始日期
            end: 结束日期
        
        Returns:
            包含 OHLCV 数据的字典
        """
        pass
    
    @abstractmethod
    def get_indicators(
        self,
        symbol: str,
        indicators: List[str] = None,
        period: str = "6mo",
        **kwargs
    ) -> Dict[str, Any]:
        """
        获取技术指标
        
        Args:
            symbol: 股票代码
            indicators: 指标列表 (如 RSI, MACD, BB)
            period: 计算周期
        
        Returns:
            技术指标数据
        """
        pass
    
    @abstractmethod
    def get_fundamentals(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """
        获取公司基本面数据
        
        Args:
            symbol: 股票代码
        
        Returns:
            基本面数据
        """
        pass
    
    @abstractmethod
    def get_balance_sheet(
        self,
        symbol: str,
        freq: str = "quarterly",
        **kwargs
    ) -> Dict[str, Any]:
        """获取资产负债表"""
        pass
    
    @abstractmethod
    def get_income_statement(
        self,
        symbol: str,
        freq: str = "quarterly",
        **kwargs
    ) -> Dict[str, Any]:
        """获取利润表"""
        pass
    
    @abstractmethod
    def get_cashflow(
        self,
        symbol: str,
        freq: str = "quarterly",
        **kwargs
    ) -> Dict[str, Any]:
        """获取现金流量表"""
        pass
    
    @abstractmethod
    def get_news(self, symbol: str, limit: int = 10, **kwargs) -> Dict[str, Any]:
        """
        获取新闻数据
        
        Args:
            symbol: 股票代码
            limit: 返回数量
        
        Returns:
            新闻数据列表
        """
        pass
    
    @abstractmethod
    def get_global_news(self, limit: int = 20, **kwargs) -> Dict[str, Any]:
        """获取全球财经新闻"""
        pass
    
    @abstractmethod
    def get_insider_transactions(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """获取内部人交易数据"""
        pass
