# TradingAgents-OpenClaw 架构设计文档

## 1. 系统架构概览

### 1.1 架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              用户交互层 (Feishu)                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ 单股票分析   │  │ 批量分析     │  │ 历史记录     │  │ 配置管理     │         │
│  │ /分析 NVDA  │  │ /分析多股   │  │ /历史 NVDA  │  │ /设置       │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
└─────────┼────────────────┼────────────────┼────────────────┼────────────────┘
          │                │                │                │
          └────────────────┴────────────────┴────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Master Agent (编排层)                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ TradingOrchestrator                                                 │   │
│  │  ┌──────────────────────────────────────────────────────────────┐  │   │
│  │  │ 1. CommandParser          - 解析用户指令                      │  │   │
│  │  │ 2. StateManager           - 管理分析状态                      │  │   │
│  │  │ 3. ParallelDispatcher     - 并行调度 sub-agents               │  │   │
│  │  │ 4. ResultAggregator       - 聚合分析结果                      │  │   │
│  │  │ 5. DebateCoordinator      - 协调辩论流程                      │  │   │
│  │  │ 6. ReportGenerator        - 生成报告                          │  │   │
│  │  │ 7. FeishuPublisher        - 发布到飞书                      │  │   │
│  │  └──────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────────────────────┘
                           │ 并行调度
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  Fundamental │   │   Sentiment  │   │  Technical   │
│   Analyst    │   │   Analyst    │   │   Analyst    │
│   (Skill)    │   │   (Skill)    │   │   (Skill)    │
└──────┬───────┘   └──────┬───────┘   └──────┬───────┘
       │                  │                  │
       └──────────────────┼──────────────────┘
                          ▼
                ┌──────────────────┐
                │   Researcher     │
                │    (Skill)       │
                └────────┬─────────┘
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
       ┌──────────┐ ┌──────────┐ ┌──────────┐
       │   Bull   │ │ Neutral  │ │   Bear   │
       │  Trader  │ │  Trader  │ │  Trader  │
       │ (Skill)  │ │ (Skill)  │ │ (Skill)  │
       └────┬─────┘ └────┬─────┘ └────┬─────┘
            └─────────────┴────────────┘
                          │
                          ▼
                ┌──────────────────┐
                │   Risk Manager   │
                │     (Skill)      │
                └────────┬─────────┘
                         │
                         ▼
                ┌──────────────────┐
                │ Portfolio Manager│
                │    (Master内)    │
                └──────────────────┘
```

### 1.2 组件职责

| 组件 | 类型 | 职责 |
|------|------|------|
| **TradingOrchestrator** | Master Agent | 整体编排、状态管理、结果聚合 |
| **FundamentalAnalyst** | Skill | 基本面分析（财务数据、公司概况） |
| **SentimentAnalyst** | Skill | 情绪分析（新闻情感、社交媒体） |
| **TechnicalAnalyst** | Skill | 技术面分析（指标、趋势） |
| **Researcher** | Skill | 整合三方观点，形成综合研判 |
| **Bull/Neutral/BearTrader** | Skill | 不同风险偏好的交易建议 |
| **RiskManager** | Skill | 风险评估和仓位建议 |
| **PortfolioManager** | Master内模块 | 最终决策和订单执行 |

---

## 2. 数据流设计

### 2.1 单次分析流程

```
用户输入: "分析 NVDA"
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│ 1. 指令解析 (CommandParser)                              │
│    - 提取股票代码: NVDA                                  │
│    - 提取日期: 默认今日                                  │
│    - 生成 trace_id: UUID                                 │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│ 2. 初始化状态 (StateManager)                             │
│    - 创建 AnalysisState                                  │
│    - 初始化 debate_states                                │
│    - 保存到上下文                                        │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│ 3. 并行分析 (ParallelDispatcher)                         │
│    - 并行启动 3 个 Analyst Skills                        │
│    - 每个 Skill 独立运行                                 │
│    - 等待全部完成                                        │
└─────────────────────────┬───────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
   Fundamental      Sentiment         Technical
   Report           Report            Report
        └─────────────────┬─────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│ 4. 研究整合 (Researcher Skill)                           │
│    - 接收三份报告                                        │
│    - 分析矛盾点                                          │
│    - 输出综合研判                                        │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│ 5. 交易辩论 (DebateCoordinator)                          │
│    - 启动 3 个 Trader Skills                             │
│    - 收集多方观点                                        │
│    - 可选: 多轮辩论                                      │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│ 6. 风险评估 (RiskManager Skill)                          │
│    - 评估交易风险                                        │
│    - 给出仓位建议                                        │
│    - 风险提示                                            │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│ 7. 最终决策 (PortfolioManager)                           │
│    - 综合所有信息                                        │
│    - 生成最终交易决策                                    │
│    - 格式化输出                                          │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│ 8. 发布结果 (FeishuPublisher)                            │
│    - 生成飞书消息卡片                                    │
│    - 发送给用户                                          │
│    - 保存历史记录                                        │
└─────────────────────────────────────────────────────────┘
```

### 2.2 状态流转

```
INITIAL
   │
   ▼
ANALYZING (并行执行3个分析)
   │
   ▼
RESEARCHING (研究员整合)
   │
   ▼
DEBATING (交易员辩论)
   │
   ▼
RISK_ASSESSING (风险评估)
   │
   ▼
FINALIZING (最终决策)
   │
   ▼
COMPLETED / FAILED
```

---

## 3. 核心模型设计

### 3.1 AnalysisState (分析状态)

```python
class AnalysisState(BaseModel):
    """单次分析的完整状态"""
    
    # 基本信息
    trace_id: str                    # 追踪ID
    stock_symbol: str                # 股票代码
    analysis_date: str               # 分析日期
    status: AnalysisStatus           # 当前状态
    created_at: datetime             # 创建时间
    updated_at: datetime             # 更新时间
    
    # 分析师报告
    fundamental_report: Optional[AnalystReport]
    sentiment_report: Optional[AnalystReport]
    technical_report: Optional[AnalystReport]
    
    # 研究整合
    research_summary: Optional[ResearchSummary]
    
    # 交易辩论
    trader_debates: List[DebateRound]
    
    # 风险评估
    risk_assessment: Optional[RiskAssessment]
    
    # 最终决策
    final_decision: Optional[TradeDecision]
    
    # 元数据
    metadata: Dict[str, Any]         # 扩展字段

class AnalysisStatus(str, Enum):
    INITIAL = "initial"
    ANALYZING = "analyzing"
    RESEARCHING = "researching"
    DEBATING = "debating"
    RISK_ASSESSING = "risk_assessing"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    FAILED = "failed"
```

### 3.2 AnalystReport (分析师报告)

```python
class AnalystReport(BaseModel):
    """单个分析师的输出报告"""
    
    agent_type: str                  # 分析师类型
    signal: TradingSignal            # 信号: BUY/SELL/HOLD
    confidence: float               # 置信度 0-1
    reasoning: str                   # 分析理由
    key_metrics: Dict[str, Any]     # 关键指标
    risks: List[str]                # 风险提示
    raw_output: str                 # 原始LLM输出
    created_at: datetime

class TradingSignal(str, Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    UNKNOWN = "unknown"
```

### 3.3 ResearchSummary (研究综合)

```python
class ResearchSummary(BaseModel):
    """研究员整合输出"""
    
    overall_signal: TradingSignal    # 综合信号
    consensus_level: float          # 共识度 0-1
    key_insights: List[str]         # 关键洞察
    contradictions: List[str]       # 矛盾点
    confidence: float               # 整体置信度
    reasoning: str                  # 综合理由
```

### 3.4 TradeDecision (交易决策)

```python
class TradeDecision(BaseModel):
    """最终交易决策"""
    
    action: TradingAction            # 交易动作
    target_price: Optional[float]   # 目标价
    stop_loss: Optional[float]      # 止损价
    position_size: str              # 仓位建议: small/medium/large
    confidence: float               # 决策置信度
    reasoning: str                  # 决策理由
    risk_level: RiskLevel           # 风险等级
    timeframe: str                  # 时间框架
    
class TradingAction(str, Enum):
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"
```

---

## 4. Skill 接口设计

### 4.1 通用接口

每个 Analyst Skill 遵循统一接口：

```python
# Skill 输入
class AnalystInput(BaseModel):
    trace_id: str
    stock_symbol: str
    analysis_date: str
    config: Dict[str, Any]          # LLM配置等

# Skill 输出
class AnalystOutput(BaseModel):
    trace_id: str
    success: bool
    report: Optional[AnalystReport]
    error: Optional[str]
    latency_ms: int
    token_usage: TokenUsage
```

### 4.2 FundamentalAnalyst Skill

```yaml
# Skill 定义
name: skill-tao-fundamental
description: 基本面分析师，分析公司财务数据和基本面信息

input_schema:
  trace_id: string
  stock_symbol: string
  analysis_date: string
  
output_schema:
  report:
    agent_type: "fundamental"
    signal: enum[BUY, SELL, HOLD]
    confidence: float
    reasoning: string
    key_metrics:
      pe_ratio: float
      pb_ratio: float
      revenue_growth: float
      # ...

tools:
  - get_fundamentals
  - get_balance_sheet
  - get_cashflow
  - get_income_statement
  - get_insider_transactions
```

### 4.3 SentimentAnalyst Skill

```yaml
name: skill-tao-sentiment
description: 情绪分析师，分析新闻和市场情绪

tools:
  - get_news
  - get_global_news
  - analyze_sentiment  # 情感分析工具
```

### 4.4 TechnicalAnalyst Skill

```yaml
name: skill-tao-technical
description: 技术面分析师，分析价格走势和技术指标

tools:
  - get_stock_data
  - get_indicators:
      - rsi
      - macd
      - bollinger_bands
      - moving_averages
      - support_resistance
```

---

## 5. 数据层设计

### 5.1 数据提供器架构

```
┌─────────────────────────────────────────────────────────────┐
│                    DataProvider                             │
│                    (统一接口层)                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Yahoo      │ │ AlphaVantage │ │   Cache      │
│  Finance     │ │     API      │ │   Layer      │
│   Client     │ │   Client     │ │   (Redis)    │
└──────────────┘ └──────────────┘ └──────────────┘
```

### 5.2 工具分类

```python
TOOLS_CATEGORIES = {
    "core_stock": {
        "description": "OHLCV股票价格数据",
        "tools": ["get_stock_data"]
    },
    "technical": {
        "description": "技术分析指标",
        "tools": ["get_indicators"]
    },
    "fundamental": {
        "description": "基本面数据",
        "tools": [
            "get_fundamentals",
            "get_balance_sheet",
            "get_cashflow",
            "get_income_statement"
        ]
    },
    "news": {
        "description": "新闻数据",
        "tools": ["get_news", "get_global_news", "get_insider_transactions"]
    }
}
```

### 5.3 缓存策略

| 数据类型 | 缓存时间 | 说明 |
|---------|---------|------|
| 股票价格 | 15分钟 | 实时性要求高 |
| 财务数据 | 24小时 | 季报/年报更新频率低 |
| 新闻数据 | 1小时 | 平衡实时性和成本 |
| 技术指标 | 1小时 | 基于价格计算 |
| 分析报告 | 4小时 | 相同股票短期不重复分析 |

---

## 6. 飞书集成设计

### 6.1 指令解析

| 指令 | 功能 | 示例 |
|------|------|------|
| `/分析 {code}` | 单股票分析 | `/分析 NVDA` |
| `/分析 {code} {date}` | 指定日期分析 | `/分析 AAPL 2025-12-01` |
| `/分析多股 {codes}` | 批量分析 | `/分析多股 NVDA,AAPL,TSLA` |
| `/历史 {code}` | 查看历史分析 | `/历史 NVDA` |
| `/设置` | 查看/修改配置 | `/设置 llm_provider=anthropic` |

### 6.2 消息卡片结构

```json
{
  "config": {"wide_screen_mode": true},
  "header": {
    "title": {"content": "📊 NVDA 分析报告", "tag": "plain_text"},
    "sub_title": {"content": "分析时间: 2026-03-24", "tag": "plain_text"}
  },
  "elements": [
    {
      "tag": "div",
      "text": {"content": "**最终建议**: 买入 (置信度: 78%)", "tag": "lark_md"}
    },
    {
      "tag": "column_set",
      "columns": [
        {"tag": "column", "elements": [{"tag": "div", "text": {"content": "基本面: ⭐⭐⭐⭐", "tag": "lark_md"}}]},
        {"tag": "column", "elements": [{"tag": "div", "text": {"content": "情绪面: ⭐⭐⭐", "tag": "lark_md"}}]},
        {"tag": "column", "elements": [{"tag": "div", "text": {"content": "技术面: ⭐⭐⭐⭐", "tag": "lark_md"}}]}
      ]
    },
    {
      "tag": "action",
      "actions": [
        {"tag": "button", "text": {"content": "查看详情", "tag": "plain_text"}, "type": "primary"},
        {"tag": "button", "text": {"content": "重新分析", "tag": "plain_text"}}
      ]
    }
  ]
}
```

---

## 7. 错误处理与容错

### 7.1 错误分类

| 错误类型 | 示例 | 处理策略 |
|---------|------|---------|
| **数据错误** | 股票代码不存在 | 返回友好提示 |
| **API错误** | Yahoo Finance限流 | 自动切换备用源 |
| **LLM错误** | OpenAI超时 | 重试3次，降级模型 |
| **Agent错误** | 某个分析师失败 | 部分结果 + 警告 |
| **系统错误** | 内部异常 | 记录日志，返回错误 |

### 7.2 降级策略

```
LLM调用失败:
  1. GPT-4o → GPT-4o-mini
  2. GPT-4o-mini → Claude-3-haiku
  3. Claude-3-haiku → Ollama本地模型
  4. 全部失败 → 返回错误

数据源失败:
  1. Alpha Vantage → Yahoo Finance
  2. Yahoo Finance → 缓存数据
  3. 缓存缺失 → 返回错误
```

---

## 8. 监控与可观测性

### 8.1 关键指标

| 指标类别 | 指标名称 | 说明 |
|---------|---------|------|
| **性能** | analysis_duration_seconds | 单次分析耗时 |
| **性能** | agent_latency_ms | 各Agent响应时间 |
| **成本** | llm_tokens_total | LLM Token消耗 |
| **成本** | api_calls_total | API调用次数 |
| **质量** | analysis_success_rate | 分析成功率 |
| **质量** | signal_accuracy | 信号准确率(回测) |

### 8.2 日志追踪

每个分析请求使用 trace_id 贯穿全链路：

```
[trace:abc-123] Received command: 分析 NVDA
[trace:abc-123] Spawned FundamentalAnalyst
[trace:abc-123] Spawned SentimentAnalyst
[trace:abc-123] Spawned TechnicalAnalyst
[trace:abc-123] Fundamental report received (latency: 2.3s)
[trace:abc-123] Sentiment report received (latency: 1.8s)
[trace:abc-123] Technical report received (latency: 2.1s)
[trace:abc-123] Researcher synthesis completed
...
[trace:abc-123] Final decision generated, published to Feishu
```

---

## 9. 安全与合规

### 9.1 免责声明

所有分析报告必须包含：

```
⚠️ 免责声明：本分析仅供参考，不构成投资建议。
投资有风险，入市需谨慎。过往业绩不代表未来表现。
```

### 9.2 数据安全

- API Keys 使用环境变量管理
- 不存储用户持仓等敏感信息
- 分析日志脱敏处理

---

## 10. 扩展性设计

### 10.1 新增分析师

添加新的分析维度：

1. 创建新的 Skill (如: skill-tao-macro)
2. 在 Master Agent 中注册
3. 修改 Researcher Prompt 接收新报告
4. 更新飞书卡片模板

### 10.2 新增数据源

1. 在 DataProvider 中添加新客户端
2. 在 VENDOR_METHODS 中注册方法
3. 配置默认供应商

### 10.3 新增交互渠道

除飞书外，可扩展支持：
- Discord
- Slack
- Telegram
- Web UI

---

**文档版本**: v1.0  
**最后更新**: 2026-03-24
