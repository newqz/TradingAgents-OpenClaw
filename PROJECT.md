# TradingAgents-OpenClaw 项目规划

## 📋 项目立项信息

| 项目属性 | 内容 |
|---------|------|
| **项目名称** | TradingAgents-OpenClaw |
| **项目代号** | TAO (TradingAgents OpenClaw) |
| **项目状态** | 已立项 |
| **立项日期** | 2026-03-24 |
| **项目负责人** | 领航员 |
| **开发团队** | AI Agent 开发团队 |
| **可行性评分** | 83/100 (推荐实施) |

---

## 🎯 项目目标

将 TauricResearch/TradingAgents (基于 LangGraph 的多Agent量化交易框架) 迁移至 OpenClaw 框架，实现：

1. **多Agent协作分析** - 基本面/情绪/技术面分析师并行工作
2. **飞书原生集成** - 通过飞书渠道进行交互
3. **多市场支持** - 美股、A股、港股全覆盖
4. **可扩展架构** - Skill 化设计，便于功能扩展
5. **成本优化** - 通过并行执行和缓存降低运营成本

---

## 📊 原项目核心架构学习总结

### 1. 原项目架构 (LangGraph)

```
┌─────────────────────────────────────────────────────────────┐
│                      LangGraph Workflow                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  START                                                       │
│   │                                                          │
│   ▼                                                          │
│  ┌─────────────────┐     ┌─────────────────┐                │
│  │ Market Analyst  │────▶│ Msg Clear       │                │
│  │ (Technical)     │     │                 │                │
│  └─────────────────┘     └────────┬────────┘                │
│                                   │                          │
│   ┌───────────────────────────────┘                          │
│   ▼                                                          │
│  ┌─────────────────┐     ┌─────────────────┐                │
│  │ Social Analyst  │────▶│ Msg Clear       │                │
│  │ (Sentiment)     │     │                 │                │
│  └─────────────────┘     └────────┬────────┘                │
│                                   │                          │
│   ┌───────────────────────────────┘                          │
│   ▼                                                          │
│  ┌─────────────────┐     ┌─────────────────┐                │
│  │ News Analyst    │────▶│ Msg Clear       │                │
│  └─────────────────┘     └────────┬────────┘                │
│                                   │                          │
│   ┌───────────────────────────────┘                          │
│   ▼                                                          │
│  ┌─────────────────┐     ┌─────────────────┐                │
│  │ Fundamentals    │────▶│ Msg Clear       │                │
│  │ Analyst         │     │                 │                │
│  └─────────────────┘     └────────┬────────┘                │
│                                   │                          │
│   ┌───────────────────────────────┘                          │
│   ▼                                                          │
│  ┌─────────────────┐                                         │
│  │ Bull Researcher │◀────┐                                   │
│  └────────┬────────┘     │ 辩论轮次循环                      │
│           │              │ (max_debate_rounds)               │
│           ▼              │                                   │
│  ┌─────────────────┐     │                                   │
│  │ Bear Researcher │─────┘                                   │
│  └────────┬────────┘                                         │
│           ▼                                                  │
│  ┌─────────────────┐                                         │
│  │ Research Manager│ 整合多方观点                              │
│  └────────┬────────┘                                         │
│           ▼                                                  │
│  ┌─────────────────┐                                         │
│  │ Trader          │ 制定交易计划                              │
│  └────────┬────────┘                                         │
│           ▼                                                  │
│  ┌─────────────────┐     ┌─────────────────┐                │
│  │ Aggressive      │◀───▶│ Conservative    │ 风险评估辩论     │
│  └────────┬────────┘     └────────┬────────┘                │
│           │                       │                          │
│           ▼                       ▼                          │
│  ┌─────────────────┐                                         │
│  │ Neutral Analyst │ 风险评估                                 │
│  └────────┬────────┘                                         │
│           ▼                                                  │
│  ┌─────────────────┐                                         │
│  │ Portfolio Mgr   │ 最终决策                                 │
│  └────────┬────────┘                                         │
│           ▼                                                  │
│          END                                                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 2. 核心组件学习

#### 2.1 状态管理 (AgentState)

原项目使用 LangGraph 的 TypedDict 状态管理：

```python
class AgentState(MessagesState):
    company_of_interest: str      # 关注的公司
    trade_date: str               # 交易日期
    sender: str                   # 发送消息的Agent
    
    # 分析师报告
    market_report: str            # 技术面报告
    sentiment_report: str         # 情绪面报告
    news_report: str              # 新闻报告
    fundamentals_report: str      # 基本面报告
    
    # 研究辩论状态
    investment_debate_state: InvestDebateState
    investment_plan: str
    trader_investment_plan: str
    
    # 风险评估状态
    risk_debate_state: RiskDebateState
    final_trade_decision: str
```

**借鉴点**: 清晰的状态分层设计，将分析结果、辩论状态、最终决策分离。

#### 2.2 数据层设计

原项目使用多数据源路由设计：

```python
# 工具分类
TOOLS_CATEGORIES = {
    "core_stock_apis": ["get_stock_data"],
    "technical_indicators": ["get_indicators"],
    "fundamental_data": ["get_fundamentals", "get_balance_sheet", ...],
    "news_data": ["get_news", "get_global_news", ...]
}

# 供应商方法映射
VENDOR_METHODS = {
    "get_stock_data": {
        "alpha_vantage": get_alpha_vantage_stock,
        "yfinance": get_YFin_data_online,
    },
    ...
}

# 自动故障转移
route_to_vendor(method, *args, **kwargs)
```

**借鉴点**: 
- 分类清晰的数据工具组织
- 多供应商自动故障转移
- 配置化供应商选择

#### 2.3 Agent 设计模式

原项目每个 Agent 采用统一的创建函数模式：

```python
def create_fundamentals_analyst(llm):
    def fundamentals_analyst_node(state):
        # 1. 构建上下文
        instrument_context = build_instrument_context(state["company_of_interest"])
        
        # 2. 定义工具
        tools = [get_fundamentals, get_balance_sheet, ...]
        
        # 3. 构建 Prompt
        system_message = "You are a researcher tasked with..."
        prompt = ChatPromptTemplate.from_messages([...])
        
        # 4. 绑定工具并执行
        chain = prompt | llm.bind_tools(tools)
        result = chain.invoke(state["messages"])
        
        # 5. 返回状态更新
        return {
            "messages": [result],
            "fundamentals_report": report,
        }
    
    return fundamentals_analyst_node
```

**借鉴点**:
- 函数工厂模式创建 Agent
- LLM + Tools 绑定执行
- 明确的状态更新返回

#### 2.4 辩论机制

原项目采用多轮辩论机制：

- **InvestDebateState**: 记录看多/看空研究员的辩论历史
- **RiskDebateState**: 记录激进/保守/中性分析师的风险评估
- **条件边**: 根据轮次决定是否继续辩论或进入下一阶段

```python
# 辩论状态
class InvestDebateState(TypedDict):
    bull_history: str
    bear_history: str
    history: str
    current_response: str
    judge_decision: str
    count: int  # 当前轮次
```

**借鉴点**:
- 状态内嵌套子状态，记录辩论过程
- 可配置的辩论轮次
- 评委机制做最终裁决

---

## 🏗️ OpenClaw 迁移架构设计

### 1. 架构对比

| 维度 | LangGraph 版本 | OpenClaw 版本 |
|------|---------------|---------------|
| **编排层** | StateGraph 状态机 | Master Agent + sub-agents |
| **Agent定义** | Python函数节点 | OpenClaw Skills |
| **状态传递** | LangGraph State | 消息传递 + 共享上下文 |
| **通信机制** | 图节点间边连接 | sessions_send / 文件共享 |
| **并行执行** | 条件边控制 | sub-agents 原生并行 |
| **交互渠道** | CLI | 飞书原生支持 |

### 2. 新架构设计

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Feishu User                                  │
└───────────────────────────┬─────────────────────────────────────────┘
                            │ 发送指令: "分析 NVDA"
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Master Agent (TradingOrchestrator)               │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 职责:                                                        │   │
│  │  1. 解析用户指令 (股票代码、日期)                               │   │
│  │  2. 并行启动三位分析师 sub-agents                              │   │
│  │  3. 收集分析结果                                              │   │
│  │  4. 调度研究员整合                                            │   │
│  │  5. 调度交易员辩论                                            │   │
│  │  6. 调度风险评估                                              │   │
│  │  7. 格式化输出并返回飞书                                       │   │
│  └─────────────────────────────────────────────────────────────┘   │
└──────────────┬──────────────────────┬──────────────────────┬────────┘
               │                      │                      │
               ▼                      ▼                      ▼
    ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
    │ FundamentalSkill │  │ SentimentSkill   │  │ TechnicalSkill   │
    │ 基本面分析师      │  │ 情绪分析师        │  │ 技术面分析师      │
    └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘
             │                     │                     │
             └─────────────────────┼─────────────────────┘
                                   ▼
                      ┌────────────────────┐
                      │ ResearcherSkill    │
                      │ 研究员整合层        │
                      └─────────┬──────────┘
                                │
              ┌─────────────────┼─────────────────┐
              ▼                 ▼                 ▼
    ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
    │ BullTraderSkill  │ │ NeutralTraderSkill│ │ BearTraderSkill  │
    │ 激进交易员        │ │ 中性交易员        │ │ 保守交易员        │
    └────────┬─────────┘ └────────┬─────────┘ └────────┬─────────┘
             └────────────────────┼────────────────────┘
                                  ▼
                      ┌────────────────────┐
                      │ RiskManagerSkill   │
                      │ 风险管理           │
                      └─────────┬──────────┘
                                ▼
                      ┌────────────────────┐
                      │ PortfolioManager   │
                      │ 投资组合经理        │
                      └────────────────────┘
```

### 3. 关键技术决策

#### 决策1: Agent 粒度划分

**方案A**: 每个分析师作为独立 Skill (推荐)
- Pros: 独立部署、独立扩展、故障隔离
- Cons: 管理复杂度稍高

**方案B**: 所有分析师在一个 Skill 中
- Pros: 管理简单
- Cons: 无法并行、单点故障

**结论**: 采用方案A，符合 OpenClaw 设计理念。

#### 决策2: 状态传递机制

**方案A**: 通过消息传递 (sessions_send)
- 使用 trace_id 串联整个流程
- 每个 sub-agent 完成后通过消息返回结果
- Master Agent 维护完整状态

**方案B**: 通过共享文件/Redis
- 状态持久化到共享存储
- sub-agents 读写共享状态

**结论**: Phase 1 采用方案A（简单），Phase 2 引入方案B（生产级）。

#### 决策3: 数据层实现

**借鉴原项目设计**:
- 保留多供应商路由架构
- 保留工具分类组织方式
- 添加本地缓存层

**新增优化**:
- 添加 Redis 缓存
- 添加请求去重
- 添加降级策略

---

## 📁 项目目录结构

```
TradingAgents-OpenClaw/
├── 📄 PROJECT.md                    # 本项目规划文档
├── 📄 README.md                     # 项目说明
│
├── 📁 original-repo/                # 原项目代码 (学习参考)
│   └── (git clone TradingAgents)
│
├── 📁 docs/                         # 文档
│   ├── architecture.md              # 架构设计文档
│   ├── api-reference.md             # API参考
│   ├── feishu-integration.md        # 飞书集成指南
│   └── deployment.md                # 部署文档
│
├── 📁 skills/                       # OpenClaw Skills
│   ├── skill-tao-data/              # 数据层 Skill
│   │   ├── SKILL.md
│   │   ├── data_provider.py
│   │   ├── cache_manager.py
│   │   └── vendors/
│   │       ├── yfinance_client.py
│   │       └── alpha_vantage_client.py
│   │
│   ├── skill-tao-fundamental/       # 基本面分析师
│   │   ├── SKILL.md
│   │   └── fundamental_analyst.py
│   │
│   ├── skill-tao-sentiment/         # 情绪分析师
│   │   ├── SKILL.md
│   │   └── sentiment_analyst.py
│   │
│   ├── skill-tao-technical/         # 技术面分析师
│   │   ├── SKILL.md
│   │   └── technical_analyst.py
│   │
│   ├── skill-tao-researcher/        # 研究员整合
│   │   ├── SKILL.md
│   │   └── researcher.py
│   │
│   ├── skill-tao-trader/            # 交易员
│   │   ├── SKILL.md
│   │   └── trader.py
│   │
│   └── skill-tao-risk/              # 风险管理
│       ├── SKILL.md
│       └── risk_manager.py
│
├── 📁 master-agent/                 # Master Agent
│   ├── orchestrator.py              # 核心编排逻辑
│   ├── state_manager.py             # 状态管理
│   ├── feishu_adapter.py            # 飞书适配器
│   └── config.py                    # 配置管理
│
├── 📁 shared/                       # 共享模块
│   ├── models.py                    # 数据模型
│   ├── prompts/                     # LLM Prompts
│   │   ├── fundamental.txt
│   │   ├── sentiment.txt
│   │   ├── technical.txt
│   │   ├── researcher.txt
│   │   ├── trader.txt
│   │   └── risk.txt
│   └── utils.py                     # 工具函数
│
├── 📁 tests/                        # 测试
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
├── 📁 deployment/                   # 部署配置
│   ├── docker/
│   ├── docker-compose.yml
│   └── kubernetes/
│
└── 📁 scripts/                      # 脚本
    ├── setup.sh                     # 初始化脚本
    └── deploy.sh                    # 部署脚本
```

---

## 📅 开发里程碑

### ✅ Phase 1: MVP (Week 1-4) - 已完成

**目标**: 验证核心流程，单股票分析可用

| Week | 任务 | 交付物 | 状态 |
|------|------|--------|------|
| W1 | 数据层开发 | skill-tao-data 完成 | ✅ |
| W2 | 分析师开发 | skill-tao-fundamental + skill-tao-technical | ✅ |
| W3 | Master Agent + 飞书集成 | 端到端流程打通 | ✅ |
| W4 | 测试优化 | MVP 上线 | ✅ |

**成功标准**:
- [x] 单次分析响应 < 30s
- [x] 分析成功率 > 95%
- [x] 飞书指令交互正常

---

### ✅ Phase 2: 完整功能 (Week 5-8) - 已完成

**目标**: 实现完整多Agent协作

| Week | 任务 | 交付物 | 状态 |
|------|------|--------|------|
| W5 | 情绪分析师 | skill-tao-sentiment | ✅ |
| W6 | 研究员整合 | skill-tao-researcher + Bull/Bear 辩论 | ✅ |
| W7 | A股/港股支持 | Phase 1.5 多市场数据 | ✅ |
| W8 | 集成测试 | 完整 Phase 2 测试 | ✅ |

**成功标准**:
- [x] 完整分析流程 < 60s
- [x] 辩论机制正常工作
- [x] 风险评估输出合格

---

### ✅ Phase 3: 交易员辩论 + 风险管理 (Week 9-10) - 已完成

**目标**: 实现交易员辩论和风险评估

| 任务 | 交付物 | 状态 |
|------|--------|------|
| 交易员辩论 | skill-tao-trader-bull/neutral/bear | ✅ |
| 风险管理 | skill-tao-risk-manager | ✅ |
| 投资组合经理 | PortfolioManager | ✅ |
| 完整编排器 | orchestrator_phase3.py | ✅ |

**成功标准**:
- [x] 三交易员并行提建议
- [x] 风险等级影响仓位大小
- [x] 简化版决策 (无需额外 LLM 调用)

---

### 🔄 Phase 4: 生产优化 (Week 11-12) - 待开发

**目标**: 生产级稳定性

| Week | 任务 | 交付物 |
|------|------|--------|
| W11 | 缓存优化 | Redis 缓存层 |
| W12 | 监控告警 | 成本/性能监控 |

**可选功能**:
- [ ] 批量分析 (多股票并行)
- [ ] 历史回测接口
- [ ] 组合优化算法

---

## 🛠️ 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| **框架** | OpenClaw | Agent编排框架 |
| **渠道** | Feishu | 用户交互渠道 |
| **LLM** | OpenAI/Anthropic/Google | 多供应商支持 |
| **数据** | yfinance / Alpha Vantage | 股票数据源 |
| **缓存** | Redis | 热数据缓存 |
| **存储** | PostgreSQL | 历史记录持久化 |
| **监控** | Prometheus + Grafana | 指标监控 |

---

## 📊 借鉴与创新

### 从原项目借鉴

| 原项目设计 | 本项目应用 |
|-----------|-----------|
| 状态分层设计 | AgentState 模型 |
| 多供应商路由 | DataProvider 类 |
| 工具分类组织 | TOOLS_CATEGORIES |
| 辩论状态机 | DebateState 类 |
| Prompt 模板 | prompts/ 目录 |

### 本项目创新

| 创新点 | 说明 |
|--------|------|
| OpenClaw 原生集成 | 飞书渠道无缝集成 |
| 并行分析优化 | sub-agents 并行执行 |
| Skill 化架构 | 模块化、可复用 |
| 成本监控 | LLM调用成本实时追踪 |

---

## ✅ 下一步行动

### 已完成项目
1. [x] **环境准备** - OpenClaw Gateway 配置
2. [x] **数据层** - skill-tao-data
3. [x] **三分析师** - skill-tao-fundamental/technical/sentiment
4. [x] **研究员辩论** - Bull/Bear 多轮辩论机制
5. [x] **交易员辩论** - Bull/Neutral/Bear 三交易员
6. [x] **风险管理** - RiskManager + PortfolioManager
7. [x] **飞书集成** - FeishuAdapter

### 待开发/优化
1. [ ] **生产部署** - 部署到 OpenClaw Gateway
2. [ ] **缓存层** - Redis 缓存优化
3. [ ] **监控告警** - 成本/性能监控
4. [ ] **批量分析** - 多股票并行处理
5. [ ] **历史回测** - 回测接口

---

**🎉 Phase 1-3 核心功能开发完成！**
