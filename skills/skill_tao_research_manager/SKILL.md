---
name: skill-tao-research-manager
description: "研究员整合管理器。综合多方研究观点，进行多空辩论，生成最终研究共识。当需要研究员辩论、投资决策研究时激活。"
metadata:
  {
    "openclaw": { "emoji": "🔬", "requires": {} }
  }
---

# Skill: skill-tao-research-manager

## 描述

研究员整合管理器，负责：
1. 调度 Bull/Bear 研究员进行多轮辩论
2. 综合双方观点生成研究共识
3. 输出最终投资建议信号

## 调用方式

```python
from skill_tao_research_manager.research_manager import ResearchManager

manager = ResearchManager(config={"llm_provider": "openai", "model": "gpt-4o"})
summary = manager.synthesize(
    symbol="AAPL",
    debate_history=[bull_view, bear_view],
    analyst_reports={"fundamental": f_report, "technical": t_report},
    trace_id="uuid"
)
```

## 输入

```json
{
  "symbol": "AAPL",
  "debate_history": [
    {"round": 1, "bull_view": {...}, "bear_view": {...}}
  ],
  "analyst_reports": {
    "fundamental": {...},
    "technical": {...},
    "sentiment": {...}
  },
  "trace_id": "uuid"
}
```

## 输出

```json
{
  "overall_signal": "buy",
  "confidence": 0.78,
  "consensus_level": 0.72,
  "key_insights": ["增长前景乐观", "估值合理"],
  "contradictions": ["竞争加剧", "宏观经济不确定性"],
  "reasoning": "综合研判..."
}
```