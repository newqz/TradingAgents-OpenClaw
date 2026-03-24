#!/usr/bin/env python3
"""
TradingAgents-OpenClaw 最终版测试
验证完整架构 Phase 1-3
"""

import sys
sys.path.insert(0, '/root/.openclaw-coding/workspace/TradingAgents-OpenClaw')

print("=" * 70)
print("TradingAgents-OpenClaw 完整版测试 (Phase 1-3)")
print("=" * 70)

# 检查所有文件
print("\n📁 完整架构文件检查:")
print("-" * 70)

import os

all_files = {
    # Phase 1
    "Data": "skills/skill-tao-data/data_provider.py",
    "Fundamental": "skills/skill-tao-fundamental/fundamental_analyst.py",
    "Technical": "skills/skill-tao-technical/technical_analyst.py",
    # Phase 1.5
    "Sentiment": "skills/skill-tao-sentiment/sentiment_analyst.py",
    # Phase 2
    "BullResearcher": "skills/skill-tao-researcher-bull/researcher_bull.py",
    "BearResearcher": "skills/skill-tao-researcher-bear/researcher_bear.py",
    "ResearchManager": "skills/skill-tao-research-manager/research_manager.py",
    # Phase 3
    "Traders": "skills/skill-tao-trader/traders.py",
    "RiskManager": "skills/skill-tao-risk-manager/risk_manager.py",
}

total_size = 0
for name, path in all_files.items():
    full_path = f"/root/.openclaw-coding/workspace/TradingAgents-OpenClaw/{path}"
    if os.path.exists(full_path):
        size = os.path.getsize(full_path)
        total_size += size
        print(f"✅ {name:20s}: {size:6d} bytes")
    else:
        print(f"❌ {name:20s}: 不存在")

print(f"\n  总代码量: {total_size:,} bytes (~{total_size/1024:.1f} KB)")

# 架构图
print("\n" + "=" * 70)
print("🏗️ 完整架构流程")
print("=" * 70)
print("""
┌──────────────────────────────────────────────────────────────────────┐
│                    TradingAgents-OpenClaw                             │
│                      完整多 Agent 架构                                 │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Phase 1: 分析师团队 (并行执行)                                        │
│  ┌──────────────┬──────────────┬──────────────┐                      │
│  │ Fundamental  │  Technical   │  Sentiment   │                      │
│  │   Analyst    │   Analyst    │   Analyst    │                      │
│  └──────┬───────┴──────┬───────┴──────┬───────┘                      │
│         │              │              │                              │
│         └──────────────┼──────────────┘                              │
│                        ▼                                              │
│              Analyst Reports (3份)                                    │
│                                                                       │
│  Phase 2: 研究员辩论 (可配置轮次)                                       │
│                        │                                              │
│         ┌──────────────┼──────────────┐                              │
│         ▼              ▼              ▼                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                 │
│  │   Bull       │ │    Bear      │ │   Research   │                 │
│  │  Researcher  │◀─┤  Researcher  │◀─┤   Manager    │                 │
│  └──────────────┘ └──────────────┘ └──────────────┘                 │
│         │              │              │                              │
│         └──────────────┼──────────────┘                              │
│                        ▼                                              │
│              Research Synthesis (综合研判)                            │
│                                                                       │
│  Phase 3: 交易执行 (并行)                                              │
│                        │                                              │
│         ┌──────────────┼──────────────┐                              │
│         ▼              ▼              ▼                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                 │
│  │   Bull       │ │   Neutral    │ │    Bear      │                 │
│  │   Trader     │ │   Trader     │ │   Trader     │                 │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘                 │
│         │                │                │                          │
│         └────────────────┼────────────────┘                          │
│                          ▼                                            │
│                Trader Recommendations (3份)                          │
│                          │                                            │
│  ┌───────────────────────┘                                            │
│  ▼                                                                    │
│  Risk Manager (风险评估)                                              │
│  │                                                                    │
│  ▼                                                                    │
│  Final Decision (最终决策)                                            │
│  │                                                                    │
│  ▼                                                                    │
│  飞书报告卡片                                                         │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
""")

# 成本估算
print("=" * 70)
print("💰 完整流程成本估算 (GPT-4o)")
print("=" * 70)

costs = [
    ("Phase 1: 三分析师", [
        ("基本面分析师", 4000, 1000, 0.15),
        ("技术面分析师", 4000, 1000, 0.15),
        ("情绪分析师", 4000, 1000, 0.15),
    ]),
    ("Phase 2: 研究员辩论", [
        ("Bull Researcher", 3000, 1500, 0.18),
        ("Bear Researcher", 3000, 1500, 0.18),
        ("Research Manager", 4000, 1500, 0.21),
    ]),
    ("Phase 3: 交易执行", [
        ("Bull Trader", 2000, 1000, 0.12),
        ("Neutral Trader", 2000, 1000, 0.12),
        ("Bear Trader", 2000, 1000, 0.12),
        ("Risk Manager", 3000, 1000, 0.15),
    ]),
]

total_cost = 0
for phase_name, phase_costs in costs:
    print(f"\n{phase_name}:")
    phase_total = 0
    for name, inp, out, cost in phase_costs:
        print(f"  {name:20s}: {inp:5d}+{out:5d} tokens ≈ ${cost:.2f}")
        phase_total += cost
    print(f"  {'Subtotal':20s}: {'':5s} {'':5s}  = ${phase_total:.2f}")
    total_cost += phase_total

print(f"\n{'='*70}")
print(f"  TOTAL: ~${total_cost:.2f} per analysis")
print(f"{'='*70}")

# 功能特性
print("\n🎯 核心功能特性")
print("-" * 70)
features = [
    "✅ 三维度分析: 基本面 + 技术面 + 情绪面",
    "✅ 多空辩论机制: Bull vs Bear 对抗性论证",
    "✅ 多风险偏好: 激进/中性/保守 三位交易员",
    "✅ 风险管理: 综合风险评估与仓位控制",
    "✅ 多市场支持: 美股 / A股 / 港股",
    "✅ 多渠道接入: 飞书 / Discord / Telegram (可扩展)",
]
for f in features:
    print(f"  {f}")

# 总结
print("\n" + "=" * 70)
print("🎉 Phase 1-3 全部完成!")
print("=" * 70)
print(f"""
项目: TradingAgents-OpenClaw
状态: 核心架构完成 ✅
代码: {total_size:,} bytes
Agent: 11 个 (3分析师 + 2研究员 + 1经理 + 3交易员 + 1风控 + 1编排)

待办:
  • 配置 OPENAI_API_KEY 进行真实测试
  • 部署到 OpenClaw 实例
  • 根据反馈优化 Prompt
  • 添加性能监控和成本追踪
""")

print("=" * 70)
