"""中国社交媒体舆情数据客户端
支持: 知乎, B站, 微博, 贴吧
"""

import re
import time
import logging
from typing import Any, Dict, List, Optional

try:
    import requests
except ImportError:
    requests = None

from .base import BaseVendor

logger = logging.getLogger(__name__)


class ChinaSocialClient(BaseVendor):
    """中国社交媒体舆情数据客户端"""
    
    def __init__(self, timeout: int = 15):
        self._timeout = timeout
        self._session = requests.Session() if requests else None
        self._headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
    
    def _make_request(self, url: str, params: Dict = None, headers: Dict = None) -> Optional[Dict]:
        if not requests:
            logger.warning("requests library not installed")
            return None
        try:
            merged_headers = {**self._headers, **(headers or {})}
            resp = self._session.get(url, params=params, headers=merged_headers, timeout=self._timeout)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.warning(f"Request failed: {e}")
            return None
    
    # ==================== 实现抽象方法 ====================
    
    def get_stock_data(self, symbol: str, period: str = "1y", interval: str = "1d", 
                       start: Optional[str] = None, end: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        return {"error": "Social media client does not support stock data", "source": "china_social"}
    
    def get_indicators(self, symbol: str, indicators: List[str] = None, 
                       period: str = "6mo", **kwargs) -> Dict[str, Any]:
        return {"error": "Social media client does not support indicators", "source": "china_social"}
    
    def get_fundamentals(self, symbol: str, period: str = "annual", **kwargs) -> Dict[str, Any]:
        return {"error": "Not supported", "source": "china_social"}
    
    def get_balance_sheet(self, symbol: str, period: str = "annual", **kwargs) -> Dict[str, Any]:
        return {"error": "Not supported", "source": "china_social"}
    
    def get_cashflow(self, symbol: str, period: str = "annual", **kwargs) -> Dict[str, Any]:
        return {"error": "Not supported", "source": "china_social"}
    
    def get_income_statement(self, symbol: str, period: str = "annual", **kwargs) -> Dict[str, Any]:
        return {"error": "Not supported", "source": "china_social"}
    
    def get_news(self, symbol: str, limit: int = 10, **kwargs) -> Dict[str, Any]:
        return self.search_zhihu(symbol, limit)
    
    def get_global_news(self, limit: int = 20, **kwargs) -> Dict[str, Any]:
        return self.get_market_sentiment()
    
    def get_insider_transactions(self, symbol: str, **kwargs) -> Dict[str, Any]:
        return {"error": "Not supported", "source": "china_social"}
    
    # ==================== 知乎 (Zhihu) ====================
    
    def get_zhihu_hot(self, limit: int = 10) -> Dict[str, Any]:
        url = "https://www.zhihu.com/api/v3/hot/topics"
        data = self._make_request(url)
        if not data or "data" not in data:
            return {"source": "zhihu", "hot_list": [], "error": "Failed to fetch"}
        hot_list = []
        for item in data["data"][:limit]:
            hot_list.append({
                "title": item.get("title", ""),
                "url": f"https://www.zhihu.com/topic/{item.get('id', '')}",
                "heat": item.get("heat", ""),
            })
        return {"source": "zhihu", "hot_list": hot_list}
    
    def search_zhihu(self, keyword: str, limit: int = 10) -> Dict[str, Any]:
        url = "https://www.zhihu.com/api/v4/search_v3"
        params = {"q": keyword, "type": "topic", "limit": limit, "offset": 0}
        data = self._make_request(url, params=params)
        if not data or "data" not in data:
            return {"source": "zhihu", "results": [], "error": "Failed to search"}
        results = []
        for item in data.get("data", []):
            results.append({"title": item.get("title", ""), "url": item.get("url", "")})
        return {"source": "zhihu", "keyword": keyword, "results": results}
    
    # ==================== B站 (Bilibili) ====================
    
    def get_bilibili_hot(self, limit: int = 10) -> Dict[str, Any]:
        url = "https://api.bilibili.com/x/web-interface/ranking/v2"
        params = {"type": "all", "ps": limit}
        data = self._make_request(url, params=params)
        if not data or "data" not in data:
            return {"source": "bilibili", "hot_list": [], "error": "Failed to fetch"}
        hot_list = []
        for item in data["data"]["list"][:limit]:
            hot_list.append({
                "title": item.get("title", ""),
                "url": f"https://www.bilibili.com/video/{item.get('bvid', '')}",
                "author": item.get("owner", {}).get("name", ""),
                "views": item.get("stat", {}).get("view", 0),
            })
        return {"source": "bilibili", "hot_list": hot_list}
    
    def get_bilibili_comments(self, bvid: str, limit: int = 20) -> Dict[str, Any]:
        url = "https://api.bilibili.com/x/v2/reply"
        params = {"type": "video", "oid": bvid, "pn": 1, "ps": limit, "sort": 2}
        data = self._make_request(url, params=params)
        if not data or "data" not in data:
            return {"source": "bilibili", "comments": [], "error": "Failed to fetch"}
        comments = []
        for item in data["data"].get("replies", [])[:limit]:
            if item:
                comments.append({"user": item.get("member", {}).get("uname", ""), "content": item.get("content", {}).get("message", ""), "likes": item.get("like", 0)})
        return {"source": "bilibili", "bvid": bvid, "comments": comments}
    
    def search_bilibili(self, keyword: str, limit: int = 10) -> Dict[str, Any]:
        url = "https://api.bilibili.com/x/web-interface/search/all/v2"
        params = {"keyword": keyword, "page": 1, "page_size": limit}
        data = self._make_request(url, params=params)
        if not data or "data" not in data:
            return {"source": "bilibili", "results": [], "error": "Failed to search"}
        results = []
        for item in data["data"].get("result", [])[:limit]:
            results.append({"title": item.get("title", "").replace("<em class=\"keyword\">", "").replace("</em>", ""), "url": f"https://www.bilibili.com/video/{item.get('bvid', '')}"})
        return {"source": "bilibili", "keyword": keyword, "results": results}
    
    # ==================== 微博 (Weibo) ====================
    
    def get_weibo_hot(self, limit: int = 20) -> Dict[str, Any]:
        url = "https://weibo.com/ajax/side/hotSearch"
        data = self._make_request(url)
        if not data or "data" not in data:
            return {"source": "weibo", "hot_list": [], "error": "Failed to fetch"}
        hot_list = []
        for item in data["data"]["realtime"][:limit]:
            hot_list.append({"word": item.get("word", ""), "url": f"https://s.weibo.com/weibo?q={item.get('word', '')}", "num": item.get("num", 0), "label": item.get("label_name", "")})
        return {"source": "weibo", "hot_list": hot_list}
    
    def search_weibo(self, keyword: str, limit: int = 10) -> Dict[str, Any]:
        url = "https://weibo.com/ajax/search"
        params = {"q": keyword, "xsort": "hot", "suball": 1}
        data = self._make_request(url, params=params)
        if not data or "data" not in data:
            return {"source": "weibo", "results": [], "error": "Failed to search"}
        results = []
        for item in data["data"].get("statuses", [])[:limit]:
            results.append({"text": item.get("text_raw", ""), "user": item.get("user", {}).get("screen_name", ""), "reposts": item.get("reposts_count", 0), "comments": item.get("comments_count", 0)})
        return {"source": "weibo", "keyword": keyword, "results": results}
    
    # ==================== 贴吧 (Tieba) ====================
    
    def search_tieba(self, keyword: str, limit: int = 10) -> Dict[str, Any]:
        url = "https://tieba.baidu.com/f/search/res"
        params = {"ie": "utf-8", "kw": keyword, "sm": 1, "rn": limit}
        data = self._make_request(url, params=params)
        if not data:
            return {"source": "tieba", "results": [], "error": "Failed to search"}
        results = []
        if "data" in data:
            for item in data["data"].get("forum_list", [])[:limit]:
                results.append({"title": item.get("title", ""), "forum_name": item.get("fname", ""), "url": f"https://tieba.baidu.com{item.get('url', '')}"})
        return {"source": "tieba", "keyword": keyword, "results": results}
    
    # ==================== 统一舆情接口 ====================
    
    def get_social_sentiment(self, keyword: str, platforms: List[str] = None) -> Dict[str, Any]:
        if platforms is None:
            platforms = ["zhihu", "bilibili", "weibo", "tieba"]
        results = {"keyword": keyword, "platforms": {}}
        for platform in platforms:
            try:
                if platform == "zhihu":
                    results["platforms"]["zhihu"] = self.search_zhihu(keyword, limit=5)
                elif platform == "bilibili":
                    results["platforms"]["bilibili"] = self.search_bilibili(keyword, limit=5)
                elif platform == "weibo":
                    results["platforms"]["weibo"] = self.search_weibo(keyword, limit=5)
                elif platform == "tieba":
                    results["platforms"]["tieba"] = self.search_tieba(keyword, limit=5)
                time.sleep(0.3)
            except Exception as e:
                logger.warning(f"Failed to get {platform} data: {e}")
                results["platforms"][platform] = {"error": str(e)}
        return results
    
    def get_market_sentiment(self) -> Dict[str, Any]:
        sentiment = {"timestamp": time.time(), "sources": {}}
        sentiment["sources"]["zhihu"] = self.get_zhihu_hot(limit=5)
        sentiment["sources"]["weibo"] = self.get_weibo_hot(limit=10)
        sentiment["sources"]["bilibili"] = self.get_bilibili_hot(limit=5)
        return sentiment
