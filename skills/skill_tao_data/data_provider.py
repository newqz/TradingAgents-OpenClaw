"""
TradingAgents-OpenClaw 数据提供器
统一的数据获取接口，支持多供应商自动故障转移
支持美股、A股、港股
"""

import os
import json
import hashlib
import re
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from functools import wraps

# 数据源分类定义
TOOLS_CATEGORIES = {
    "core_stock": {
        "description": "OHLCV股票价格数据",
        "tools": ["get_stock_data"]
    },
    "technical": {
        "description": "技术分析指标",
        "tools": ["get_indicators"]
    },
    "fundamental": {
        "description": "公司基本面数据",
        "tools": [
            "get_fundamentals",
            "get_balance_sheet",
            "get_cashflow",
            "get_income_statement"
        ]
    },
    "news": {
        "description": "新闻和内部人数据",
        "tools": ["get_news", "get_global_news", "get_insider_transactions"]
    }
}

# 供应商列表
VENDOR_LIST = ["yfinance", "alpha_vantage", "finnhub", "tushare", "china_stock"]


class CacheManager:
    """简单的内存缓存管理器，生产环境可替换为 Redis"""
    
    def __init__(self, enabled: bool = True, ttl_minutes: int = 60):
        self.enabled = enabled
        self.ttl = timedelta(minutes=ttl_minutes)
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    def _make_key(self, method: str, *args, **kwargs) -> str:
        """生成缓存键"""
        key_data = f"{method}:{args}:{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, method: str, *args, **kwargs) -> Optional[Any]:
        """获取缓存数据"""
        if not self.enabled:
            return None
        
        key = self._make_key(method, *args, **kwargs)
        cached = self._cache.get(key)
        
        if cached:
            if datetime.now() - cached["timestamp"] < self.ttl:
                return cached["data"]
            else:
                # 过期清理
                del self._cache[key]
        
        return None
    
    def set(self, method: str, data: Any, *args, **kwargs):
        """设置缓存数据"""
        if not self.enabled:
            return
        
        key = self._make_key(method, *args, **kwargs)
        self._cache[key] = {
            "data": data,
            "timestamp": datetime.now()
        }
    
    def clear(self):
        """清空缓存"""
        self._cache.clear()


class SymbolClassifier:
    """股票代码分类器"""
    
    @staticmethod
    def classify(symbol: str) -> str:
        """
        分类股票代码类型
        
        Returns:
            "us_stock" - 美股 (AAPL, NVDA, TSLA)
            "a_stock" - A股 (000001.SZ, 600000.SH)
            "hk_stock" - 港股 (0700.HK, 3690.HK)
            "unknown" - 未知
        """
        symbol = symbol.upper().strip()
        
        # A股格式: 000001.SZ, 600000.SH, 300001.SZ
        if re.match(r'^\d{6}\.(SZ|SH|SS)$', symbol):
            return "a_stock"
        
        # 港股格式: 0700.HK, 3690.HK
        if re.match(r'^\d{4,5}\.HK$', symbol):
            return "hk_stock"
        
        # 纯6位数字，可能是A股
        if re.match(r'^\d{6}$', symbol):
            return "a_stock"
        
        # 美股格式: AAPL, NVDA, TSLA (字母开头，无后缀)
        if re.match(r'^[A-Z]{1,5}$', symbol):
            return "us_stock"
        
        return "unknown"
    
    @staticmethod
    def get_recommended_vendor(symbol: str) -> str:
        """获取推荐的数据供应商"""
        stock_type = SymbolClassifier.classify(symbol)
        
        vendor_map = {
            "us_stock": "yfinance",
            "a_stock": "china_stock",
            "hk_stock": "china_stock"
        }
        
        return vendor_map.get(stock_type, "yfinance")


class DataProvider:
    """
    统一数据提供器
    
    支持多供应商自动故障转移，内置缓存机制
    支持美股、A股、港股
    """
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        cache_enabled: bool = True
    ):
        self.config = config or {}
        self.cache = CacheManager(enabled=cache_enabled)
        self._vendors = {}
        self._init_vendors()
    
    def _init_vendors(self):
        """初始化所有供应商客户端"""
        import importlib.util
        
        # 获取 vendors 目录路径
        vendors_dir = os.path.join(os.path.dirname(__file__), "vendors")
        
        def _load_vendor(module_name: str):
            """动态加载供应商模块"""
            module_path = os.path.join(vendors_dir, f"{module_name}.py")
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return module
            return None
        
        # 加载供应商
        yfinance_mod = _load_vendor("yfinance_client")
        alpha_vantage_mod = _load_vendor("alpha_vantage_client")
        china_stock_mod = _load_vendor("china_stock_client")
        finnhub_mod = _load_vendor("finnhub_client")
        tushare_mod = _load_vendor("tushare_client")
        
        # 初始化供应商客户端
        self._vendors = {
            "yfinance": yfinance_mod.YFinanceClient() if yfinance_mod else None,
            "alpha_vantage": alpha_vantage_mod.AlphaVantageClient(
                api_key=self.config.get("alpha_vantage_api_key") or 
                         os.getenv("ALPHA_VANTAGE_API_KEY")
            ) if alpha_vantage_mod else None,
            "finnhub": finnhub_mod.FinnhubClient(
                api_key=self.config.get("finnhub_api_key") or
                        os.getenv("FINNHUB_API_KEY")
            ) if finnhub_mod else None,
            "tushare": tushare_mod.TuShareClient(
                token=self.config.get("tushare_token") or
                       os.getenv("TUSHARE_TOKEN")
            ) if tushare_mod else None,
            "china_stock": china_stock_mod.ChinaStockClient() if china_stock_mod else None,
        }
        
        # 保存供应商模块引用用于方法映射
        self._vendor_modules = {
            "yfinance": yfinance_mod,
            "alpha_vantage": alpha_vantage_mod,
            "finnhub": finnhub_mod,
            "tushare": tushare_mod,
            "china_stock": china_stock_mod,
        }
        
        # 供应商方法映射 (动态构建)
        self._vendor_methods = self._build_vendor_methods()
    
    def _build_vendor_methods(self) -> Dict[str, Dict[str, Any]]:
        """构建供应商方法映射"""
        # 从已加载的模块获取类
        def _get_vendor_class(vendor_name: str):
            """从模块获取供应商类"""
            mod = self._vendor_modules.get(vendor_name)
            if not mod:
                return None
            class_name = "".join([part.capitalize() for part in vendor_name.split("_")])
            return getattr(mod, class_name, None)
        
        # 使用已加载的模块
        YFinanceClient = _get_vendor_class("yfinance")
        AlphaVantageClient = _get_vendor_class("alpha_vantage")
        ChinaStockClient = _get_vendor_class("china_stock")
        FinnhubClient = _get_vendor_class("finnhub")
        TuShareClient = _get_vendor_class("tushare")
        
        return {
            # core_stock_apis
            "get_stock_data": {
                "yfinance": YFinanceClient.get_stock_data if YFinanceClient else None,
                "alpha_vantage": AlphaVantageClient.get_stock_data if AlphaVantageClient else None,
                "finnhub": FinnhubClient.get_stock_data if FinnhubClient else None,
                "tushare": TuShareClient.get_stock_data if TuShareClient else None,
                "china_stock": ChinaStockClient.get_stock_data if ChinaStockClient else None,
            },
            # technical_indicators
            "get_indicators": {
                "yfinance": YFinanceClient.get_indicators if YFinanceClient else None,
                "alpha_vantage": AlphaVantageClient.get_indicators if AlphaVantageClient else None,
                "finnhub": FinnhubClient.get_indicators if FinnhubClient else None,
                "tushare": TuShareClient.get_indicators if TuShareClient else None,
                "china_stock": ChinaStockClient.get_indicators if ChinaStockClient else None,
            },
            # fundamental_data
            "get_fundamentals": {
                "yfinance": YFinanceClient.get_fundamentals if YFinanceClient else None,
                "alpha_vantage": AlphaVantageClient.get_fundamentals if AlphaVantageClient else None,
                "finnhub": FinnhubClient.get_fundamentals if FinnhubClient else None,
                "tushare": TuShareClient.get_fundamentals if TuShareClient else None,
                "china_stock": ChinaStockClient.get_fundamentals if ChinaStockClient else None,
            },
            "get_balance_sheet": {
                "yfinance": YFinanceClient.get_balance_sheet if YFinanceClient else None,
                "alpha_vantage": AlphaVantageClient.get_balance_sheet if AlphaVantageClient else None,
                "finnhub": FinnhubClient.get_balance_sheet if FinnhubClient else None,
                "tushare": TuShareClient.get_balance_sheet if TuShareClient else None,
                "china_stock": ChinaStockClient.get_balance_sheet if ChinaStockClient else None,
            },
            "get_cashflow": {
                "yfinance": YFinanceClient.get_cashflow if YFinanceClient else None,
                "alpha_vantage": AlphaVantageClient.get_cashflow if AlphaVantageClient else None,
                "finnhub": FinnhubClient.get_cashflow if FinnhubClient else None,
                "tushare": TuShareClient.get_cashflow if TuShareClient else None,
                "china_stock": ChinaStockClient.get_cashflow if ChinaStockClient else None,
            },
            "get_income_statement": {
                "yfinance": YFinanceClient.get_income_statement if YFinanceClient else None,
                "alpha_vantage": AlphaVantageClient.get_income_statement if AlphaVantageClient else None,
                "finnhub": FinnhubClient.get_income_statement if FinnhubClient else None,
                "tushare": TuShareClient.get_income_statement if TuShareClient else None,
                "china_stock": ChinaStockClient.get_income_statement if ChinaStockClient else None,
            },
            # news_data
            "get_news": {
                "yfinance": YFinanceClient.get_news if YFinanceClient else None,
                "alpha_vantage": AlphaVantageClient.get_news if AlphaVantageClient else None,
                "finnhub": FinnhubClient.get_news if FinnhubClient else None,
                "tushare": TuShareClient.get_news if TuShareClient else None,
                "china_stock": ChinaStockClient.get_news if ChinaStockClient else None,
            },
            "get_global_news": {
                "yfinance": YFinanceClient.get_global_news if YFinanceClient else None,
                "alpha_vantage": AlphaVantageClient.get_global_news if AlphaVantageClient else None,
                "finnhub": FinnhubClient.get_global_news if FinnhubClient else None,
                "tushare": TuShareClient.get_global_news if TuShareClient else None,
                "china_stock": ChinaStockClient.get_global_news if ChinaStockClient else None,
            },
            "get_insider_transactions": {
                "yfinance": YFinanceClient.get_insider_transactions if YFinanceClient else None,
                "alpha_vantage": AlphaVantageClient.get_insider_transactions if AlphaVantageClient else None,
                "finnhub": FinnhubClient.get_insider_transactions if FinnhubClient else None,
                "tushare": TuShareClient.get_insider_transactions if TuShareClient else None,
                "china_stock": ChinaStockClient.get_insider_transactions if ChinaStockClient else None,
            },
        }
    
    def _get_vendor_for_method(self, method: str, symbol: str = "") -> List[str]:
        """获取方法对应的供应商配置（带故障转移）"""
        # 根据股票代码类型选择首选供应商
        if symbol:
            recommended = SymbolClassifier.get_recommended_vendor(symbol)
            fallback_order = [recommended] + [v for v in VENDOR_LIST if v != recommended]
        else:
            # 获取配置中的供应商
            category = self._get_category_for_method(method)
            vendor_config = self.config.get("data_vendors", {}).get(category, "yfinance")
            primary_vendors = [v.strip() for v in vendor_config.split(",")]
            fallback_order = primary_vendors + [v for v in VENDOR_LIST if v not in primary_vendors]
        
        return fallback_order
    
    def _get_category_for_method(self, method: str) -> str:
        """获取方法所属分类"""
        for category, info in TOOLS_CATEGORIES.items():
            if method in info["tools"]:
                return category
        return "core_stock"
    
    def _route_to_vendor(self, method: str, symbol: str = "", *args, **kwargs) -> Any:
        """
        将方法调用路由到适当的供应商，支持自动故障转移
        """
        # 先检查缓存
        cached = self.cache.get(method, symbol, *args, **kwargs)
        if cached is not None:
            return cached
        
        # 获取供应商链
        vendor_chain = self._get_vendor_for_method(method, symbol)
        
        last_error = None
        
        for vendor_name in vendor_chain:
            if vendor_name not in self._vendors:
                continue
            
            vendor = self._vendors[vendor_name]
            
            try:
                # 调用供应商方法
                if hasattr(vendor, method):
                    method_func = getattr(vendor, method)
                    result = method_func(*args, **kwargs)
                    
                    # 缓存结果
                    self.cache.set(method, result, symbol, *args, **kwargs)
                    
                    return result
                else:
                    continue
                    
            except Exception as e:
                # 记录错误，尝试下一个供应商
                last_error = e
                print(f"Vendor {vendor_name} failed for {method}: {e}")
                continue
        
        # 所有供应商都失败
        raise RuntimeError(
            f"All vendors failed for method '{method}' with symbol '{symbol}'. "
            f"Last error: {last_error}"
        )
    
    # ============ 公共接口 ============
    
    def get_stock_data(
        self,
        symbol: str,
        period: str = "1y",
        interval: str = "1d",
        start: Optional[str] = None,
        end: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取股票历史价格数据
        
        支持:
        - 美股: AAPL, NVDA, TSLA
        - A股: 000001.SZ, 600000.SH
        - 港股: 0700.HK, 3690.HK
        
        Args:
            symbol: 股票代码
            period: 时间周期
            interval: 数据间隔
            start: 开始日期
            end: 结束日期
        
        Returns:
            股票数据字典
        """
        return self._route_to_vendor(
            "get_stock_data",
            symbol,
            symbol=symbol,
            period=period,
            interval=interval,
            start=start,
            end=end
        )
    
    def get_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """
        获取公司基本面数据
        
        Args:
            symbol: 股票代码
        
        Returns:
            基本面数据字典
        """
        return self._route_to_vendor("get_fundamentals", symbol, symbol=symbol)
    
    def get_balance_sheet(
        self,
        symbol: str,
        freq: str = "quarterly"
    ) -> Dict[str, Any]:
        """获取资产负债表"""
        return self._route_to_vendor(
            "get_balance_sheet",
            symbol,
            symbol=symbol,
            freq=freq
        )
    
    def get_income_statement(
        self,
        symbol: str,
        freq: str = "quarterly"
    ) -> Dict[str, Any]:
        """获取利润表"""
        return self._route_to_vendor(
            "get_income_statement",
            symbol,
            symbol=symbol,
            freq=freq
        )
    
    def get_cashflow(
        self,
        symbol: str,
        freq: str = "quarterly"
    ) -> Dict[str, Any]:
        """获取现金流量表"""
        return self._route_to_vendor(
            "get_cashflow",
            symbol,
            symbol=symbol,
            freq=freq
        )
    
    def get_indicators(
        self,
        symbol: str,
        indicators: List[str],
        period: str = "6mo",
        **kwargs
    ) -> Dict[str, Any]:
        """
        获取技术指标
        
        Args:
            symbol: 股票代码
            indicators: 指标列表
            period: 计算周期
        
        Returns:
            技术指标数据
        """
        return self._route_to_vendor(
            "get_indicators",
            symbol,
            symbol=symbol,
            indicators=indicators,
            period=period,
            **kwargs
        )
    
    def get_news(
        self,
        symbol: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """获取新闻数据"""
        return self._route_to_vendor(
            "get_news",
            symbol,
            symbol=symbol,
            limit=limit
        )
    
    def get_global_news(self, limit: int = 20) -> Dict[str, Any]:
        """获取全球财经新闻"""
        return self._route_to_vendor("get_global_news", "", limit=limit)
    
    def get_insider_transactions(self, symbol: str) -> Dict[str, Any]:
        """获取内部人交易数据"""
        return self._route_to_vendor(
            "get_insider_transactions",
            symbol,
            symbol=symbol
        )
    
    def classify_symbol(self, symbol: str) -> str:
        """
        识别股票代码类型
        
        Returns:
            "us_stock" | "a_stock" | "hk_stock" | "unknown"
        """
        return SymbolClassifier.classify(symbol)
    
    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()


# 便捷函数
def get_data_provider(config: Optional[Dict] = None) -> DataProvider:
    """获取数据提供器实例"""
    return DataProvider(config=config)
