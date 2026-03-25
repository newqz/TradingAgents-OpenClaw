"""
新浪财经股票数据客户端
用于获取A股、港股实时行情数据
数据来源: Eastmoney-stock skill (实际使用 Sina Finance API)
"""

import sys
import os
from typing import Any, Dict, List, Optional
from datetime import datetime

# 动态导入base
vendors_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, vendors_dir)
from base import BaseVendor


class SinaStockClient(BaseVendor):
    """
    新浪财经股票数据客户端
    
    支持:
    - A股: 600519.SH (贵州茅台), 000001.SZ (平安银行)
    - 港股: 00700.HK (腾讯), 03690.HK (美团)
    - 美股: US:AAPL, US:GOOGL
    
    注意: 实际使用 Sina Finance API (hq.sinajs.cn)
    """
    
    def __init__(self):
        super().__init__()
        self.name = "sina_stock"
        self.ak = None  # 不使用akshare，直接用requests
        self._available = True
        self._session = None
    
    def _ensure_available(self):
        """确保客户端可用"""
        if not self._available:
            raise ImportError("SinaStockClient is not available")
        
        if self._session is None:
            import requests
            self._session = requests.Session()
            self._session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'http://finance.sina.com.cn',
            })
    
    def _normalize_symbol(self, symbol: str) -> str:
        """
        标准化股票代码为新浪格式
        
        Args:
            symbol: 原始代码 (如 600519, 000001.SZ, 00700.HK)
        
        Returns:
            新浪格式 (如 sh600519, sz000001, hk00700)
        """
        symbol = symbol.upper().strip()
        
        # 美股
        if symbol.startswith('US:') or symbol.startswith('US.'):
            return symbol.replace('US:', 'us_').replace('US.', 'us_')
        
        # 港股
        if symbol.endswith('.HK'):
            code = symbol.replace('.HK', '').lstrip('0')
            return f'hk{code}'
        
        # A股沪市
        if len(symbol) == 6 and symbol.startswith(('6', '5')):
            return f'sh{symbol}'
        
        # A股深市
        if len(symbol) == 6 and symbol.startswith(('0', '3')):
            return f'sz{symbol}'
        
        # 已经是标准格式
        if symbol.startswith(('sh', 'sz', 'hk', 'us_')):
            return symbol
        
        return symbol
    
    def get_stock_data(
        self,
        symbol: str,
        period: str = "1d",
        interval: str = "1d",
        start: Optional[str] = None,
        end: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取股票实时行情数据
        
        Args:
            symbol: 股票代码 (如 600519, 000001.SZ, 00700.HK)
            period: 时间周期 (用于兼容，实际只返回实时数据)
            interval: 间隔 (用于兼容)
        
        Returns:
            包含股票数据的字典
        """
        self._ensure_available()
        
        normalized = self._normalize_symbol(symbol)
        
        try:
            url = f"https://hq.sinajs.cn/list={normalized}"
            
            response = self._session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.text.strip()
            
            if '不存在' in data or '错误的股票代码' in data.lower():
                return {
                    'error': f'股票代码不存在: {symbol}',
                    'symbol': symbol
                }
            
            # 解析数据
            # 格式: var hq_str_sh600519="名称,开盘价,昨日收盘价,当前价,最高价,最低价,...;";
            if '=' not in data:
                return {
                    'error': '数据格式异常',
                    'symbol': symbol
                }
            
            parts = data.split('=')
            if len(parts) < 2:
                return {'error': '数据格式异常', 'symbol': symbol}
            
            content = parts[1].strip().strip('";')
            values = content.split(',')
            
            if len(values) < 32:
                return {'error': '数据不完整', 'symbol': symbol, 'raw': data}
            
            name = values[0]
            open_price = float(values[1]) if values[1] else 0
            yesterday_close = float(values[2]) if values[2] else 0
            current_price = float(values[3]) if values[3] else 0
            high_price = float(values[4]) if values[4] else 0
            low_price = float(values[5]) if values[5] else 0
            
            # 涨跌
            change = current_price - yesterday_close
            change_percent = (change / yesterday_close * 100) if yesterday_close > 0 else 0
            
            # 成交量和成交额
            try:
                volume = int(float(values[8])) if values[8] else 0
            except:
                volume = 0
            
            try:
                amount = float(values[9]) if values[9] else 0
            except:
                amount = 0
            
            # 时间
            date = values[30] if len(values) > 30 else ''
            time = values[31] if len(values) > 31 else ''
            
            # 判断市场
            market = 'UNKNOWN'
            if normalized.startswith('sh'):
                market = '沪市A股'
            elif normalized.startswith('sz'):
                market = '深市A股'
            elif normalized.startswith('hk'):
                market = '港股'
            elif normalized.startswith('us_'):
                market = '美股'
            
            return {
                'symbol': symbol,
                'normalized': normalized,
                'name': name,
                'price': current_price,
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': current_price,  # 实时数据用当前价作为收盘价
                'yesterday_close': yesterday_close,
                'change': round(change, 2),
                'change_percent': round(change_percent, 2),
                'volume': volume,
                'amount': amount,
                'market': market,
                'timestamp': f"{date} {time}".strip(),
                'source': 'sina',
                'provider': self.name
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'symbol': symbol
            }
    
    def get_quote(self, symbols: List[str]) -> Dict[str, Any]:
        """
        批量获取股票报价
        
        Args:
            symbols: 股票代码列表
        
        Returns:
            批量查询结果
        """
        self._ensure_available()
        
        if not symbols:
            return {'error': '股票代码列表为空', 'results': {}}
        
        # 标准化并去重
        normalized_list = [self._normalize_symbol(s) for s in symbols]
        unique_normalized = list(dict.fromkeys(normalized_list))  # 去重保持顺序
        
        # 批量查询 (新浪支持最多50个)
        codes = ','.join(unique_normalized[:50])
        
        try:
            url = f"https://hq.sinajs.cn/list={codes}"
            response = self._session.get(url, timeout=15)
            response.raise_for_status()
            
            data = response.text.strip()
            lines = data.split('\n')
            
            results = {}
            for i, line in enumerate(lines):
                if '=' not in line:
                    continue
                
                parts = line.split('=')
                if len(parts) < 2:
                    continue
                
                content = parts[1].strip().strip('";')
                values = content.split(',')
                
                if len(values) < 10:
                    continue
                
                symbol = symbols[i] if i < len(symbols) else unique_normalized[i]
                results[symbol] = {
                    'symbol': symbol,
                    'name': values[0],
                    'price': float(values[3]) if values[3] else 0,
                    'change': float(values[3]) - float(values[2]) if len(values) > 3 and values[2] else 0,
                    'change_percent': 0,
                    'volume': int(float(values[8])) if len(values) > 8 and values[8] else 0,
                    'source': 'sina'
                }
                
                # 计算涨跌幅
                if len(values) > 2 and values[2] and float(values[2]) > 0:
                    change = float(values[3]) - float(values[2])
                    results[symbol]['change'] = round(change, 2)
                    results[symbol]['change_percent'] = round(change / float(values[2]) * 100, 2)
            
            return {
                'results': results,
                'count': len(results),
                'source': 'sina'
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'results': {}
            }
    
    def get_market_overview(self) -> Dict[str, Any]:
        """
        获取市场概览 (上证、深证指数)
        
        Returns:
            市场指数数据
        """
        self._ensure_available()
        
        # 上证指数和深证指数
        return self.get_quote(['000001.SZ', '399001.SZ'])
    
    def search_stock(self, keyword: str) -> Dict[str, Any]:
        """
        搜索股票
        
        Args:
            keyword: 搜索关键词 (股票名称或代码)
        
        Returns:
            搜索结果列表
        """
        # 新浪搜索API
        self._ensure_available()
        
        try:
            url = f"https://suggest3.sinajs.cn/suggest/type=11,12,13,14,15,16,17,18,19,20&key={keyword}"
            response = self._session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.text.strip()
            
            # 格式: var suggest_result="name,code,type;name,code,type;...";
            if '=' not in data:
                return {'error': '搜索结果格式异常', 'results': []}
            
            content = data.split('=')[1].strip().strip('";')
            items = content.split(';')
            
            results = []
            for item in items:
                parts = item.split(',')
                if len(parts) >= 3:
                    results.append({
                        'name': parts[0],
                        'code': parts[2],
                        'type': parts[1] if len(parts) > 1 else ''
                    })
            
            return {
                'results': results[:20],  # 限制20条
                'keyword': keyword,
                'source': 'sina'
            }
            
        except Exception as e:
            return {'error': str(e), 'results': []}
    
    # 兼容现有接口 - 返回错误表示不可用
    def get_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """基本面数据 - 新浪实时数据不包含，此处返回空"""
        return {
            'error': 'Sina实时数据不包含基本面，请使用get_stock_data获取行情',
            'symbol': symbol
        }
    
    def get_balance_sheet(self, symbol: str, freq: str = "quarterly") -> Dict[str, Any]:
        """资产负债表 - 不支持"""
        return {'error': '不支持资产负债表查询，请使用其他数据源', 'symbol': symbol}
    
    def get_income_statement(self, symbol: str, freq: str = "quarterly") -> Dict[str, Any]:
        """利润表 - 不支持"""
        return {'error': '不支持利润表查询，请使用其他数据源', 'symbol': symbol}
    
    def get_cashflow(self, symbol: str, freq: str = "quarterly") -> Dict[str, Any]:
        """现金流量表 - 不支持"""
        return {'error': '不支持现金流量表查询，请使用其他数据源', 'symbol': symbol}
    
    def get_indicators(self, symbol: str, indicators: List[str], period: str = "6mo", **kwargs) -> Dict[str, Any]:
        """技术指标 - 不支持"""
        return {'error': '不支持技术指标计算，请使用get_stock_data获取K线数据', 'symbol': symbol}
    
    def get_news(self, symbol: str, limit: int = 10) -> Dict[str, Any]:
        """新闻 - 不支持"""
        return {'error': '不支持新闻查询，请使用其他数据源', 'symbol': symbol}
    
    def get_global_news(self, limit: int = 20) -> Dict[str, Any]:
        """全球新闻 - 不支持"""
        return {'error': '不支持新闻查询，请使用其他数据源'}
    
    def get_insider_transactions(self, symbol: str) -> Dict[str, Any]:
        """内部人交易 - 不支持"""
        return {'error': '不支持内部人交易查询', 'symbol': symbol}
