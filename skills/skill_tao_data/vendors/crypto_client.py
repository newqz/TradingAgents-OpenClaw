"""
CryptoMarketClient - Cryptocurrency Market Data Vendor

Uses free public APIs:
- CoinGecko (primary, no API key required)
- Binance (backup for real-time data)

Supports:
- Real-time prices
- K-line/candlestick data
- Market overview
- Trend coins
- Global market data
"""

import sys
import os
import json
import time
from typing import Dict, List, Any, Optional

# Try to import requests
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class CryptoMarketClient:
    """Cryptocurrency market data client using CoinGecko and Binance APIs."""
    
    def __init__(self, api_key: str = None):
        """
        Initialize CryptoMarketClient.
        
        Args:
            api_key: Optional API key (not required for CoinGecko free tier)
        """
        self.api_key = api_key
        self._session = None
        
        # CoinGecko API (free, no key required)
        self.coingecko_base = "https://api.coingecko.com/api/v3"
        
        # Binance API (free, no key required for public endpoints)
        self.binance_base = "https://api.binance.com/api/v3"
        
        if HAS_REQUESTS:
            self._session = requests.Session()
            self._session.headers.update({
                "Accept": "application/json",
                "User-Agent": "TradingAgents-OpenClaw/1.0"
            })
    
    def _make_request(self, url: str, params: Dict = None) -> Dict[str, Any]:
        """Make HTTP request with error handling."""
        if not HAS_REQUESTS:
            return {"error": "requests library not installed. Run: pip install requests"}
        
        try:
            response = self._session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
        except json.JSONDecodeError:
            return {"error": "Invalid JSON response"}
    
    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize crypto symbol (e.g., btc -> bitcoin)."""
        symbol = symbol.lower().strip()
        
        # Common symbol mappings
        symbol_map = {
            "btc": "bitcoin",
            "eth": "ethereum",
            "bnb": "binancecoin",
            "xrp": "ripple",
            "ada": "cardano",
            "doge": "dogecoin",
            "sol": "solana",
            "dot": "polkadot",
            "matic": "matic-network",
            "shib": "shiba-inu",
            "avax": "avalanche-2",
            "link": "chainlink",
            "uni": "uniswap",
            "atom": "cosmos",
            "ltc": "litecoin",
        }
        
        return symbol_map.get(symbol, symbol)
    
    # ============ Core Market Data ============
    
    def get_stock_data(self, symbol: str, period: str = "7d", 
                      interval: str = "daily", **kwargs) -> Dict[str, Any]:
        """
        Get cryptocurrency price data.
        
        Args:
            symbol: Crypto symbol (e.g., btc, eth)
            period: Time period (1d, 7d, 30d, 90d, 1y, etc.)
            interval: Data interval (minutely, hourly, daily)
        
        Returns:
            Dict with price data
        """
        if not HAS_REQUESTS:
            return {"error": "requests library not installed"}
        
        coin_id = self._normalize_symbol(symbol)
        
        # Map period to days
        days_map = {"1d": 1, "7d": 7, "30d": 30, "90d": 90, "1y": 365, "all": "max"}
        days = days_map.get(period, 7)
        
        url = f"{self.coingecko_base}/coins/{coin_id}/market_chart"
        params = {
            "vs_currency": "usd",
            "days": days,
            "interval": interval if days == 1 else "daily"
        }
        
        result = self._make_request(url, params)
        
        if "error" in result:
            return result
        
        # Parse price data
        prices = result.get("prices", [])
        if not prices:
            return {"error": f"No data found for {symbol}"}
        
        # Calculate stats
        price_values = [p[1] for p in prices]
        current_price = price_values[-1] if price_values else 0
        start_price = price_values[0] if price_values else 0
        change = current_price - start_price
        change_pct = (change / start_price * 100) if start_price else 0
        
        return {
            "symbol": symbol.upper(),
            "name": coin_id.capitalize(),
            "price": current_price,
            "change": change,
            "change_percent": change_pct,
            "period": period,
            "interval": interval,
            "data_points": len(prices),
            "provider": "coingecko",
            "prices": prices[-30:]  # Last 30 data points
        }
    
    def get_quote(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Get quotes for multiple cryptocurrencies.
        
        Args:
            symbols: List of crypto symbols (e.g., ["btc", "eth", "sol"])
        
        Returns:
            Dict with quotes for each symbol
        """
        if not HAS_REQUESTS:
            return {"error": "requests library not installed"}
        
        coin_ids = [self._normalize_symbol(s) for s in symbols]
        
        url = f"{self.coingecko_base}/simple/price"
        params = {
            "ids": ",".join(coin_ids),
            "vs_currencies": "usd",
            "include_24hr_change": "true",
            "include_last_updated_at": "true"
        }
        
        result = self._make_request(url, params)
        
        if "error" in result:
            return result
        
        quotes = {}
        for symbol, coin_id in zip(symbols, coin_ids):
            if coin_id in result:
                data = result[coin_id]
                price_data = data.get("usd", {})
                quotes[symbol.upper()] = {
                    "symbol": symbol.upper(),
                    "price": price_data if isinstance(price_data, (int, float)) else price_data.get("usd", 0),
                    "change_24h": data.get("usd_24h_change", 0),
                    "last_updated": data.get("last_updated_at", 0),
                    "provider": "coingecko"
                }
            else:
                quotes[symbol.upper()] = {"error": f"Symbol {symbol} not found"}
        
        return {"results": quotes}
    
    def get_market_overview(self) -> Dict[str, Any]:
        """
        Get global cryptocurrency market overview.
        
        Returns:
            Dict with global market data
        """
        if not HAS_REQUESTS:
            return {"error": "requests library not installed"}
        
        url = f"{self.coingecko_base}/global"
        result = self._make_request(url)
        
        if "error" in result:
            return result
        
        data = result.get("data", {})
        
        return {
            "total_market_cap": data.get("total_market_cap", {}).get("usd", 0),
            "total_volume_24h": data.get("total_volume", {}).get("usd", 0),
            "btc_dominance": data.get("market_cap_percentage", {}).get("btc", 0),
            "eth_dominance": data.get("market_cap_percentage", {}).get("eth", 0),
            "active_cryptocurrencies": data.get("active_cryptocurrencies", 0),
            "market_change_24h": data.get("market_cap_change_percentage_24h_usd", 0),
            "provider": "coingecko"
        }
    
    def get_trending_coins(self) -> Dict[str, Any]:
        """
        Get trending cryptocurrencies.
        
        Returns:
            Dict with trending coins
        """
        if not HAS_REQUESTS:
            return {"error": "requests library not installed"}
        
        url = f"{self.coingecko_base}/search/trending"
        result = self._make_request(url)
        
        if "error" in result:
            return result
        
        coins = result.get("coins", [])
        trending = []
        
        for item in coins[:10]:  # Top 10
            coin = item.get("item", {})
            trending.append({
                "id": coin.get("id", ""),
                "symbol": coin.get("symbol", "").upper(),
                "name": coin.get("name", ""),
                "market_cap_rank": coin.get("market_cap_rank", 0),
                "price_btc": coin.get("price_btc", 0),
                "score": coin.get("score", 0)
            })
        
        return {"trending": trending, "provider": "coingecko"}
    
    # ============ Binance Integration (Backup) ============
    
    def get_binance_klines(self, symbol: str, interval: str = "1d", 
                          limit: int = 100) -> Dict[str, Any]:
        """
        Get candlestick data from Binance.
        
        Args:
            symbol: Trading pair (e.g., "BTCUSDT")
            interval: Kline interval (1m, 5m, 15m, 1h, 4h, 1d)
            limit: Number of klines to return (max 1000)
        
        Returns:
            Dict with kline data
        """
        if not HAS_REQUESTS:
            return {"error": "requests library not installed"}
        
        symbol = symbol.upper()
        
        url = f"{self.binance_base}/klines"
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": min(limit, 1000)
        }
        
        result = self._make_request(url, params)
        
        if "error" in result:
            return result
        
        # Parse klines
        klines = []
        for k in result:
            klines.append({
                "open_time": k[0],
                "open": float(k[1]),
                "high": float(k[2]),
                "low": float(k[3]),
                "close": float(k[4]),
                "volume": float(k[5]),
                "close_time": k[6],
                "quote_volume": float(k[7])
            })
        
        return {
            "symbol": symbol,
            "interval": interval,
            "klines": klines,
            "provider": "binance"
        }
    
    def get_binance_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Get 24hr ticker statistics from Binance.
        
        Args:
            symbol: Trading pair (e.g., "BTCUSDT")
        
        Returns:
            Dict with ticker data
        """
        if not HAS_REQUESTS:
            return {"error": "requests library not installed"}
        
        symbol = symbol.upper()
        
        url = f"{self.binance_base}/ticker/24hr"
        params = {"symbol": symbol}
        
        result = self._make_request(url, params)
        
        if "error" in result:
            return result
        
        return {
            "symbol": result.get("symbol", symbol),
            "last_price": float(result.get("lastPrice", 0)),
            "price_change": float(result.get("priceChange", 0)),
            "price_change_percent": float(result.get("priceChangePercent", 0)),
            "high_24h": float(result.get("highPrice", 0)),
            "low_24h": float(result.get("lowPrice", 0)),
            "volume_24h": float(result.get("volume", 0)),
            "quote_volume_24h": float(result.get("quoteVolume", 0)),
            "provider": "binance"
        }
    
    # ============ Search ============
    
    def search_coin(self, query: str) -> Dict[str, Any]:
        """
        Search for cryptocurrencies by name or symbol.
        
        Args:
            query: Search query
        
        Returns:
            Dict with search results
        """
        if not HAS_REQUESTS:
            return {"error": "requests library not installed"}
        
        url = f"{self.coingecko_base}/search"
        params = {"query": query}
        
        result = self._make_request(url, params)
        
        if "error" in result:
            return result
        
        coins = result.get("coins", [])
        return {
            "results": [
                {
                    "id": c.get("id", ""),
                    "symbol": c.get("symbol", "").upper(),
                    "name": c.get("name", ""),
                    "market_cap_rank": c.get("market_cap_rank", 0),
                    "thumb": c.get("thumb", "")
                }
                for c in coins[:20]  # Top 20 results
            ],
            "provider": "coingecko"
        }
    
    def __del__(self):
        """Cleanup session."""
        if self._session:
            self._session.close()
