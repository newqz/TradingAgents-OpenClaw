# SKILLS.md - TradingAgents Skills

## 项目 Skills

### Phase 1: 分析师 Skills

| Skill | 目录 | 功能 |
|-------|------|------|
| skill-tao-fundamental | `skills/skill-tao-fundamental/` | 基本面分析 |
| skill-tao-technical | `skills/skill-tao-technical/` | 技术面分析 |
| skill-tao-sentiment | `skills/skill-tao-sentiment/` | 情绪面分析 |

### Phase 2: 研究员 Skills

| Skill | 目录 | 功能 |
|-------|------|------|
| skill-tao-researcher-bull | `skills/skill-tao-researcher-bull/` | 看多研究员 |
| skill-tao-researcher-bear | `skills/skill-tao-researcher-bear/` | 看空研究员 |
| skill-tao-research-manager | `skills/skill-tao-research-manager/` | 研究整合 |

### Phase 3: 交易员 Skills

| Skill | 目录 | 功能 |
|-------|------|------|
| skill-tao-trader | `skills/skill-tao-trader/` | 交易决策 (整合) |
| skill-tao-risk-manager | `skills/skill-tao-risk-manager/` | 风险管理 |

## Skill YAML 格式

每个 Skill 目录包含 `SKILL.md`，格式：

```yaml
---
name: skill-tao-{name}
description: "描述：当...时激活"
metadata:
  { "openclaw": { "emoji": "📊", "requires": {} } }
---

# Skill 文档

## 描述
...

## 调用方式
...

## 输入/输出
...
```

## OpenClaw Skill 发现机制

1. OpenClaw 扫描 `skills/` 目录
2. 查找含 YAML frontmatter 的 `SKILL.md`
3. 根据 `description` 匹配用户请求
4. 激活对应的 Skill

## 调用 Skills

### 方式 A: 直接导入 (Python)

```python
import sys
from bootstrap import setup
setup()

from skill_tao_fundamental.fundamental_analyst import FundamentalAnalyst

analyst = FundamentalAnalyst()
result = analyst.analyze({
    "stock_symbol": "AAPL",
    "analysis_date": "2026-03-25"
})
```

### 方式 B: OpenClaw sessions_spawn

```javascript
sessions_spawn({
    runtime: "subagent",
    task: "分析 AAPL 的基本面",
    cwd: "/root/.openclaw/workspace/TradingAgents-OpenClaw"
})
```

## Skill 开发指南

1. 创建目录: `skills/skill-{name}/`
2. 创建 `SKILL.md` - 定义 Skill 元数据
3. 创建 Python 模块 - 实现分析逻辑
4. 添加单元测试 - 确保功能正确
