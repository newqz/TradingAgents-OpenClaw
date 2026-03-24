# TradingAgents-OpenClaw

<p align="center">
  <h1>🚀 TradingAgents-OpenClaw</h1>
  <p>基于 OpenClaw 框架的多 Agent 量化交易分析系统</p>
  <p>
    <a href="#核心特性">核心特性</a> •
    <a href="#架构设计">架构设计</a> •
    <a href="#快速开始">快速开始</a> •
    <a href="#成本估算">成本估算</a>
  </p>
</p>

---

## 📖 项目介绍

**TradingAgents-OpenClaw** 是将 [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents) 迁移到 [OpenClaw](https://github.com/openclaw) 框架的开源项目。

与原项目相比，OpenClaw 版本的优势：
- **原生多 Agent 支持** - 利用 OpenClaw 的 `sessions_spawn` 实现真正的并行 Agent 协作
- **多渠道接入** - 飞书、Discord、Telegram 等渠道开箱即用
- **模块化架构** - 每个 Agent 作为独立 Skill，易于扩展和维护
- **多市场覆盖** - 美股、A股、港股统一支持

---

## ✨ 核心特性

### 🤖 多 Agent 协作架构 (11 Agents)

| 阶段 | Agents | 职责 |
|------|--------|------|
| **Phase 1** | 3 位分析师 | 基本面 + 技术面 + 情绪面 并行分析 |
| **Phase 2** | 3 位研究员 | Bull vs Bear 多空辩论 + 研究经理整合 |
| **Phase 3** | 3 位交易员 | 激进/中性/保守 多风险偏好策略 |
| **风控** | 1 位风控经理 | 综合风险评估与仓位控制 |

### 🗣️ 多空对抗辩论机制

核心创新：不是简单的投票，而是**对抗性论证**

```
Bull Researcher: "我认为应该买入，理由是..."
    ↓
Bear Researcher: "我反对，你的逻辑有问题，因为..."
    ↓
Bull Researcher: "你忽略了这一点，让我补充..."
    ↓
Research Manager: "基于双方观点，综合研判如下..."
```

### 🌍 多市场支持

| 市场 | 代码格式 | 示例 | 数据源 |
|------|----------|------|--------|
| 🇺🇸 美股 | 字母代码 | `NVDA`, `AAPL` | Yahoo Finance / Alpha Vantage |
| 🇨🇳 A股 | 代码.交易所 | `000001.SZ`, `600000.SH` | akshare (东方财富) |
| 🇭🇰 港股 | 代码.HK | `0700.HK`, `3690.HK` | akshare |

---

## 🏗️ 架构设计

### 完整架构流程

```
用户指令 (飞书/Discord/Telegram)
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│                    Master Agent                              │
│              (TradingOrchestrator)                           │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Phase 1: 分析师团队 (并行执行)                               │
│  ┌──────────────┬──────────────┬──────────────┐              │
│  │ Fundamental  │  Technical   │  Sentiment   │              │
│  │   Analyst    │   Analyst    │   Analyst    │              │
│  └──────┬───────┴──────┬───────┴──────┬───────┘              │
│         │              │              │                      │
│         └──────────────┼──────────────┘                      │
│                        ▼                                      │
│              Analyst Reports (3份)                            │
│                                                               │
│  Phase 2: 多空研究员辩论 (可配置轮次)                          │
│                        │                                      │
│         ┌──────────────┼──────────────┐                      │
│         ▼              ▼              ▼                      │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐         │
│  │   Bull       │ │    Bear      │ │   Research   │         │
│  │  Researcher  │◀─┤  Researcher  │◀─┤   Manager    │         │
│  └──────────────┘ └──────────────┘ └──────────────┘         │
│         │              │              │                      │
│         └──────────────┼──────────────┘                      │
│                        ▼                                      │
│              Research Synthesis (综合研判)                    │
│                                                               │
│  Phase 3: 交易执行 (并行)                                     │
│                        │                                      │
│         ┌──────────────┼──────────────┐                      │
│         ▼              ▼              ▼                      │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐         │
│  │   Bull       │ │   Neutral    │ │    Bear      │         │
│  │   Trader     │ │   Trader     │ │   Trader     │         │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘         │
│         │                │                │                  │
│         └────────────────┼────────────────┘                  │
│                          ▼                                    │
│                Trader Recommendations (3份)                  │
│                          │                                    │
│  ┌───────────────────────┘                                    │
│  ▼                                                            │
│  Risk Manager (风险评估)                                      │
│  │                                                            │
│  ▼                                                            │
│  Final Decision (最终决策)                                    │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
多渠道报告输出 (飞书卡片/Discord消息等)
```

### 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| **框架** | OpenClaw | Agent 编排框架 |
| **LLM** | OpenAI GPT-4o / Claude 3.5 | 分析推理 |
| **数据源** | yfinance / alpha-vantage / akshare | 股票数据 |
| **渠道** | Feishu / Discord / Telegram | 用户交互 |
| **缓存** | Redis (可选) | 数据缓存 |

---

## 🚀 快速开始

### 前置要求

- Python 3.10+
- OpenAI API Key
- OpenClaw Gateway (如部署到 OpenClaw)
- 飞书 Bot (如使用飞书渠道)

### 安装

```bash
# 克隆项目
git clone https://github.com/newqz/TradingAgents-OpenClaw.git
cd TradingAgents-OpenClaw

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
export OPENAI_API_KEY="sk-..."
export ALPHA_VANTAGE_API_KEY="..."  # 可选
```

### 飞书指令

| 指令 | 功能 | 示例 |
|------|------|------|
| `/分析 {code}` | 单股票分析 | `/分析 NVDA` |
| `/分析 {code} {date}` | 指定日期分析 | `/分析 AAPL 2025-12-01` |
| `/分析多股 {codes}` | 批量分析 | `/分析多股 NVDA,AAPL,TSLA` |
| `/历史 {code}` | 查看历史分析 | `/历史 NVDA` |

**支持的市场**
- 🇺🇸 **美股**: `NVDA`, `AAPL`, `TSLA`
- 🇨🇳 **A股**: `000001.SZ`, `600000.SH`, `300001.SZ`
- 🇭🇰 **港股**: `0700.HK`, `3690.HK`, `9988.HK`

---

## 💰 成本估算

基于 GPT-4o，单次完整分析成本约 **$1.50**

| 阶段 | Agents | Token 消耗 | 估算成本 |
|------|--------|-----------|---------|
| Phase 1: 分析师 | 3 | 15,000 | ~$0.45 |
| Phase 2: 研究员 | 3 | 12,000 | ~$0.57 |
| Phase 3: 交易执行 | 4 | 11,000 | ~$0.51 |
| **总计** | **10** | **38,000** | **~$1.53** |

**成本优化建议**:
- 使用 GPT-4o-mini 进行初步筛选，成本降低 80%
- 添加缓存机制，相同股票 24h 内复用结果
- 配置成本上限告警

---

## 📁 项目结构

```
TradingAgents-OpenClaw/
├── README.md                    # 本文件
├── PROJECT.md                   # 项目规划文档
├── requirements.txt             # Python 依赖
│
├── skills/                      # OpenClaw Skills
│   ├── skill-tao-data/          # 数据层
│   │   ├── data_provider.py     # 统一数据接口
│   │   └── vendors/             # 数据供应商
│   │       ├── yfinance_client.py
│   │       ├── alpha_vantage_client.py
│   │       └── china_stock_client.py  # A股/港股
│   │
│   ├── skill-tao-fundamental/   # 基本面分析师
│   ├── skill-tao-technical/     # 技术面分析师
│   ├── skill-tao-sentiment/     # 情绪分析师
│   │
│   ├── skill-tao-researcher-bull/   # 看多研究员
│   ├── skill-tao-researcher-bear/   # 看空研究员
│   ├── skill-tao-research-manager/  # 研究经理
│   │
│   ├── skill-tao-trader/        # 三位交易员
│   └── skill-tao-risk-manager/  # 风险管理
│
├── master-agent/                # Master Agent
│   ├── orchestrator_full.py     # 完整编排器
│   └── feishu_adapter.py        # 飞书适配器
│
├── shared/                      # 共享模块
│   └── models.py                # 数据模型
│
└── docs/                        # 文档
    └── architecture.md          # 架构设计
```

---

## 📚 文档

- [PROJECT.md](./PROJECT.md) - 项目规划与里程碑
- [docs/architecture.md](./docs/architecture.md) - 详细架构设计

---

## 🙏 致谢

本项目基于 [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents) 开发。

**原项目信息**:
- 论文: [TradingAgents: Multi-Agents LLM Financial Trading Framework](https://arxiv.org/abs/2412.20138)
- 作者: Yijia Xiao, Edward Sun, Di Luo, Wei Wang

---

## ⚠️ 免责声明

本系统仅供研究和学习使用，**不构成任何投资建议**。投资有风险，入市需谨慎。过往业绩不代表未来表现。

---

## 📄 License

MIT License - 详见 [LICENSE](./LICENSE)

---

<p align="center">
  Built with ❤️ using <a href="https://github.com/openclaw">OpenClaw</a>
</p>
