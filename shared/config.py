"""
项目路径配置模块
自动检测项目根目录并设置 Python path
"""

import os
import sys

# 获取项目根目录 (master-agent 的父目录)
_CURRENT_FILE = os.path.abspath(__file__)
PROJECT_ROOT = os.path.dirname(os.path.dirname(_CURRENT_FILE))  # shared/ -> 项目根

# Skill 目录
SKILLS_DIR = os.path.join(PROJECT_ROOT, 'skills')
MASTER_AGENT_DIR = os.path.join(PROJECT_ROOT, 'master-agent')

def setup_paths():
    """设置 Python path"""
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)
    
    # 添加各 skill 路径
    skill_dirs = [
        'skill-tao-fundamental',
        'skill-tao-technical',
        'skill-tao-sentiment',
        'skill-tao-researcher-bull',
        'skill-tao-researcher-bear',
        'skill-tao-research-manager',
        'skill-tao-risk-manager',
        'skill-tao-trader',
        'skill-tao-trader-bull',
        'skill-tao-trader-neutral',
        'skill-tao-trader-bear',
        'skill_tao_data',  # 注意：使用下划线因为 Python 模块名不能含连字符
    ]
    
    for skill_dir in skill_dirs:
        full_path = os.path.join(SKILLS_DIR, skill_dir)
        if os.path.isdir(full_path) and full_path not in sys.path:
            sys.path.insert(0, full_path)
    
    # 添加 master-agent
    if MASTER_AGENT_DIR not in sys.path:
        sys.path.insert(0, MASTER_AGENT_DIR)

# 自动设置路径
setup_paths()
