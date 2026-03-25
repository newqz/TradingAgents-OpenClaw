# -*- coding: utf-8 -*-
"""
状态机验证模块
确保分析状态转换的合法性和一致性
"""

from typing import Dict, Set, Optional, Callable
from functools import wraps

from .models import AnalysisStatus


class StateTransitionError(Exception):
    """非法状态转换异常"""
    def __init__(self, current: AnalysisStatus, target: AnalysisStatus, allowed: Set[AnalysisStatus]):
        self.current = current
        self.target = target
        self.allowed = allowed
        super().__init__(
            f"Invalid state transition: {current.value} → {target.value}. "
            f"Allowed transitions: {[s.value for s in allowed]}"
        )


class StateMachine:
    """
    状态机验证器
    
    确保 AnalysisState 的状态转换遵循合法路径:
    INITIAL → ANALYZING → RESEARCHING → DEBATING → RISK_ASSESSING → FINALIZING → COMPLETED/FAILED
    """
    
    # 合法状态转换映射
    VALID_TRANSITIONS: Dict[AnalysisStatus, Set[AnalysisStatus]] = {
        AnalysisStatus.INITIAL: {AnalysisStatus.ANALYZING, AnalysisStatus.FAILED},
        AnalysisStatus.ANALYZING: {AnalysisStatus.RESEARCHING, AnalysisStatus.FAILED},
        AnalysisStatus.RESEARCHING: {AnalysisStatus.DEBATING, AnalysisStatus.FAILED},
        AnalysisStatus.DEBATING: {AnalysisStatus.RISK_ASSESSING, AnalysisStatus.FAILED},
        AnalysisStatus.RISK_ASSESSING: {AnalysisStatus.FINALIZING, AnalysisStatus.FAILED},
        AnalysisStatus.FINALIZING: {AnalysisStatus.COMPLETED, AnalysisStatus.FAILED},
        AnalysisStatus.COMPLETED: set(),  # 终态
        AnalysisStatus.FAILED: set(),    # 终态
    }
    
    # 终态集合
    TERMINAL_STATES: Set[AnalysisStatus] = {AnalysisStatus.COMPLETED, AnalysisStatus.FAILED}
    
    # 起始状态
    START_STATE: AnalysisStatus = AnalysisStatus.INITIAL
    
    @classmethod
    def validate_transition(cls, current: AnalysisStatus, target: AnalysisStatus) -> bool:
        """
        验证状态转换是否合法
        
        Args:
            current: 当前状态
            target: 目标状态
            
        Returns:
            是否允许转换
        """
        allowed = cls.VALID_TRANSITIONS.get(current, set())
        return target in allowed
    
    @classmethod
    def get_allowed_transitions(cls, current: AnalysisStatus) -> Set[AnalysisStatus]:
        """
        获取从当前状态可以转换到的所有状态
        
        Args:
            current: 当前状态
            
        Returns:
            允许的目标状态集合
        """
        return cls.VALID_TRANSITIONS.get(current, set())
    
    @classmethod
    def is_terminal(cls, status: AnalysisStatus) -> bool:
        """检查是否为终态"""
        return status in cls.TERMINAL_STATES
    
    @classmethod
    def is_valid_sequence(cls, transitions: list) -> bool:
        """
        验证状态序列是否合法
        
        Args:
            transitions: 状态列表，如 [INITIAL, ANALYZING, RESEARCHING]
            
        Returns:
            是否为合法序列
        """
        if not transitions:
            return True
        
        # 必须从初始状态开始
        if transitions[0] != cls.START_STATE:
            return False
        
        # 检查每个转换
        for i in range(len(transitions) - 1):
            if not cls.validate_transition(transitions[i], transitions[i + 1]):
                return False
        
        return True
    
    @classmethod
    def assert_transition(cls, current: AnalysisStatus, target: AnalysisStatus):
        """
        验证转换，不合法则抛出异常
        
        Raises:
            StateTransitionError: 非法转换
        """
        if not cls.validate_transition(current, target):
            allowed = cls.get_allowed_transitions(current)
            raise StateTransitionError(current, target, allowed)


def validate_state_transition(func: Callable) -> Callable:
    """
    装饰器: 自动验证状态转换
    
    使用方式:
        @validate_state_transition
        def update_status(self, new_status):
            ...
    
    要求方法所在对象的 status 字段可访问
    """
    @wraps(func)
    def wrapper(self, new_status, *args, **kwargs):
        # 获取当前状态
        current = getattr(self, 'status', None)
        if current is not None:
            # 验证转换
            StateMachine.assert_transition(current, new_status)
        
        return func(self, new_status, *args, **kwargs)
    
    return wrapper


# 便捷函数
def validate(state: str, new_state: str) -> bool:
    """
    验证状态转换 (字符串版本)
    
    Args:
        state: 当前状态字符串
        new_state: 目标状态字符串
        
    Returns:
        是否允许转换
    """
    try:
        current = AnalysisStatus(state)
        target = AnalysisStatus(new_state)
        return StateMachine.validate_transition(current, target)
    except ValueError:
        return False


def get_next_states(state: str) -> list:
    """
    获取可以转换到的下一个状态列表
    
    Args:
        state: 当前状态字符串
        
    Returns:
        下一个可能状态列表
    """
    try:
        current = AnalysisStatus(state)
        return [s.value for s in StateMachine.get_allowed_transitions(current)]
    except ValueError:
        return []
