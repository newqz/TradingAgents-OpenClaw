"""
Finnhub Data Client
提供美股数据，支持新闻、基本面、技术指标
官网: https://finnhub.io/
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests

# 添加 vendors 目录到 path
_vendors_dir = os.path.dirname(os.path.abspath(__file__))
if _vendors_dir not in sys.path:
    sys.path.insert(0, _vendors_dir)

from base import BaseVendor


class FinnhubClient(BaseVendor):
    """Finnhub 数据客户端"""
    
    BASE_URL = "https://finnhub.io/api/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化 Finnhub 客户端
        
        Args:
            api_key: Finnhub API key (免费注册: https://finnhub.io/)
                   也可通过 FINNHUB_API_KEY 环境变量设置
        """
        self.api_key = api_key or os.getenv("FINNHUB_API_KEY")
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict[str, Any]:
        """发起 API 请求"""
        if not self.api_key:
            raise ValueError(
                "Finnhub API key required. "
                "Set FINNHUB_API_KEY environment variable or pass api_key parameter."
            )
        
        params = params or {}
        params["token"] = self.api_key
        
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Finnhub API error: {e}")
    
    def get_stock_data(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """
        获取股票报价
        
        Finnhub 提供实时报价，使用 candle endpoint
        """
        # 转换 symbol 格式 (AAPL -> AAPL US)
        exchange_symbol = f"{symbol.upper()} US"
        
        # 获取最近交易日的数据
        to_time = int(datetime.now().timestamp())
        from_time = int((datetime.now() - timedelta(days=7)).timestamp())
        
        data = self._make_request("scan/candle", {
            "symbol": exchange_symbol,
            "resolution": "D",
            "from": from_time,
            "to": to_time
        })
        
        if data.get("s") == "no_data":
            return {
                "symbol": symbol,
                "error": "No data available",
                "source": "finnhub"
            }
        
        # 解析 OHLCV
        closes = data.get("c", [])
        highs = data.get("h", [])
        lows = data.get("l", [])
        opens = data.get("o", [])
        volumes = data.get("v", [])
        timestamps = data.get("t", [])
        
        ohlcv = []
        for i in range(len(closes)):
            if closes[i]:
                ohlcv.append({
                    "date": datetime.fromtimestamp(timestamps[i]).strftime("%Y-%m-%d"),
                    "open": opens[i] if i < len(opens) else None,
                    "high": highs[i] if i < len(highs) else None,
                    "low": lows[i] if i < len(lows) else None,
                    "close": closes[i],
                    "volume": volumes[i] if i < len(volumes) else None
                })
        
        return {
            "symbol": symbol,
            "data": ohlcv,
            "source": "finnhub"
        }
    
    def get_indicators(self, symbol: str, indicators: List[str] = None, **kwargs) -> Dict[str, Any]:
        """
        获取技术指标
        """
        exchange_symbol = f"{symbol.upper()} US"
        indicators = indicators or ["RSI", "MACD", "BB"]
        
        result = {}
        
        # RSI
        if "RSI" in indicators:
            try:
                rsi_data = self._make_request("scan/RSI", {
                    "symbol": exchange_symbol
                })
                result["RSI"] = rsi_data
            except Exception:
                result["RSI"] = {"error": "RSI calculation failed"}
        
        # MACD
        if "MACD" in indicators:
            try:
                macd_data = self._make_request("scan/MACD", {
                    "symbol": exchange_symbol
                })
                result["MACD"] = macd_data
            except Exception:
                result["MACD"] = {"error": "MACD calculation failed"}
        
        # Bollinger Bands
        if "BB" in indicators:
            try:
                bb_data = self._make_request("scan/BB", {
                    "symbol": exchange_symbol
                })
                result["BB"] = bb_data
            except Exception:
                result["BB"] = {"error": "BB calculation failed"}
        
        return {
            "symbol": symbol,
            "indicators": result,
            "source": "finnhub"
        }
    
    def get_fundamentals(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """
        获取公司基本信息
        """
        exchange_symbol = f"{symbol.upper()} US"
        
        # 获取公司基本信息
        profile = self._make_request("stock/profile2", {
            "symbol": exchange_symbol
        })
        
        # 获取关键指标
        metrics = self._make_request("stock/metric", {
            "symbol": exchange_symbol,
            "metric": "all"
        })
        
        return {
            "symbol": symbol,
            "profile": profile,
            "metrics": metrics.get("metric", {}),
            "source": "finnhub"
        }
    
    def get_balance_sheet(self, symbol: str, freq: str = "annual", **kwargs) -> Dict[str, Any]:
        """获取资产负债表"""
        exchange_symbol = f"{symbol.upper()} US"
        
        data = self._make_request("stock/financials", {
            "symbol": exchange_symbol,
            "freq": freq,
            "statement": "balance"
        })
        
        return {
            "symbol": symbol,
            "balance_sheet": data,
            "source": "finnhub"
        }
    
    def get_income_statement(self, symbol: str, freq: str = "annual", **kwargs) -> Dict[str, Any]:
        """获取利润表"""
        exchange_symbol = f"{symbol.upper()} US"
        
        data = self._make_request("stock/financials", {
            "symbol": exchange_symbol,
            "freq": freq,
            "statement": "ic"
        })
        
        return {
            "symbol": symbol,
            "income_statement": data,
            "source": "finnhub"
        }
    
    def get_cashflow(self, symbol: str, freq: str = "annual", **kwargs) -> Dict[str, Any]:
        """获取现金流量表"""
        exchange_symbol = f"{symbol.upper()} US"
        
        data = self._make_request("stock/financials", {
            "symbol": exchange_symbol,
            "freq": freq,
            "statement": "cf"
        })
        
        return {
            "symbol": symbol,
            "cashflow": data,
            "source": "finnhub"
        }
    
    def get_news(self, symbol: str, limit: int = 10, **kwargs) -> Dict[str, Any]:
        """
        获取新闻（按股票代码）
        注意: Finnhub 免费版不支持股票特定新闻，使用市场新闻替代
        """
        # 获取市场新闻
        news = self._make_request("news", {
            "category": "general",
            "minId": 0,
            "maxSize": limit
        })
        
        return {
            "symbol": symbol,
            "news": news[:limit],
            "source": "finnhub"
        }
    
    def get_global_news(self, limit: int = 20, **kwargs) -> Dict[str, Any]:
        """获取全球财经新闻"""
        news = self._make_request("news", {
            "category": "general",
            "minId": 0,
            "maxSize": limit
        })
        
        return {
            "news": news[:limit],
            "source": "finnhub"
        }
    
    def get_insider_transactions(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """获取内部人交易"""
        exchange_symbol = f"{symbol.upper()} US"
        
        data = self._make_request("stock/insider-transactions", {
            "symbol": exchange_symbol
        })
        
        return {
            "symbol": symbol,
            "insider_transactions": data.get("data", []),
            "source": "finnhub"
        }
