"""
Yahoo Finance 数据客户端
使用 yfinance 库获取股票数据
"""

import pandas as pd
from typing import Any, Dict, List, Optional
from datetime import datetime


class YFinanceClient:
    """Yahoo Finance 数据客户端"""
    
    def __init__(self):
        self.name = "yfinance"
        try:
            import yfinance as yf
            self.yf = yf
        except ImportError:
            raise ImportError(
                "yfinance is required. Install with: pip install yfinance"
            )
    
    def _get_ticker(self, symbol: str):
        """获取 ticker 对象"""
        return self.yf.Ticker(symbol)
    
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
        """
        ticker = self._get_ticker(symbol)
        
        # 获取历史数据
        if start and end:
            hist = ticker.history(start=start, end=end, interval=interval)
        else:
            hist = ticker.history(period=period, interval=interval)
        
        if hist.empty:
            raise ValueError(f"No data found for {symbol}")
        
        # 格式化数据
        hist.reset_index(inplace=True)
        if 'Date' in hist.columns:
            hist['Date'] = hist['Date'].dt.strftime('%Y-%m-%d')
        elif 'Datetime' in hist.columns:
            hist['Datetime'] = hist['Datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        return {
            "symbol": symbol,
            "data": hist.to_dict('records'),
            "period": period,
            "interval": interval,
            "source": "yfinance"
        }
    
    def get_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """
        获取公司基本面数据
        """
        ticker = self._get_ticker(symbol)
        info = ticker.info
        
        if not info:
            raise ValueError(f"No fundamental data found for {symbol}")
        
        # 提取关键信息
        company_info = {
            "name": info.get("longName"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "country": info.get("country"),
            "website": info.get("website"),
            "description": info.get("longBusinessSummary"),
            "employees": info.get("fullTimeEmployees"),
        }
        
        financial_highlights = {
            "market_cap": info.get("marketCap"),
            "enterprise_value": info.get("enterpriseValue"),
            "revenue": info.get("totalRevenue"),
            "revenue_growth": info.get("revenueGrowth"),
            "gross_profit": info.get("grossProfits"),
            "ebitda": info.get("ebitda"),
            "net_income": info.get("netIncomeToCommon"),
            "profit_margin": info.get("profitMargins"),
            "operating_margin": info.get("operatingMargins"),
        }
        
        valuation = {
            "pe_ratio": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "peg_ratio": info.get("pegRatio"),
            "pb_ratio": info.get("priceToBook"),
            "ps_ratio": info.get("priceToSalesTrailing12Months"),
            "ev_ebitda": info.get("enterpriseToEbitda"),
            "ev_revenue": info.get("enterpriseToRevenue"),
        }
        
        return {
            "symbol": symbol,
            "company_info": company_info,
            "financial_highlights": financial_highlights,
            "valuation": valuation,
            "source": "yfinance",
            "raw_info": info  # 保留原始数据
        }
    
    def get_balance_sheet(
        self,
        symbol: str,
        freq: str = "quarterly"
    ) -> Dict[str, Any]:
        """获取资产负债表"""
        ticker = self._get_ticker(symbol)
        
        if freq == "quarterly":
            bs = ticker.quarterly_balance_sheet
        else:
            bs = ticker.balance_sheet
        
        if bs is None or bs.empty:
            raise ValueError(f"No balance sheet data for {symbol}")
        
        # 转换为可读格式
        bs_dict = {}
        for col in bs.columns:
            date_str = col.strftime('%Y-%m-%d') if hasattr(col, 'strftime') else str(col)
            bs_dict[date_str] = bs[col].dropna().to_dict()
        
        return {
            "symbol": symbol,
            "frequency": freq,
            "balance_sheet": bs_dict,
            "source": "yfinance"
        }
    
    def get_income_statement(
        self,
        symbol: str,
        freq: str = "quarterly"
    ) -> Dict[str, Any]:
        """获取利润表"""
        ticker = self._get_ticker(symbol)
        
        if freq == "quarterly":
            inc = ticker.quarterly_income_stmt
        else:
            inc = ticker.income_stmt
        
        if inc is None or inc.empty:
            raise ValueError(f"No income statement data for {symbol}")
        
        inc_dict = {}
        for col in inc.columns:
            date_str = col.strftime('%Y-%m-%d') if hasattr(col, 'strftime') else str(col)
            inc_dict[date_str] = inc[col].dropna().to_dict()
        
        return {
            "symbol": symbol,
            "frequency": freq,
            "income_statement": inc_dict,
            "source": "yfinance"
        }
    
    def get_cashflow(
        self,
        symbol: str,
        freq: str = "quarterly"
    ) -> Dict[str, Any]:
        """获取现金流量表"""
        ticker = self._get_ticker(symbol)
        
        if freq == "quarterly":
            cf = ticker.quarterly_cashflow
        else:
            cf = ticker.cashflow
        
        if cf is None or cf.empty:
            raise ValueError(f"No cash flow data for {symbol}")
        
        cf_dict = {}
        for col in cf.columns:
            date_str = col.strftime('%Y-%m-%d') if hasattr(col, 'strftime') else str(col)
            cf_dict[date_str] = cf[col].dropna().to_dict()
        
        return {
            "symbol": symbol,
            "frequency": freq,
            "cashflow": cf_dict,
            "source": "yfinance"
        }
    
    def get_indicators(
        self,
        symbol: str,
        indicators: List[str],
        period: str = "6mo",
        **kwargs
    ) -> Dict[str, Any]:
        """
        计算技术指标
        """
        # 获取价格数据
        price_data = self.get_stock_data(symbol, period=period)
        df = pd.DataFrame(price_data["data"])
        
        if df.empty:
            raise ValueError(f"No price data for {symbol}")
        
        # 计算指标
        results = {}
        
        for indicator in indicators:
            indicator = indicator.lower().strip()
            
            if indicator == "rsi":
                results["rsi"] = self._calc_rsi(df)
            elif indicator == "macd":
                results["macd"] = self._calc_macd(df)
            elif indicator == "bollinger_bands":
                results["bollinger_bands"] = self._calc_bollinger_bands(df)
            elif indicator == "sma":
                results["sma"] = self._calc_sma(df)
            elif indicator == "ema":
                results["ema"] = self._calc_ema(df)
            else:
                results[indicator] = {"error": f"Unknown indicator: {indicator}"}
        
        return {
            "symbol": symbol,
            "indicators": results,
            "period": period,
            "source": "yfinance"
        }
    
    def _calc_rsi(self, df: pd.DataFrame, period: int = 14) -> Dict:
        """计算 RSI 指标"""
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        latest = rsi.iloc[-1]
        
        return {
            "value": round(latest, 2),
            "period": period,
            "interpretation": (
                "oversold" if latest < 30 else
                "overbought" if latest > 70 else
                "neutral"
            )
        }
    
    def _calc_macd(self, df: pd.DataFrame) -> Dict:
        """计算 MACD 指标"""
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        histogram = macd - signal
        
        return {
            "macd": round(macd.iloc[-1], 4),
            "signal": round(signal.iloc[-1], 4),
            "histogram": round(histogram.iloc[-1], 4),
            "trend": "bullish" if macd.iloc[-1] > signal.iloc[-1] else "bearish"
        }
    
    def _calc_bollinger_bands(self, df: pd.DataFrame, period: int = 20) -> Dict:
        """计算布林带"""
        sma = df['Close'].rolling(window=period).mean()
        std = df['Close'].rolling(window=period).std()
        upper = sma + (std * 2)
        lower = sma - (std * 2)
        
        current_price = df['Close'].iloc[-1]
        
        return {
            "upper": round(upper.iloc[-1], 2),
            "middle": round(sma.iloc[-1], 2),
            "lower": round(lower.iloc[-1], 2),
            "position": (
                "above_upper" if current_price > upper.iloc[-1] else
                "below_lower" if current_price < lower.iloc[-1] else
                "within_band"
            )
        }
    
    def _calc_sma(self, df: pd.DataFrame) -> Dict:
        """计算简单移动平均线"""
        sma_20 = df['Close'].rolling(window=20).mean().iloc[-1]
        sma_50 = df['Close'].rolling(window=50).mean().iloc[-1]
        sma_200 = df['Close'].rolling(window=200).mean().iloc[-1]
        
        return {
            "sma_20": round(sma_20, 2),
            "sma_50": round(sma_50, 2),
            "sma_200": round(sma_200, 2) if not pd.isna(sma_200) else None
        }
    
    def _calc_ema(self, df: pd.DataFrame) -> Dict:
        """计算指数移动平均线"""
        ema_12 = df['Close'].ewm(span=12, adjust=False).mean().iloc[-1]
        ema_26 = df['Close'].ewm(span=26, adjust=False).mean().iloc[-1]
        
        return {
            "ema_12": round(ema_12, 2),
            "ema_26": round(ema_26, 2)
        }
    
    def get_news(
        self,
        symbol: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """获取新闻数据"""
        ticker = self._get_ticker(symbol)
        
        try:
            news = ticker.news
            if not news:
                return {
                    "symbol": symbol,
                    "news": [],
                    "count": 0,
                    "source": "yfinance"
                }
            
            # 格式化新闻
            formatted_news = []
            for item in news[:limit]:
                formatted_news.append({
                    "title": item.get("title"),
                    "publisher": item.get("publisher"),
                    "published": item.get("published"),
                    "link": item.get("link"),
                    "summary": item.get("summary", "")
                })
            
            return {
                "symbol": symbol,
                "news": formatted_news,
                "count": len(formatted_news),
                "source": "yfinance"
            }
            
        except Exception as e:
            return {
                "symbol": symbol,
                "news": [],
                "count": 0,
                "error": str(e),
                "source": "yfinance"
            }
    
    def get_global_news(self, limit: int = 20) -> Dict[str, Any]:
        """
        获取全球财经新闻
        注意：yfinance 不直接提供全球新闻，返回空或模拟数据
        """
        # yfinance 没有直接的全局新闻接口
        # 可以通过 ^GSPC (S&P 500) 获取相关新闻
        return self.get_news("^GSPC", limit=limit)
    
    def get_insider_transactions(self, symbol: str) -> Dict[str, Any]:
        """
        获取内部人交易数据
        注意：yfinance 的 insider 数据有限
        """
        ticker = self._get_ticker(symbol)
        
        try:
            # 尝试获取机构持股变化
            institutional_holders = ticker.institutional_holders
            
            if institutional_holders is not None and not institutional_holders.empty:
                return {
                    "symbol": symbol,
                    "institutional_holders": institutional_holders.to_dict('records'),
                    "note": "yfinance provides limited insider data",
                    "source": "yfinance"
                }
            else:
                return {
                    "symbol": symbol,
                    "institutional_holders": [],
                    "note": "No insider data available",
                    "source": "yfinance"
                }
                
        except Exception as e:
            return {
                "symbol": symbol,
                "institutional_holders": [],
                "error": str(e),
                "source": "yfinance"
            }
