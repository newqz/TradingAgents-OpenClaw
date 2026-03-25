# TOOLS.md - TradingAgents 工具配置

## LLM 配置

### Deep Think LLM (分析师、研究员)
```json
{
  "provider": "openai",
  "model": "gpt-4o",
  "temperature": 0.7
}
```

### Fast LLM (简单查询)
```json
{
  "provider": "openai", 
  "model": "gpt-4o-mini",
  "temperature": 0.5
}
```

## 数据源配置

### yfinance (免费)
- 用途: 美股历史数据、股票信息
- 无需 API Key
- 限流: 请求间隔 ≥ 0.5s

### Alpha Vantage (付费)
- 用途: 美股实时/历史数据
- API Key: 环境变量 `ALPHA_VANTAGE_API_KEY`
- 限流: 5请求/分钟 (免费版)

### 中国股票数据 (AKShare)
- 用途: A股、港股数据
- 无需 API Key
- 备选: 东方财富 API

## API 密钥

| 服务 | 环境变量 | 说明 |
|------|----------|------|
| OpenAI | `OPENAI_API_KEY` | LLM 调用 |
| Alpha Vantage | `ALPHA_VANTAGE_API_KEY` | 美股数据 |
| Finnhub | `FINNHUB_API_KEY` | 实时行情 |

## Skill 路径配置

```python
PROJECT_ROOT = "/root/.openclaw/workspace/TradingAgents-OpenClaw"

SKILLS_DIR = os.path.join(PROJECT_ROOT, 'skills')
SKILL_MODULES = [
    'skill-tao-fundamental',
    'skill-tao-technical', 
    'skill-tao-sentiment',
    'skill-tao-researcher-bull',
    'skill-tao-researcher-bear',
    'skill-tao-research-manager',
    'skill-tao-trader',
]
```

## 风险评估参数

| 风险等级 | 评分范围 | 仓位建议 |
|----------|----------|----------|
| LOW | 0-30 | 15-20% |
| MEDIUM | 31-60 | 8-12% |
| HIGH | 61-80 | 3-7% |
| EXTREME | 81-100 | 0-2% |

## 辩论配置

```yaml
max_debate_rounds: 3        # 最大辩论轮数
consensus_threshold: 0.6     # 共识阈值
confidence_threshold: 0.7    # 置信度阈值
```

## 缓存配置

```yaml
cache:
  enabled: true
  ttl: 3600                 # 缓存 TTL (秒)
  max_size: 100             # 最大缓存条目
```

## 日志配置

```yaml
logging:
  level: INFO
  format: "[{time}] {level}: {message}"
  file: "logs/trading.log"
```
