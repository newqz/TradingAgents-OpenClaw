"""
TuShare Data Client
提供A股数据，支持基本面、行情、技术指标
官网: http://www.tushare.pro/
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

try:
    import tushare as ts
    TUSHARE_AVAILABLE = True
except ImportError:
    TUSHARE_AVAILABLE = False

# 添加 vendors 目录到 path
_vendors_dir = os.path.dirname(os.path.abspath(__file__))
if _vendors_dir not in sys.path:
    sys.path.insert(0, _vendors_dir)

from base import BaseVendor


class TuShareClient(BaseVendor):
    """TuShare 数据客户端（用于A股）"""
    
    def __init__(self, token: Optional[str] = None):
        """
        初始化 TuShare 客户端
        
        Args:
            token: TuShare Pro API token (免费注册: https://tushare.pro/)
                  也可通过 TUSHARE_TOKEN 环境变量设置
        """
        self.token = token or os.getenv("TUSHARE_TOKEN")
        self.pro = None
        
        if TUSHARE_AVAILABLE and self.token:
            try:
                ts.set_token(self.token)
                self.pro = ts.pro_api()
            except Exception as e:
                print(f"TuShare initialization warning: {e}")
    
    def _ensure_init(self):
        """确保 TuShare 已初始化"""
        if not TUSHARE_AVAILABLE:
            raise ImportError(
                "TuShare not installed. Install with: pip install tushare"
            )
        if not self.token:
            raise ValueError(
                "TuShare token required. "
                "Set TUSHARE_TOKEN environment variable or pass token parameter."
            )
        if not self.pro:
            ts.set_token(self.token)
            self.pro = ts.pro_api()
    
    def _convert_a_code(self, symbol: str) -> str:
        """
        转换A股代码格式
        
        000001.SZ -> 000001.SZ
        600000.SH -> 600000.SH
        000001 -> 自动判断
        """
        symbol = symbol.upper().strip()
        
        # 已经是完整格式
        if symbol.endswith((".SZ", ".SH", ".SS")):
            return symbol
        
        # 纯数字，需要补充后缀
        if symbol.isdigit() and len(symbol) == 6:
            # 6开头是上海，0/3开头是深圳
            if symbol.startswith("6"):
                return f"{symbol}.SH"
            else:
                return f"{symbol}.SZ"
        
        return symbol
    
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
        获取A股历史行情
        
        Args:
            symbol: A股代码 (e.g., "000001.SZ", "600000.SH", "000001")
            period: 时间周期 (1d, 1w, 1m, 1y)
            interval: 数据间隔
            start: 开始日期 (YYYYMMDD)
            end: 结束日期 (YYYYMMDD)
        """
        self._ensure_init()
        
        ts_code = self._convert_a_code(symbol)
        
        # 解析日期
        if end:
            end_date = end
        else:
            end_date = datetime.now().strftime("%Y%m%d")
        
        if start:
            start_date = start
        else:
            days_map = {"1d": 365, "1w": 365, "1m": 365 * 3, "1y": 365 * 5}
            days = days_map.get(period, 365)
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
        
        try:
            df = self.pro.daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )
            
            if df is None or df.empty:
                return {
                    "symbol": symbol,
                    "ts_code": ts_code,
                    "error": "No data available",
                    "source": "tushare"
                }
            
            # 转换格式
            ohlcv = []
            for _, row in df.iterrows():
                ohlcv.append({
                    "date": row["trade_date"],
                    "open": row["open"],
                    "high": row["high"],
                    "low": row["low"],
                    "close": row["close"],
                    "volume": row["vol"]
                })
            
            # 按日期排序（降序）
            ohlcv.reverse()
            
            return {
                "symbol": symbol,
                "ts_code": ts_code,
                "data": ohlcv,
                "source": "tushare"
            }
            
        except Exception as e:
            raise RuntimeError(f"TuShare get_stock_data error: {e}")
    
    def get_indicators(self, symbol: str, indicators: List[str] = None, **kwargs) -> Dict[str, Any]:
        """
        获取技术指标
        注意: TuShare 基础版不直接提供技术指标计算
        """
        # 基本面指标替代
        indicator_map = {
            "PE": "市盈率",
            "PB": "市净率",
            "PS": "市销率",
            "DC": "总市值",
        }
        
        return {
            "symbol": symbol,
            "indicators": indicator_map,
            "note": "TuShare provides financial indicators, not technical indicators",
            "source": "tushare"
        }
    
    def get_fundamentals(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """
        获取A股基本面信息
        """
        self._ensure_init()
        
        ts_code = self._convert_a_code(symbol)
        
        try:
            # 获取股票基本信息
            df = self.pro.stock_basic(
                ts_code=ts_code,
                list_status="L",
                fields="ts_code,symbol,name,area,industry,market,list_date"
            )
            
            if df is None or df.empty:
                return {
                    "symbol": symbol,
                    "error": "Stock not found",
                    "source": "tushare"
                }
            
            basic_info = df.iloc[0].to_dict() if len(df) > 0 else {}
            
            # 获取财务指标
            try:
                financials = self.pro.fina_indicator(
                    ts_code=ts_code,
                    start_date=(datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
                )
                fina_data = financials.iloc[0].to_dict() if not financials.empty else {}
            except Exception:
                fina_data = {}
            
            return {
                "symbol": symbol,
                "ts_code": ts_code,
                "basic_info": basic_info,
                "financial_indicators": fina_data,
                "source": "tushare"
            }
            
        except Exception as e:
            raise RuntimeError(f"TuShare get_fundamentals error: {e}")
    
    def get_balance_sheet(self, symbol: str, freq: str = "annual", **kwargs) -> Dict[str, Any]:
        """获取资产负债表"""
        self._ensure_init()
        
        ts_code = self._convert_a_code(symbol)
        
        try:
            period = freq  # annual, quarterly
            
            df = self.pro.balancesheet(
                ts_code=ts_code,
                period=period,
                fields="ts_code,ann_date,end_date,total_liab,total_asset"
            )
            
            return {
                "symbol": symbol,
                "ts_code": ts_code,
                "balance_sheet": df.to_dict("records") if not df.empty else [],
                "source": "tushare"
            }
            
        except Exception as e:
            raise RuntimeError(f"TuShare get_balance_sheet error: {e}")
    
    def get_income_statement(self, symbol: str, freq: str = "annual", **kwargs) -> Dict[str, Any]:
        """获取利润表"""
        self._ensure_init()
        
        ts_code = self._convert_a_code(symbol)
        
        try:
            df = self.pro.income(
                ts_code=ts_code,
                period=freq,
                fields="ts_code,ann_date,end_date,revenue,profit"
            )
            
            return {
                "symbol": symbol,
                "ts_code": ts_code,
                "income_statement": df.to_dict("records") if not df.empty else [],
                "source": "tushare"
            }
            
        except Exception as e:
            raise RuntimeError(f"TuShare get_income_statement error: {e}")
    
    def get_cashflow(self, symbol: str, freq: str = "annual", **kwargs) -> Dict[str, Any]:
        """获取现金流量表"""
        self._ensure_init()
        
        ts_code = self._convert_a_code(symbol)
        
        try:
            df = self.pro.cashflow(
                ts_code=ts_code,
                period=freq,
                fields="ts_code,ann_date,end_date,net_inc,operate_cashflow"
            )
            
            return {
                "symbol": symbol,
                "ts_code": ts_code,
                "cashflow": df.to_dict("records") if not df.empty else [],
                "source": "tushare"
            }
            
        except Exception as e:
            raise RuntimeError(f"TuShare get_cashflow error: {e}")
    
    def get_news(self, symbol: str, limit: int = 10, **kwargs) -> Dict[str, Any]:
        """
        获取新闻数据
        注意: TuShare 基础版不支持新闻 API
        """
        return {
            "symbol": symbol,
            "news": [],
            "note": "TuShare basic version does not provide news API",
            "source": "tushare"
        }
    
    def get_global_news(self, limit: int = 20, **kwargs) -> Dict[str, Any]:
        """获取财经新闻"""
        return {
            "news": [],
            "note": "TuShare basic version does not provide news API",
            "source": "tushare"
        }
    
    def get_insider_transactions(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """
        获取内部人交易（股权变动）
        """
        self._ensure_init()
        
        ts_code = self._convert_a_code(symbol)
        
        try:
            df = self.pro.stk_holder_tracker(
                ts_code=ts_code,
                start_date=(datetime.now() - timedelta(days=90)).strftime("%Y%m%d")
            )
            
            return {
                "symbol": symbol,
                "ts_code": ts_code,
                "insider_transactions": df.to_dict("records") if not df.empty else [],
                "source": "tushare"
            }
            
        except Exception as e:
            # 可能是权限问题，返回空
            return {
                "symbol": symbol,
                "ts_code": ts_code,
                "insider_transactions": [],
                "note": f"Failed to get insider transactions: {e}",
                "source": "tushare"
            }
