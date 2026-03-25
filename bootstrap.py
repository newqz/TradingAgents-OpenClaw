"""
TradingAgents-OpenClaw Bootstrap Module
设置 Python path 并导入核心组件

用法:
  from bootstrap import setup
  setup()  # 在任何导入之前调用
  
  from master_agent.orchestrator_phase3 import TradingOrchestrator
"""

import os
import sys

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

def setup():
    """设置 Python path"""
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)
    
    # 添加 master-agent
    master_agent_dir = os.path.join(PROJECT_ROOT, 'master-agent')
    if master_agent_dir not in sys.path:
        sys.path.insert(0, master_agent_dir)
    
    # 添加各 skill 路径
    skills_dir = os.path.join(PROJECT_ROOT, 'skills')
    if os.path.isdir(skills_dir):
        for skill_name in os.listdir(skills_dir):
            skill_path = os.path.join(skills_dir, skill_name)
            if os.path.isdir(skill_path) and skill_path not in sys.path:
                sys.path.insert(0, skill_path)

# 自动设置路径
setup()

# 导出核心组件
from shared.models import (
    AnalysisState,
    AnalysisStatus,
    FeishuCommand,
    TAOConfig,
    TradingAction,
    TradeDecision,
    TradingSignal,
    AgentType,
)

__all__ = ['setup', 'PROJECT_ROOT']