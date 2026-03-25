# BOOTSTRAP.md - TradingAgents 首次启动

_这是 TradingAgents-OpenClaw 项目的首次启动指南。_

## 项目概述

TradingAgents 是一个三阶段量化交易分析系统：

1. **Phase 1**: 三分析师并行 (基本面/技术面/情绪面)
2. **Phase 2**: 研究员多空辩论 (Bull vs Bear)
3. **Phase 3**: 交易员决策 + 风险管理

## 快速开始

### 1. 检查环境

```bash
# 检查 Python 版本 (需要 3.8+)
python3 --version

# 检查必要的包
pip3 list | grep -E "openai|pandas|yfinance"
```

### 2. 配置 API 密钥

在环境变量或 `TOOLS.md` 中设置：

```bash
export OPENAI_API_KEY="sk-..."
export ALPHA_VANTAGE_API_KEY="..."  # 可选
```

### 3. 测试分析

```bash
cd /root/.openclaw/workspace/TradingAgents-OpenClaw

python3 -c "
import sys
from bootstrap import setup
setup()
from master_agent.orchestrator_phase3 import TradingOrchestrator

orchestrator = TradingOrchestrator()
print('✅ TradingAgents 初始化成功')
"
```

### 4. 运行测试

```bash
python3 test_phase1.py
python3 test_phase2.py
python3 test_phase3.py
```

## 部署到 OpenClaw Gateway

### 方式 A: 新建 Gateway 实例

```bash
# 创建新实例目录
mkdir -p /root/.openclaw-trading

# 复制项目文件
cp -r TradingAgents-OpenClaw /root/.openclaw-trading/workspace/

# 启动 Gateway
cd /root/.openclaw-trading
OPENCLAW_STATE_DIR=/root/.openclaw-trading nohup openclaw gateway run --port 18799 > /tmp/trading.log 2>&1 &
```

### 方式 B: 集成到现有实例

将 Skills 复制到系统目录：

```bash
cp -r skills/* /usr/local/lib/node_modules/openclaw/skills/
```

然后重启 Gateway。

## 验证部署

```bash
# 检查 Skills 是否被识别
openclaw skills list

# 测试分析命令
openclaw exec "分析 AAPL"
```

## 常见问题

### Q: Python 导入错误
A: 确保先运行 `from bootstrap import setup; setup()`

### Q: Skill 未识别
A: 检查 SKILL.md 是否有 YAML frontmatter

### Q: LLM 调用失败
A: 检查 OPENAI_API_KEY 环境变量

---

_完成后删除此文件：_ `rm BOOTSTRAP.md`
