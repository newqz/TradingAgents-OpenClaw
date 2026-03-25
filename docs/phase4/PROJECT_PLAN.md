# Phase 4: Multi-Market Integration Plan

## Overview
Extend TradingAgents-OpenClaw to support A-shares and cryptocurrency markets, integrating ClawHub skills for comprehensive market coverage.

## Target Markets
- A-shares (China)
- Cryptocurrency (BTC, ETH, etc.)
- Social media sentiment (Weibo)

## Skills to Integrate

### Priority 1: eastmoney-stock (Phase 4a)
- **Source**: ClawHub
- **Purpose**: Real-time A-share data from Eastmoney
- **Status**: v1.0.0 ✅
- **Timeline**: Week 1-2
- **Integration**: Python adapter → DataProvider

### Priority 2: crypto-trader (Phase 4b)
- **Source**: ClawHub
- **Purpose**: Crypto trading strategies + sentiment analysis
- **Status**: v1.0.0 ✅
- **Timeline**: Week 3-4
- **Integration**: Sentiment module integration

### Priority 3: weibo-trending (Phase 4c)
- **Source**: ClawHub
- **Purpose**: Weibo hot search data
- **Status**: v1.0.0 ✅
- **Timeline**: Week 5-6
- **Integration**: Social sentiment pipeline

### Priority 4: crypto-market-data (Phase 4d)
- **Source**: ClawHub
- **Purpose**: Real-time crypto prices
- **Status**: v1.0.2 ✅
- **Timeline**: Week 7+
- **Integration**: Node.js bridge or Python rewrite

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Phase 4 Architecture                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Phase 1-3 Core Engine                    │   │
│  │  Research Agent → Debate → Trading → Risk            │   │
│  └──────────────────────┬───────────────────────────────┘   │
│                         │                                    │
│  ┌──────────────────────▼───────────────────────────────┐   │
│  │              DataProviderRegistry                     │   │
│  │                                                       │   │
│  │  register("a_stock", EastMoneyAdapter)               │   │
│  │  register("a_stock", TushareAdapter)     # fallback   │   │
│  │  register("crypto", CryptoTraderAdapter)              │   │
│  │  register("social", WeiboAdapter)                    │   │
│  └──────────────────────┬───────────────────────────────┘   │
│                         │                                    │
│  ┌──────────────────────▼───────────────────────────────┐   │
│  │              Data Adapter Layer                       │   │
│  │                                                       │   │
│  │  EastMoneyAdapter  │  CryptoTraderAdapter            │   │
│  │  WeiboAdapter      │  TushareAdapter (existing)      │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Data Schema

```python
@dataclass
class MarketSignal:
    source: str           # "eastmoney" | "crypto_trader" | "weibo"
    signal_type: str      # "price" | "sentiment" | "trend"
    asset_id: str         # "SH600519" | "BTC-USDT"
    timestamp: datetime
    payload: dict         # Standardized data
    confidence: float     # 0.0 - 1.0
```

## Development Guidelines

1. **Frequent commits**: Commit after each small milestone
2. **Document everything**: Save progress in docs/phase4/
3. **Test after each integration**: Verify data flows correctly
4. **Graceful degradation**: If one source fails, fallback to others

## Progress Tracking

| Phase | Skill | Status | Start Date | End Date | Notes |
|-------|-------|--------|------------|----------|-------|
| 4a | eastmoney-stock | 🔄 In Progress | 2026-03-25 | - | - |
| 4b | crypto-trader | ⏳ Pending | - | - | - |
| 4c | weibo-trending | ⏳ Pending | - | - | - |
| 4d | crypto-market-data | ⏳ Pending | - | - | - |
