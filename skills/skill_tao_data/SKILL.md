# Skill: skill-tao-data

## 描述

TradingAgents-OpenClaw 数据层 Skill，提供统一的股票数据获取接口。支持多供应商（Yahoo Finance、Alpha Vantage）自动故障转移，内置缓存机制。

## 功能

- 股票价格数据 (OHLCV)
- 财务报表数据 (资产负债表、利润表、现金流量表)
- 技术指标数据 (RSI、MACD、布林带等)
- 新闻数据
- 内部人交易数据

## 支持的数据源

| 数据源 | 类型 | 优先级 |
|--------|------|--------|
| Yahoo Finance | 免费 | 默认首选 |
| Alpha Vantage | 免费+付费 | 备用 |

## 使用方法

### 作为 Skill 调用

```python
from tradingagents.data import DataProvider

provider = DataProvider()

# 获取股票数据
data = provider.get_stock_data("AAPL", period="1y")

# 获取财务数据
fundamentals = provider.get_fundamentals("TSLA")

# 获取技术指标
indicators = provider.get_indicators("NVDA", indicators=["rsi", "macd"])
```

### 直接命令行使用

```bash
# 获取股票基本信息
python -m skill_tao_data get_stock_data --symbol AAPL

# 获取财务数据
python -m skill_tao_data get_fundamentals --symbol TSLA

# 获取技术指标
python -m skill_tao_data get_indicators --symbol NVDA --indicators rsi,macd
```

## 配置

```yaml
# config.yaml
data_vendors:
  core_stock: "yfinance"        # 或 alpha_vantage
  technical: "yfinance"
  fundamental: "yfinance"
  news: "yfinance"

cache:
  enabled: true
  ttl_minutes: 60
  redis_url: "redis://localhost:6379/0"
```

## API

### get_stock_data(symbol, period, interval)
获取股票历史价格数据

### get_fundamentals(symbol)
获取公司基本面数据

### get_balance_sheet(symbol, freq)
获取资产负债表

### get_income_statement(symbol, freq)
获取利润表

### get_cashflow(symbol, freq)
获取现金流量表

### get_indicators(symbol, indicators, period)
获取技术指标

### get_news(symbol, limit)
获取新闻数据

## 错误处理

- 自动故障转移到备用数据源
- 缓存回退机制
- 详细的错误日志

## 依赖

- yfinance
- alpha-vantage
- pandas
- redis (可选，用于缓存)
