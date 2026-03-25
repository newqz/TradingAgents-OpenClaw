"""
A股/港股数据客户端
使用 akshare 库获取中国股票数据
"""

import re
from typing import Any, Dict, List, Optional
from datetime import datetime


class ChinaStockClient:
    """
    A股/港股数据客户端
    
    支持:
    - A股: 000001.SZ, 600000.SH, 300001.SZ
    - 港股: 0700.HK, 3690.HK
    """
    
    def __init__(self):
        self.name = "china_stock"
        self.ak = None
        self._available = False
        
        try:
            import akshare as ak
            self.ak = ak
            self._available = True
        except ImportError:
            # 不在初始化时抛出错误，留到实际调用时再检查
            pass
    
    def _ensure_available(self):
        """确保 akshare 可用"""
        if not self._available:
            raise ImportError(
                "akshare is required for China stock data. "
                "Install with: pip install akshare"
            )
    
    def _parse_symbol(self, symbol: str) -> Dict[str, str]:
        """
        解析股票代码
        
        支持的格式:
        - A股: 000001.SZ, 600000.SH, 300001.SZ
        - 港股: 0700.HK, 3690.HK
        - 纯数字: 000001 (默认深交所)
        """
        symbol = symbol.upper().strip()
        
        # 匹配带后缀的格式
        if ".SZ" in symbol:
            return {
                "code": symbol.replace(".SZ", ""),
                "market": "sz",
                "type": "a_stock"
            }
        elif ".SH" in symbol or ".SS" in symbol:
            return {
                "code": symbol.replace(".SH", "").replace(".SS", ""),
                "market": "sh",
                "type": "a_stock"
            }
        elif ".HK" in symbol:
            code = symbol.replace(".HK", "")
            # 港股需要补零到5位
            code = code.zfill(5)
            return {
                "code": code,
                "market": "hk",
                "type": "hk_stock"
            }
        
        # 纯数字，根据代码判断市场
        if symbol.isdigit():
            code = symbol
            if code.startswith("6"):
                return {"code": code, "market": "sh", "type": "a_stock"}
            elif code.startswith("0") or code.startswith("3"):
                return {"code": code, "market": "sz", "type": "a_stock"}
            elif len(code) <= 5:
                # 可能是港股
                return {"code": code.zfill(5), "market": "hk", "type": "hk_stock"}
        
        raise ValueError(f"Unsupported symbol format: {symbol}")
    
    def get_stock_data(
        self,
        symbol: str,
        period: str = "1y",
        interval: str = "1d",
        start: Optional[str] = None,
        end: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取股票历史数据"""
        self._ensure_available()
        """
        获取股票历史价格数据
        """
        parsed = self._parse_symbol(symbol)
        code = parsed["code"]
        market = parsed["market"]
        stock_type = parsed["type"]
        
        # 将 period 转换为日期范围
        if not start:
            from datetime import timedelta
            end_date = datetime.now()
            
            period_map = {
                "1d": 1, "5d": 5, "1mo": 30, "3mo": 90,
                "6mo": 180, "1y": 365, "2y": 730, "5y": 1825
            }
            days = period_map.get(period, 365)
            start_date = end_date - timedelta(days=days)
            start = start_date.strftime("%Y%m%d")
            end = end_date.strftime("%Y%m%d")
        
        if stock_type == "a_stock":
            # A股数据
            if market == "sh":
                df = self.ak.stock_zh_a_hist(
                    symbol=code,
                    period="daily",
                    start_date=start,
                    end_date=end,
                    adjust="qfq"  # 前复权
                )
            else:
                df = self.ak.stock_zh_a_hist(
                    symbol=code,
                    period="daily",
                    start_date=start,
                    end_date=end,
                    adjust="qfq"
                )
        else:
            # 港股数据
            df = self.ak.stock_hk_hist(
                symbol=code,
                period="daily",
                start_date=start,
                end_date=end,
                adjust="qfq"
            )
        
        if df is None or df.empty:
            raise ValueError(f"No data found for {symbol}")
        
        # 标准化列名
        column_mapping = {
            "日期": "Date",
            "开盘": "Open",
            "收盘": "Close",
            "最高": "High",
            "最低": "Low",
            "成交量": "Volume",
            "成交额": "Amount",
            "振幅": "Amplitude",
            "涨跌幅": "Change_pct",
            "涨跌额": "Change",
            "换手率": "Turnover"
        }
        
        df = df.rename(columns=column_mapping)
        
        # 格式化日期
        if "Date" in df.columns:
            df["Date"] = df["Date"].astype(str)
        
        return {
            "symbol": symbol,
            "data": df.to_dict('records'),
            "period": period,
            "interval": interval,
            "market": market,
            "stock_type": stock_type,
            "source": "akshare"
        }
    
    def get_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """获取公司基本面数据"""
        self._ensure_available()
        parsed = self._parse_symbol(symbol)
        code = parsed["code"]
        stock_type = parsed["type"]
        
        if stock_type == "a_stock":
            # A股基本面
            try:
                # 获取个股信息
                info_df = self.ak.stock_individual_info_em(symbol=code)
                info = dict(zip(info_df["item"], info_df["value"]))
                
                company_info = {
                    "name": info.get("股票简称"),
                    "full_name": info.get("公司名称"),
                    "industry": info.get("行业"),
                    "province": info.get("地域"),
                    "website": info.get("公司主页"),
                }
                
                financial_highlights = {
                    "total_shares": info.get("总股本"),
                    "float_shares": info.get("流通股"),
                    "market_cap": None,  # 需要计算
                }
                
                # 获取财务指标
                indicators_df = self.ak.stock_financial_analysis_indicator(symbol=code)
                if not indicators_df.empty:
                    latest = indicators_df.iloc[0]
                    valuation = {
                        "pe_ratio": latest.get("市盈率"),
                        "pb_ratio": latest.get("市净率"),
                        "ps_ratio": latest.get("市销率"),
                        "roe": latest.get("净资产收益率"),
                    }
                else:
                    valuation = {}
                
                return {
                    "symbol": symbol,
                    "company_info": company_info,
                    "financial_highlights": financial_highlights,
                    "valuation": valuation,
                    "source": "akshare",
                    "raw_info": info
                }
                
            except Exception as e:
                raise ValueError(f"Failed to get fundamentals for {symbol}: {e}")
        
        else:
            # 港股基本面
            try:
                info_df = self.ak.stock_hk_gdfx_free_detail_em(symbol=code)
                
                return {
                    "symbol": symbol,
                    "company_info": {
                        "name": f"港股 {code}",
                        "note": "港股基本面数据有限"
                    },
                    "financial_highlights": {},
                    "valuation": {},
                    "source": "akshare",
                    "note": "港股基本面数据通过 stock_hk_gdfx_free_detail_em 获取"
                }
                
            except Exception as e:
                raise ValueError(f"Failed to get HK stock fundamentals: {e}")
    
    def get_balance_sheet(
        self,
        symbol: str,
        freq: str = "quarterly"
    ) -> Dict[str, Any]:
        """获取资产负债表"""
        self._ensure_available()
        parsed = self._parse_symbol(symbol)
        code = parsed["code"]
        stock_type = parsed["type"]
        
        if stock_type != "a_stock":
            raise ValueError("Balance sheet data only available for A-shares")
        
        try:
            if freq == "quarterly":
                df = self.ak.stock_balance_sheet_by_report_em(symbol=code)
            else:
                df = self.ak.stock_balance_sheet_by_yearly_em(symbol=code)
            
            return {
                "symbol": symbol,
                "frequency": freq,
                "balance_sheet": df.to_dict() if not df.empty else {},
                "source": "akshare"
            }
            
        except Exception as e:
            raise ValueError(f"Failed to get balance sheet: {e}")
    
    def get_income_statement(
        self,
        symbol: str,
        freq: str = "quarterly"
    ) -> Dict[str, Any]:
        """获取利润表"""
        self._ensure_available()
        parsed = self._parse_symbol(symbol)
        code = parsed["code"]
        stock_type = parsed["type"]
        
        if stock_type != "a_stock":
            raise ValueError("Income statement only available for A-shares")
        
        try:
            if freq == "quarterly":
                df = self.ak.stock_profit_sheet_by_report_em(symbol=code)
            else:
                df = self.ak.stock_profit_sheet_by_yearly_em(symbol=code)
            
            return {
                "symbol": symbol,
                "frequency": freq,
                "income_statement": df.to_dict() if not df.empty else {},
                "source": "akshare"
            }
            
        except Exception as e:
            raise ValueError(f"Failed to get income statement: {e}")
    
    def get_cashflow(
        self,
        symbol: str,
        freq: str = "quarterly"
    ) -> Dict[str, Any]:
        """获取现金流量表"""
        self._ensure_available()
        parsed = self._parse_symbol(symbol)
        code = parsed["code"]
        stock_type = parsed["type"]
        
        if stock_type != "a_stock":
            raise ValueError("Cash flow data only available for A-shares")
        
        try:
            if freq == "quarterly":
                df = self.ak.stock_cash_flow_sheet_by_report_em(symbol=code)
            else:
                df = self.ak.stock_cash_flow_sheet_by_yearly_em(symbol=code)
            
            return {
                "symbol": symbol,
                "frequency": freq,
                "cashflow": df.to_dict() if not df.empty else {},
                "source": "akshare"
            }
            
        except Exception as e:
            raise ValueError(f"Failed to get cash flow: {e}")
    
    def get_indicators(
        self,
        symbol: str,
        indicators: List[str],
        period: str = "6mo",
        **kwargs
    ) -> Dict[str, Any]:
        """计算技术指标"""
        self._ensure_available()
        import pandas as pd
        
        # 获取价格数据
        price_data = self.get_stock_data(symbol, period=period)
        df = pd.DataFrame(price_data.get("data", []))
        
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
            "source": "akshare"
        }
    
    def _calc_rsi(self, df, period: int = 14) -> Dict:
        """计算 RSI"""
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        latest = rsi.iloc[-1]
        
        return {
            "value": round(float(latest), 2),
            "period": period,
            "interpretation": (
                "oversold" if latest < 30 else
                "overbought" if latest > 70 else
                "neutral"
            )
        }
    
    def _calc_macd(self, df) -> Dict:
        """计算 MACD"""
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        histogram = macd - signal
        
        return {
            "macd": round(float(macd.iloc[-1]), 4),
            "signal": round(float(signal.iloc[-1]), 4),
            "histogram": round(float(histogram.iloc[-1]), 4),
            "trend": "bullish" if macd.iloc[-1] > signal.iloc[-1] else "bearish"
        }
    
    def _calc_bollinger_bands(self, df, period: int = 20) -> Dict:
        """计算布林带"""
        sma = df['Close'].rolling(window=period).mean()
        std = df['Close'].rolling(window=period).std()
        upper = sma + (std * 2)
        lower = sma - (std * 2)
        
        current_price = df['Close'].iloc[-1]
        
        return {
            "upper": round(float(upper.iloc[-1]), 2),
            "middle": round(float(sma.iloc[-1]), 2),
            "lower": round(float(lower.iloc[-1]), 2),
            "position": (
                "above_upper" if current_price > upper.iloc[-1] else
                "below_lower" if current_price < lower.iloc[-1] else
                "within_band"
            )
        }
    
    def _calc_sma(self, df) -> Dict:
        """计算 SMA"""
        sma_20 = df['Close'].rolling(window=20).mean().iloc[-1]
        sma_60 = df['Close'].rolling(window=60).mean().iloc[-1]
        
        return {
            "sma_20": round(float(sma_20), 2),
            "sma_60": round(float(sma_60), 2)
        }
    
    def _calc_ema(self, df) -> Dict:
        """计算 EMA"""
        ema_12 = df['Close'].ewm(span=12, adjust=False).mean().iloc[-1]
        ema_26 = df['Close'].ewm(span=26, adjust=False).mean().iloc[-1]
        
        return {
            "ema_12": round(float(ema_12), 2),
            "ema_26": round(float(ema_26), 2)
        }
    
    def get_news(
        self,
        symbol: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """获取新闻数据"""
        self._ensure_available()
        parsed = self._parse_symbol(symbol)
        code = parsed["code"]
        
        try:
            # 获取个股新闻
            news_df = self.ak.stock_news_em(symbol=code)
            
            if news_df is None or news_df.empty:
                return {
                    "symbol": symbol,
                    "news": [],
                    "count": 0,
                    "source": "akshare"
                }
            
            # 格式化新闻
            formatted_news = []
            for _, row in news_df.head(limit).iterrows():
                formatted_news.append({
                    "title": row.get("新闻标题"),
                    "content": row.get("新闻内容"),
                    "published": row.get("发布时间"),
                    "source": row.get("文章来源")
                })
            
            return {
                "symbol": symbol,
                "news": formatted_news,
                "count": len(formatted_news),
                "source": "akshare"
            }
            
        except Exception as e:
            return {
                "symbol": symbol,
                "news": [],
                "count": 0,
                "error": str(e),
                "source": "akshare"
            }
    
    def get_global_news(self, limit: int = 20) -> Dict[str, Any]:
        """获取财经要闻"""
        self._ensure_available()
        try:
            # 获取东方财富财经要闻
            news_df = self.ak.stock_zh_a_spot_em()
            
            return {
                "news": [],
                "count": 0,
                "note": "Global news via akshare - use stock_news_em for individual stocks",
                "source": "akshare"
            }
            
        except Exception as e:
            return {
                "news": [],
                "count": 0,
                "error": str(e),
                "source": "akshare"
            }
    
    def get_insider_transactions(self, symbol: str) -> Dict[str, Any]:
        """获取内部人交易数据"""
        self._ensure_available()
        parsed = self._parse_symbol(symbol)
        code = parsed["code"]
        
        try:
            # 获取高管持股变动
            insider_df = self.ak.stock_gdfx_free_holding_detail_em(symbol=code)
            
            return {
                "symbol": symbol,
                "insider_transactions": insider_df.to_dict('records') if insider_df is not None else [],
                "source": "akshare"
            }
            
        except Exception as e:
            return {
                "symbol": symbol,
                "insider_transactions": [],
                "error": str(e),
                "source": "akshare"
            }
