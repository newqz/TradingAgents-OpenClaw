# TradingAgents-OpenClaw

<p align="center">
  <h1>🚀 TradingAgents-OpenClaw</h1>
  <p>基于 OpenClaw 框架的多Agent量化交易分析系统</p>
  <p>
    <a href="#项目介绍">项目介绍</a> •
    <a href="#架构设计">架构设计</a> •
    <a href="#快速开始">快速开始</a> •
    <a href="#开发计划">开发计划</a>
  </p>
</p>

---

## 📖 项目介绍

**TradingAgents-OpenClaw** 是将 [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents) 迁移到 OpenClaw 框架的开源项目。

### 核心特性

- 🤖 **多Agent协作** - 基本面/情绪/技术面分析师并行分析
- 💬 **飞书原生集成** - 通过飞书指令直接获取分析报告
- 🌍 **多市场支持** - 美股、A股、港股全覆盖
- ⚡ **并行优化** - 利用 OpenClaw sub-agents 提升响应速度
- 🧩 **模块化设计** - Skill 化架构，易于扩展
- 📊 **智能决策** - 多轮辩论机制生成交易建议

### 技术栈

| 层级 | 技术 |
|------|------|
| 框架 | OpenClaw |
| 渠道 | Feishu (飞书) |
| LLM | OpenAI / Anthropic / Google / Ollama |
| 数据 | Yahoo Finance / Alpha Vantage / akshare |
| 缓存 | Redis |

---

## 🏗️ 架构设计

### 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        Feishu User                          │
└───────────────────────────┬─────────────────────────────────┘
                            │ 发送指令: "分析 NVDA"
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                 TradingOrchestrator                         │
│                    (Master Agent)                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  1. 解析指令 → 2. 并行分析 → 3. 整合 → 4. 决策      │   │
│  └─────────────────────────────────────────────────────┘   │
└──────────────┬──────────────────────┬──────────────────────┘
               │                      │
   ┌───────────┴───────────┐ ┌────────┴──────────┐
   ▼                       ▼ ▼                   ▼
Fundamental  Sentiment  Technical  Researcher  Traders  Risk
Analyst      Analyst    Analyst    (整合)      (辩论)   Manager
```

### Agent 角色

| Agent | 职责 | 状态 |
|-------|------|------|
| **FundamentalAnalyst** | 分析财务数据、公司基本面 | 🚧 开发中 |
| **SentimentAnalyst** | 分析新闻情绪、市场情绪 | 📋 计划中 |
| **TechnicalAnalyst** | 分析技术指标、价格走势 | 🚧 开发中 |
| **Researcher** | 整合三方观点，形成综合研判 | 📋 计划中 |
| **Bull/Neutral/BearTrader** | 不同风险偏好交易建议 | 📋 计划中 |
| **RiskManager** | 风险评估、仓位建议 | 📋 计划中 |

---

## 🚀 快速开始

### 前置要求

- Python 3.10+
- OpenClaw Gateway 已部署
- 飞书机器人已配置
- API Keys (OpenAI / Alpha Vantage)

### 安装

```bash
# 克隆项目
git clone <repository-url>
cd TradingAgents-OpenClaw

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 添加你的 API Keys
```

### 飞书指令

| 指令 | 功能 | 示例 |
|------|------|------|
| `/分析 {code}` | 单股票分析 | `/分析 NVDA` |
| `/分析 {code} {date}` | 指定日期分析 | `/分析 AAPL 2025-12-01` |
| `/历史 {code}` | 查看历史分析 | `/历史 NVDA` |

**支持的市场**
- 🇺🇸 **美股**: `NVDA`, `AAPL`, `TSLA` (字母代码)
- 🇨🇳 **A股**: `000001.SZ`, `600000.SH`, `300001.SZ` (深交所/上交所)
- 🇭🇰 **港股**: `0700.HK`, `3690.HK`, `9988.HK` (香港交易所)

---

## 📅 开发计划

### Phase 1: MVP (Week 1-4) - 当前阶段

- [ ] 数据层 (Yahoo Finance 集成)
- [ ] 基本面分析师 Skill
- [ ] 技术面分析师 Skill
- [ ] Master Agent 编排
- [ ] 飞书基础集成

### Phase 2: 完整功能 (Week 5-8)

- [ ] 情绪分析师 Skill
- [ ] 研究员整合层
- [ ] 交易员辩论机制
- [ ] 风险管理

### Phase 3: 生产优化 (Week 9-12)

- [ ] Redis 缓存层
- [ ] 监控告警
- [ ] 批量分析
- [ ] 完整文档

---

## 📚 文档

- [项目规划](./PROJECT.md) - 完整的项目规划文档
- [架构设计](./docs/architecture.md) - 详细架构设计
- [飞书集成](./docs/feishu-integration.md) - 飞书集成指南
- [部署文档](./docs/deployment.md) - 部署说明

---

## 🙏 致谢

本项目基于 [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents) 开发，感谢原作者的开源贡献。

### 原项目信息

- **论文**: [TradingAgents: Multi-Agents LLM Financial Trading Framework](https://arxiv.org/abs/2412.20138)
- **技术**: LangGraph + Python
- **作者**: Yijia Xiao, Edward Sun, Di Luo, Wei Wang

---

## ⚠️ 免责声明

本系统仅供研究和学习使用，不构成任何投资建议。投资有风险，入市需谨慎。

---

## 📄 License

MIT License - 详见 [LICENSE](./LICENSE)
