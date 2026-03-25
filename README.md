# TradingAgents-OpenClaw

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Pydantic-1.9+-green.svg" alt="Pydantic">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
</p>

> **AI-Powered Multi-Agent Trading Research System**
> 多智能体AI驱动的交易研究系统

## Overview | 概述

TradingAgents-OpenClaw is a multi-agent AI trading research system that simulates a team of analysts, researchers, and traders making investment decisions together.

TradingAgents-OpenClaw 是一个多智能体AI交易研究系统，模拟分析师、研究员和交易员团队共同做出投资决策。

### Architecture | 架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        Phase 1: 三分析师并行                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   基本面     │  │   技术面     │  │   情绪面     │         │
│  │ Fundamental  │  │  Technical   │  │  Sentiment   │         │
│  │  Analyst     │  │  Analyst     │  │  Analyst     │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         └──────────────────┼──────────────────┘                 │
│                            ▼                                    │
│                        Phase 2: 多空研究员辩论                    │
│         ┌─────────────────┴─────────────────┐                  │
│         │     Bull Researcher (多头)          │                  │
│         │     Bear Researcher (空头)          │                  │
│         └─────────────────┬─────────────────┘                  │
│                           ▼                                      │
│                      Research Manager                           │
│                      (研究整合)                                  │
│                           ▼                                      │
│                        Phase 3: 交易员辩论                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Bull Trader │  │ Neutral Trader│  │ Bear Trader │         │
│  │   (多头交易)  │  │  (中性交易)  │  │  (空头交易)  │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         └──────────────────┼──────────────────┘                 │
│                            ▼                                    │
│                    Risk Manager (风险管理)                        │
│                            ▼                                    │
│                   Portfolio Manager (组合经理)                    │
│                            ▼                                    │
│                      Trade Decision                             │
│                      (最终交易决策)                              │
└─────────────────────────────────────────────────────────────────┘
```

## Features | 功能

### ✅ Completed | 已完成

- **Multi-Agent Debate System** - Bull/Bear researcher debate mechanism
- **Three-Phase Pipeline** - Analyst → Researcher → Trader workflow
- **Risk Management** - Four-level risk assessment framework
- **Multi-Source Data** - YFinance, Finnhub, TuShare, Sina, CoinGecko, Binance
- **Thread-Safe Cache** - LRU cache with TTL expiration
- **JSON Safety** - Robust JSON parsing with validation
- **State Machine** - Validated state transitions
- **Logging System** - Colored console + file logging
- **Unit Tests** - Core functionality test coverage

## Quick Start | 快速开始

### Prerequisites | 前置要求

- Python 3.8+
- pip or pipenv

### Installation | 安装

```bash
# Clone the repository
git clone https://github.com/newqz/TradingAgents-OpenClaw.git
cd TradingAgents-OpenClaw

# Install in development mode
pip install -e .

# Or install dependencies only
pip install -r requirements.txt
```

### Configuration | 配置

#### Required | 必需

| Variable | Description | 中文说明 |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for LLM | OpenAI API密钥 |
| `ANTHROPIC_API_KEY` | Anthropic API key (alternative) | Anthropic API密钥(备选) |

```bash
# Option 1: Export environment variable
export OPENAI_API_KEY=sk-your-key-here

# Option 2: Create .env file (not committed to git)
echo "OPENAI_API_KEY=sk-your-key-here" > .env
```

#### Optional Data Sources | 可选数据源

| Variable | Description | Data Coverage | 中文说明 |
|----------|-------------|---------------|----------|
| `FINNHUB_API_KEY` | Finnhub API key | US stocks, news | 美股新闻+指标 |
| `TUSHARE_TOKEN` | TuShare token | China A-shares | A股财务数据 |
| `ALPHA_VANTAGE_API_KEY` | AlphaVantage key | US stocks, forex | 美股+外汇 |

> **Note**: These are optional. The system falls back to free data sources (YFinance, Sina Stock) when not configured.

### Running | 运行

```bash
# Run Phase 3 full pipeline
python3 -m master_agent.orchestrator_phase3

# Run with specific stock
python3 -m master_agent.orchestrator_phase3 --symbol NVDA

# Run tests
python3 test_phase3.py
```

## Project Structure | 项目结构

```
TradingAgents-OpenClaw/
├── master_agent/              # Main orchestration agents
│   ├── orchestrator_phase3.py  # Phase 3 orchestrator
│   ├── portfolio_manager.py    # Portfolio management
│   └── trader_debate_orchestrator.py
├── shared/                    # Shared modules
│   ├── models.py              # Pydantic data models
│   ├── json_utils.py          # JSON parsing utilities
│   ├── state_machine.py       # State machine validation
│   ├── interfaces.py          # Abstract base classes
│   └── logging_config.py      # Logging configuration
├── skills/                    # Agent skills
│   ├── skill_tao_fundamental/ # Fundamental analyst
│   ├── skill_tao_technical/   # Technical analyst
│   ├── skill_tao_sentiment/   # Sentiment analyst
│   ├── skill_tao_researcher_bull/
│   ├── skill_tao_researcher_bear/
│   ├── skill_tao_research_manager/
│   ├── skill_tao_risk_manager/
│   ├── skill_tao_trader/
│   └── skill_tao_data/        # Data provider
│       └── vendors/           # Data source adapters
│           ├── yfinance_client.py
│           ├── finnhub_client.py
│           ├── tushare_client.py
│           ├── sina_stock_client.py
│           └── crypto_client.py
├── tests/                    # Unit tests
├── pyproject.toml            # Package configuration
└── README.md                 # This file
```

## Data Flow | 数据流

```
1. User Input (symbol, command)
        ↓
2. Data Collection (multi-source fallback)
   YFinance → Finnhub → AlphaVantage
        ↓
3. Parallel Analysis (Phase 1)
   Fundamental + Technical + Sentiment
        ↓
4. Researcher Debate (Phase 2)
   Bull vs Bear → Research Manager
        ↓
5. Trader Debate (Phase 3)
   Bull/Neutral/Bear → Risk Manager
        ↓
6. Final Decision
   Portfolio Manager → Trade Decision
        ↓
7. Output (Feishu notification, etc.)
```

## Configuration Points | 配置项说明

### 1. LLM Configuration | LLM配置

Edit `shared/config.py` or set environment variables:

```python
# Model selection
DEEP_THINK_LLM = {
    "provider": "openai",      # or "anthropic"
    "model": "gpt-4o",        # or "claude-opus-4.6"
    "temperature": 0.7
}

QUICK_THINK_LLM = {
    "provider": "openai",
    "model": "gpt-4o-mini",
    "temperature": 0.5
}
```

### 2. Data Source Priority | 数据源优先级

Configure in `skills/skill_tao_data/data_provider.py`:

```python
VENDOR_LIST = [
    "yfinance",      # Default: free, global
    "alpha_vantage", # US stocks + forex
    "finnhub",       # US stocks + news
    "tushare",       # China A-shares
    "china_stock",   # China stocks (Sina)
    "sina_stock",    # China stocks (Sina backup)
    "crypto"         # Crypto (CoinGecko + Binance)
]
```

### 3. Risk Management | 风险管理

Configure in `master_agent/portfolio_manager.py`:

```python
# Risk level thresholds
RISK_THRESHOLDS = {
    "extreme": 80,   # Max 5% position
    "high": 60,      # Max 10% position
    "medium": 40,    # Max 20% position
    "low": 20       # Max 30% position
}

# Maximum position size
MAX_POSITION_PCT = {
    "extreme": 0.05,
    "high": 0.10,
    "medium": 0.20,
    "low": 0.30
}
```

### 4. Cache Configuration | 缓存配置

Configure in `skills/skill_tao_data/data_provider.py`:

```python
CacheManager(
    enabled=True,
    ttl_minutes=60,     # Cache expiration
    maxsize=10000       # Max cache entries (LRU eviction)
)
```

### 5. Debate Configuration | 辩论配置

Configure in `master_agent/orchestrator_phase3.py`:

```python
config = TAOConfig(
    max_debate_rounds=3,    # Max debate rounds
    enable_risk_management=True,
    confidence_threshold=0.6
)
```

## API Keys Setup | API密钥设置

### OpenAI | 开放AI

1. Visit [OpenAI API](https://platform.openai.com/api-keys)
2. Create a new API key
3. Export: `export OPENAI_API_KEY=sk-...`

### Anthropic | Anthropic

1. Visit [Anthropic Console](https://console.anthropic.com/)
2. Create a new API key
3. Export: `export ANTHROPIC_API_KEY=sk-ant-...`

### Finnhub | 金融中心

1. Visit [Finnhub](https://finnhub.io/)
2. Register for free API key
3. Export: `export FINNHUB_API_KEY=your_key`

### TuShare | Tushare

1. Visit [TuShare](https://tushare.pro/)
2. Register and get token
3. Export: `export TUSHARE_TOKEN=your_token`

## Deployment | 部署

### Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY . /app

RUN pip install -e .

ENV OPENAI_API_KEY=${OPENAI_API_KEY}
ENV FINNHUB_API_KEY=${FINNHUB_API_KEY}

CMD ["python3", "-m", "master_agent.orchestrator_phase3"]
```

### Build and run

```bash
docker build -t tradingagents .
docker run -e OPENAI_API_KEY=sk-... tradingagents
```

### Docker Compose

```yaml
version: '3.8'
services:
  tradingagents:
    build: .
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - FINNHUB_API_KEY=${FINNHUB_API_KEY}
    volumes:
      - ./data:/app/data
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tradingagents
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: tradingagents
        image: tradingagents:latest
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: tradingagents-secrets
              key: openai-api-key
```

## Testing | 测试

```bash
# Run all tests
python3 test_phase3.py

# Run specific test
python3 -c "
from bootstrap import setup
setup()
from shared.json_utils import safe_json_parse
print(safe_json_parse('{\"test\": true}'))
"

# Run pytest (if installed)
pip install pytest
pytest tests/ -v
```

## Troubleshooting | 故障排除

### ImportError: No module named 'shared'

```bash
# Run from project root
cd /root/.openclaw/workspace/TradingAgents-OpenClaw
python3 -m master_agent.orchestrator_phase3

# Or install the package
pip install -e .
```

### JSON Parse Errors

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Cache Issues

Clear cache:
```python
from skills.skill_tao_data.data_provider import CacheManager
cache = CacheManager(enabled=True)
cache.clear()
```

## Contributing | 贡献

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

## License | 许可证

MIT License - see [LICENSE](LICENSE) file.

## Contact | 联系方式

- GitHub Issues: [newqz/TradingAgents-OpenClaw](https://github.com/newqz/TradingAgents-OpenClaw/issues)

---

<p align="center">
  Made with ❤️ by TradingAgents Team
</p>
