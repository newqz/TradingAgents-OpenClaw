"""
Skill Importer - 解决 Python 3.6 的模块导入问题
使用 importlib 动态导入 Skills
"""

import importlib
import importlib.util
import os
import sys
from typing import Any, Callable, Optional


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS_DIR = os.path.join(PROJECT_ROOT, 'skills')

# 已加载的模块缓存
_loaded_modules = {}


def import_skill_module(skill_name: str, module_name: str):
    """
    动态导入 skill 模块
    
    Args:
        skill_name: skill 目录名 (如 'skill_tao_fundamental')
        module_name: 模块文件名 (如 'fundamental_analyst')
    
    Returns:
        导入的模块对象
    """
    skill_path = os.path.join(SKILLS_DIR, skill_name, f"{module_name}.py")
    
    if not os.path.exists(skill_path):
        raise FileNotFoundError(f"Module not found: {skill_path}")
    
    spec = importlib.util.spec_from_file_location(module_name, skill_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module: {module_name}")
    
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    return module


def import_skill_class(skill_name: str, module_name: str, class_name: str):
    """
    动态导入 skill 类
    
    Args:
        skill_name: skill 目录名 (如 'skill_tao_fundamental')
        module_name: 模块文件名 (如 'fundamental_analyst')
        class_name: 类名 (如 'FundamentalAnalyst')
    
    Returns:
        导入的类
    """
    module = import_skill_module(skill_name, module_name)
    return getattr(module, class_name)


# 预定义的导入映射
SKILL_CLASSES = {
    'fundamental_analyst': ('skill_tao_fundamental', 'fundamental_analyst', 'FundamentalAnalyst'),
    'technical_analyst': ('skill_tao_technical', 'technical_analyst', 'TechnicalAnalyst'),
    'sentiment_analyst': ('skill_tao_sentiment', 'sentiment_analyst', 'SentimentAnalyst'),
    'researcher_bull': ('skill_tao_researcher_bull', 'researcher_bull', 'BullResearcher'),
    'researcher_bear': ('skill_tao_researcher_bear', 'researcher_bear', 'BearResearcher'),
    'research_manager': ('skill_tao_research_manager', 'research_manager', 'ResearchManager'),
    'risk_manager': ('skill_tao_risk_manager', 'risk_manager', 'RiskManager'),
    'traders': ('skill_tao_trader', 'traders', None),  # traders.py 有多个类
}


def get_skill_class(key: str):
    """
    获取 skill 类
    
    Args:
        key: 预定义的 key (如 'fundamental_analyst')
    
    Returns:
        类对象
    """
    if key not in SKILL_CLASSES:
        raise KeyError(f"Unknown skill key: {key}")
    
    skill_name, module_name, class_name = SKILL_CLASSES[key]
    return import_skill_class(skill_name, module_name, class_name)
