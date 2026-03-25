# TradingAgents-OpenClaw 整合方案评估

# TradingAgents-OpenClaw 整合方案评估

---

## 1. 技术可行性评分

| Skill | 评分 | 理由 |
|-------|------|------|
| eastmoney-stock | **9/10** | 同为Python，A股数据直接补充核心数据源，API成熟 |
| crypto-trader | **8/10** | 情感分析+交易逻辑可复用，与现有Agent架构契合 |
| weibo-trending | **7/10** | 舆情信号有价值，但需NLP管道将热搜转化为投资信号 |
| crypto-market-data | **6/10** | Node.js异构栈，需跨语言桥接，但数据维度互补 |
| china-stock-sentiment | **4/10** | TODO未完成，整合风险高，建议观望 |

---

## 2. 整合架构建议

采用 **事件驱动 + 适配器模式**，避免侵入式修改：

```
┌─────────────────────────────────────────┐
│         TradingAgents 核心引擎           │
│   (Research/Trading/Risk/Debate Agents) │
└──────────────┬──────────────────────────┘
               │ Unified Data Protocol (Protobuf/JSON Schema)
        ┌──────┴──────┐
        │ Data Router │  ← 统一数据总线 (Redis Streams)
        └──┬───┬───┬──┘
           │   │   │
    ┌──────┤   │   ├──────────┐
    ▼      ▼   ▼   ▼          ▼
Adapter  Adapter Adapter   Adapter
 (东财)  (Crypto)(微博)   (Crypto-Node)
```

**核心原则**：每个Skill封装为独立Adapter，通过统一Schema推送至数据总线，核心引擎零感知来源差异。

---

## 3. 数据流设计

```python
# 统一数据Schema
@dataclass
class MarketSignal:
    source: str          # "eastmoney" | "crypto" | "weibo"
    signal_type: str     # "price" | "sentiment" | "trend"
    asset_id: str        # "SH600519" | "BTC-USDT"
    timestamp: datetime
    payload: dict        # 标准化后的数据体
    confidence: float    # 0-1 信号置信度

# 数据流: Source → Adapter → Router → Agent
```

**关键流程**：
- **实时流**：eastmoney行情 + crypto-market-data → Research Agent（<1s延迟）
- **准实时流**：weibo热搜 → NLP提取实体 → Sentiment Agent（5min周期）
- **批处理流**：crypto-trader情感分析结果 → Risk Agent（日频汇总）

Node.js的crypto-market-data通过 **HTTP微服务** 或 **子进程IPC** 桥接：

```python
# Node.js桥接适配器
class CryptoNodeAdapter:
    def __init__(self):
        self.proc = subprocess.Popen(
            ["node", "crypto-market-data/index.js"],
            stdout=subprocess.PIPE
        )
    
    async def fetch(self, symbol: str) -> MarketSignal:
        # 通过HTTP调用Node服务
        resp = await httpx.get(f"http://localhost:3001/api/market/{symbol}")
        return MarketSignal(source="crypto-node", **self._normalize(resp.json()))
```

---

## 4. 风险评估

| 风险 | 等级 | 缓解措施 |
|------|------|----------|
| 东财API反爬/限流 | 🔴高 | IP池+请求限速+本地缓存层 |
| Node.js进程崩溃拖垮主系统 | 🟡中 | 进程隔离+健康检查+熔断器 |
| 微博数据噪声导致误判 | 🟡中 | 置信度阈值过滤，需>0.7才入决策链 |
| 多源数据时间戳不对齐 | 🟡中 | 统一UTC时间窗口对齐（Event Time语义） |
| china-stock-sentiment未完成 | 🔴高 | **不纳入本期整合** |

---

## 5. 实施优先级

```
Phase 4a (Week 1-2): eastmoney-stock ← 最高ROI，同语言，核心数据
Phase 4b (Week 3-4): crypto-trader   ← 情感分析引擎可泛化复用
Phase 4c (Week 5-6): weibo-trending  ← 舆情补充，需额外NLP工作
Phase 4d (Week 7+):  crypto-market-data ← 跨语言，优先级最低
Phase 5:  china-stock-sentiment ← 待其完成TODO后再评估
```

---

## 6. 关键代码接口示例

```python
# 东财适配器核心接口
class EastMoneyAdapter(BaseAdapter):
    async def get_realtime_quote(self, stock_code: str) -> MarketSignal:
        raw = eastmoney_api.get_quote(stock_code)  # 调用eastmoney-stock
        return MarketSignal(
            source="eastmoney", signal_type="price",
            asset_id=stock_code, timestamp=datetime.utcnow(),
            payload={"price": raw.price, "volume": raw.volume,
                     "change_pct": raw.change_pct},
            confidence=0.95
        )

# 注册到TradingAgents数据总线
class DataRouter:
    def __init__(self):
        self.adapters: dict[str, BaseAdapter] = {}
        self.bus = RedisStream("trading:signals")
    
    def register(self, name: str, adapter: BaseAdapter):
        self.adapters[name] = adapter
    
    async def broadcast(self, signal: MarketSignal):
        await self.bus.publish(signal.to_dict())

# Agent消费端
class ResearchAgent:
    async def on_signal(self, signal: MarketSignal):
        if signal.confidence < 0.6:
            return  # 低置信度丢弃
        self.analysis_queue.put(signal)
```

---

**总结**：优先整合eastmoney-stock（1周可产出），采用适配器+数据总线解耦，china-stock-sentiment暂不碰。整体方案技术风险可控，预计6周完成核心整合。