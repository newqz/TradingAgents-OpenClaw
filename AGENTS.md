# AGENTS.md - TradingAgents 工作规范

_这是 TradingAgents-OpenClaw 的工作目录。_

## 项目结构

```
TradingAgents-OpenClaw/
├── master-agent/         # 核心编排器
│   ├── orchestrator.py          # Phase 1 编排器
│   ├── orchestrator_phase3.py   # Phase 3 完整编排器
│   ├── portfolio_manager.py      # 投资组合经理
│   └── trader_debate_orchestrator.py  # 交易员辩论
├── skills/              # 分析 Skills
│   ├── skill-tao-fundamental/   # 基本面分析
│   ├── skill-tao-technical/     # 技术分析
│   ├── skill-tao-sentiment/     # 情绪分析
│   ├── skill-tao-research-manager/  # 研究整合
│   └── skill-tao-trader/        # 交易决策
├── shared/             # 共享模块
│   └── models.py              # 数据模型
└── bootstrap.py       # 路径配置
```

## 会话启动

每次会话开始时：

1. 读取 `SOUL.md` - 了解分析理念
2. 读取 `USER.md` - 了解用户偏好
3. 检查 `memory/` 目录 - 获取历史分析记录

## 分析流程

### Phase 1: 三分析师并行
```
用户请求 → 并行调度 → 基本面 + 技术面 + 情绪面
```

### Phase 2: 研究员辩论
```
分析师报告 → Bull研究员的看多观点
          → Bear研究员的看空观点
          → Research Manager 综合裁决
```

### Phase 3: 交易员决策
```
研究结论 → 三交易员建议 (Bull/Neutral/Bear)
        → Risk Manager 风险评估
        → Portfolio Manager 最终决策
```

## 记忆管理

- **分析记录**: 每次分析保存到 `memory/analysis-YYYY-MM-DD.md`
- **错误日志**: 分析失败保存到 `memory/errors-YYYY-MM-DD.md`
- **学习改进**: 从错误中学习，更新 `memory/learnings.md`

### 目录结构
```
memory/
├── YYYY-MM-DD.md           # 每日分析记录
├── errors-YYYY-MM-DD.md   # 错误日志
└── learnings.md            # 改进记录
```

## 工具使用

**分析工具**: 通过 Skills 调用 LLM 进行分析

**数据获取**: 使用 yfinance、Alpha Vantage 等获取市场数据

**风险评估**: 基于量化模型评估风险等级

## 安全准则

- 不存储用户敏感信息（身份证、银行卡等）
- API 密钥仅保存在环境变量或 TOOLS.md
- 分析结果仅用于参考，不作为投资依据
- 外部 API 调用有超时保护

## 心跳任务

见 `HEARTBEAT.md` - 配置定期检查任务

---

_遵循此规范确保分析流程一致性和可追溯性。_
