"""
skill-tao-data: TradingAgents-OpenClaw 数据层

提供统一的股票数据获取接口，支持多供应商自动故障转移。

使用示例:
    from skill_tao_data import DataProvider, get_data_provider
    
    # 方法1: 直接实例化
    provider = DataProvider()
    data = provider.get_stock_data("AAPL")
    
    # 方法2: 使用工厂函数
    provider = get_data_provider()
    fundamentals = provider.get_fundamentals("TSLA")
"""

from .data_provider import DataProvider, get_data_provider, TOOLS_CATEGORIES

__version__ = "0.1.0"
__all__ = [
    "DataProvider",
    "get_data_provider",
    "TOOLS_CATEGORIES",
]
