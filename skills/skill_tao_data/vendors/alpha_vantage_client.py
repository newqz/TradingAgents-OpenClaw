"""
Alpha Vantage 数据客户端
使用 Alpha Vantage API 获取股票数据
需要 API Key: https://www.alphavantage.co/support/#api-key
"""

import os
from typing import Any, Dict, List, Optional


class AlphaVantageClient:
    """Alpha Vantage 数据客户端"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.name = "alpha_vantage"
        self.api_key = api_key or os.getenv("ALPHA_VANTAGE_API_KEY")
        self._initialized = False
        
        if not self.api_key:
            # 不在初始化时抛出错误，留到实际调用时再检查
            return
        
        try:
            from alpha_vantage.timeseries import TimeSeries
            from alpha_vantage.fundamentaldata import FundamentalData
            from alpha_vantage.techindicators import TechIndicators
            
            self.TimeSeries = TimeSeries
            self.FundamentalData = FundamentalData
            self.TechIndicators = TechIndicators
            self._initialized = True
            
        except ImportError:
            raise ImportError(
                "alpha_vantage is required. Install with: pip install alpha-vantage"
            )
    
    def _ensure_api_key(self):
        """确保 API key 已设置"""
        if not self.api_key:
            raise ValueError(
                "Alpha Vantage API key is required. "
                "Get one free at: https://www.alphavantage.co/support/#api-key"
            )
    
    def _handle_rate_limit(self):
        """处理 API 限流 - Alpha Vantage 免费版有调用频率限制"""
        import time
        # 免费版限制: 5 calls per minute
        time.sleep(12)  # 每次调用间隔 12 秒
    
    def get_stock_data(
        self,
        symbol: str,
        period: str = "1y",
        interval: str = "1d",
        start: Optional[str] = None,
        end: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取股票历史价格数据"""
        self._ensure_api_key()
        self._handle_rate_limit()
        
        ts = self.TimeSeries(key=self.api_key, output_format='pandas')
        
        # 映射 period 到 Alpha Vantage 的输出大小
        outputsize = "full" if period in ["1y", "2y", "5y", "10y", "max"] else "compact"
        
        # 获取数据
        if interval in ["1m", "5m", "15m", "30m", "60m"]:
            # 分钟级数据
            data, meta = ts.get_intraday(
                symbol=symbol,
                interval=interval.replace("m", "min"),
                outputsize=outputsize
            )
        else:
            # 日线数据
            data, meta = ts.get_daily(symbol=symbol, outputsize=outputsize)
        
        if data.empty:
            raise ValueError(f"No data found for {symbol}")
        
        # 格式化
        data.reset_index(inplace=True)
        if 'date' in data.columns:
            data['date'] = data['date'].dt.strftime('%Y-%m-%d')
        
        # 重命名列以统一格式
        data.columns = [col.capitalize() for col in data.columns]
        
        return {
            "symbol": symbol,
            "data": data.to_dict('records'),
            "period": period,
            "interval": interval,
            "source": "alpha_vantage",
            "meta": meta
        }
    
    def get_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """获取公司基本面数据"""
        self._ensure_api_key()
        self._handle_rate_limit()
        
        fd = self.FundamentalData(key=self.api_key, output_format='pandas')
        
        # 获取公司概况
        overview, _ = fd.get_company_overview(symbol)
        
        if overview is None or overview.empty:
            raise ValueError(f"No fundamental data for {symbol}")
        
        # Alpha Vantage 返回的是 DataFrame，取第一行
        info = overview.iloc[0].to_dict() if not overview.empty else {}
        
        company_info = {
            "name": info.get("Name"),
            "sector": info.get("Sector"),
            "industry": info.get("Industry"),
            "country": info.get("Country"),
            "description": info.get("Description"),
        }
        
        financial_highlights = {
            "market_cap": info.get("MarketCapitalization"),
            "revenue": info.get("RevenueTTM"),
            "gross_profit": info.get("GrossProfitTTM"),
            "ebitda": info.get("EBITDA"),
            "net_income": info.get("NetIncomeTTM"),
        }
        
        valuation = {
            "pe_ratio": info.get("PERatio"),
            "forward_pe": info.get("ForwardPE"),
            "peg_ratio": info.get("PEGRatio"),
            "pb_ratio": info.get("PriceToBookRatio"),
            "ps_ratio": info.get("PriceToSalesRatioTTM"),
            "ev_ebitda": info.get("EVToEBITDA"),
            "ev_revenue": info.get("EVToRevenue"),
        }
        
        return {
            "symbol": symbol,
            "company_info": company_info,
            "financial_highlights": financial_highlights,
            "valuation": valuation,
            "source": "alpha_vantage",
            "raw_info": info
        }
    
    def get_balance_sheet(
        self,
        symbol: str,
        freq: str = "quarterly"
    ) -> Dict[str, Any]:
        """获取资产负债表"""
        self._ensure_api_key()
        self._handle_rate_limit()
        
        fd = self.FundamentalData(key=self.api_key, output_format='pandas')
        
        if freq == "quarterly":
            data, _ = fd.get_balance_sheet_quarterly(symbol)
        else:
            data, _ = fd.get_balance_sheet_annual(symbol)
        
        if data is None or data.empty:
            raise ValueError(f"No balance sheet data for {symbol}")
        
        return {
            "symbol": symbol,
            "frequency": freq,
            "balance_sheet": data.to_dict(),
            "source": "alpha_vantage"
        }
    
    def get_income_statement(
        self,
        symbol: str,
        freq: str = "quarterly"
    ) -> Dict[str, Any]:
        """获取利润表"""
        self._ensure_api_key()
        self._handle_rate_limit()
        
        fd = self.FundamentalData(key=self.api_key, output_format='pandas')
        
        if freq == "quarterly":
            data, _ = fd.get_income_statement_quarterly(symbol)
        else:
            data, _ = fd.get_income_statement_annual(symbol)
        
        if data is None or data.empty:
            raise ValueError(f"No income statement data for {symbol}")
        
        return {
            "symbol": symbol,
            "frequency": freq,
            "income_statement": data.to_dict(),
            "source": "alpha_vantage"
        }
    
    def get_cashflow(
        self,
        symbol: str,
        freq: str = "quarterly"
    ) -> Dict[str, Any]:
        """获取现金流量表"""
        self._ensure_api_key()
        self._handle_rate_limit()
        
        fd = self.FundamentalData(key=self.api_key, output_format='pandas')
        
        if freq == "quarterly":
            data, _ = fd.get_cash_flow_quarterly(symbol)
        else:
            data, _ = fd.get_cash_flow_annual(symbol)
        
        if data is None or data.empty:
            raise ValueError(f"No cash flow data for {symbol}")
        
        return {
            "symbol": symbol,
            "frequency": freq,
            "cashflow": data.to_dict(),
            "source": "alpha_vantage"
        }
    
    def get_indicators(
        self,
        symbol: str,
        indicators: List[str],
        period: str = "6mo",
        **kwargs
    ) -> Dict[str, Any]:
        """获取技术指标"""
        self._ensure_api_key()
        
        """
        Alpha Vantage 提供丰富的技术指标
        """
        self._handle_rate_limit()
        
        ti = self.TechIndicators(key=self.api_key, output_format='pandas')
        results = {}
        
        # 映射指标名称到 Alpha Vantage 方法
        indicator_map = {
            "rsi": lambda: ti.get_rsi(symbol, interval='daily'),
            "macd": lambda: ti.get_macd(symbol, interval='daily'),
            "sma": lambda: ti.get_sma(symbol, interval='daily'),
            "ema": lambda: ti.get_ema(symbol, interval='daily'),
            "bbands": lambda: ti.get_bbands(symbol, interval='daily'),
            "stoch": lambda: ti.get_stoch(symbol, interval='daily'),
            "adx": lambda: ti.get_adx(symbol, interval='daily'),
            "atr": lambda: ti.get_atr(symbol, interval='daily'),
        }
        
        for indicator in indicators:
            indicator = indicator.lower().strip()
            
            try:
                if indicator in indicator_map:
                    data, meta = indicator_map[indicator]()
                    
                    if not data.empty:
                        latest = data.iloc[0].to_dict()
                        results[indicator] = {
                            "value": latest,
                            "meta": meta
                        }
                    else:
                        results[indicator] = {"error": "No data available"}
                else:
                    results[indicator] = {"error": f"Indicator not supported: {indicator}"}
                    
            except Exception as e:
                results[indicator] = {"error": str(e)}
            
            # 每个指标调用间隔
            if indicator != indicators[-1]:
                self._handle_rate_limit()
        
        return {
            "symbol": symbol,
            "indicators": results,
            "period": period,
            "source": "alpha_vantage"
        }
    
    def get_news(
        self,
        symbol: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        获取新闻数据
        Alpha Vantage 有专门的新闻 API (需要高级套餐)
        """
        # Alpha Vantage 免费版不包含新闻 API
        # 返回提示信息
        return {
            "symbol": symbol,
            "news": [],
            "count": 0,
            "note": "Alpha Vantage free tier does not include news API. Consider upgrading or using yfinance.",
            "source": "alpha_vantage"
        }
    
    def get_global_news(self, limit: int = 20) -> Dict[str, Any]:
        """获取全球财经新闻"""
        return {
            "news": [],
            "count": 0,
            "note": "Alpha Vantage free tier does not include global news API.",
            "source": "alpha_vantage"
        }
    
    def get_insider_transactions(self, symbol: str) -> Dict[str, Any]:
        """获取内部人交易数据"""
        return {
            "symbol": symbol,
            "insider_transactions": [],
            "note": "Alpha Vantage does not provide insider transaction data.",
            "source": "alpha_vantage"
        }
