# -*- coding: utf-8 -*-
"""
State Machine Tests
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.state_machine import StateMachine, StateTransitionError
from shared.models import AnalysisStatus


class TestStateMachine:
    """状态机测试"""
    
    def test_valid_transitions(self):
        """测试合法状态转换"""
        assert StateMachine.validate_transition(
            AnalysisStatus.INITIAL, AnalysisStatus.ANALYZING
        )
        assert StateMachine.validate_transition(
            AnalysisStatus.ANALYZING, AnalysisStatus.RESEARCHING
        )
        assert StateMachine.validate_transition(
            AnalysisStatus.RESEARCHING, AnalysisStatus.DEBATING
        )
        assert StateMachine.validate_transition(
            AnalysisStatus.DEBATING, AnalysisStatus.RISK_ASSESSING
        )
        assert StateMachine.validate_transition(
            AnalysisStatus.RISK_ASSESSING, AnalysisStatus.FINALIZING
        )
        assert StateMachine.validate_transition(
            AnalysisStatus.FINALIZING, AnalysisStatus.COMPLETED
        )
    
    def test_invalid_transitions(self):
        """测试非法状态转换"""
        # 不能跳过中间状态
        assert not StateMachine.validate_transition(
            AnalysisStatus.INITIAL, AnalysisStatus.COMPLETED
        )
        assert not StateMachine.validate_transition(
            AnalysisStatus.ANALYZING, AnalysisStatus.DEBATING
        )
        # 不能后退
        assert not StateMachine.validate_transition(
            AnalysisStatus.COMPLETED, AnalysisStatus.INITIAL
        )
    
    def test_failure_transition(self):
        """测试失败转换"""
        assert StateMachine.validate_transition(
            AnalysisStatus.INITIAL, AnalysisStatus.FAILED
        )
        assert StateMachine.validate_transition(
            AnalysisStatus.ANALYZING, AnalysisStatus.FAILED
        )
        assert StateMachine.validate_transition(
            AnalysisStatus.RESEARCHING, AnalysisStatus.FAILED
        )
    
    def test_terminal_states(self):
        """测试终态"""
        assert StateMachine.is_terminal(AnalysisStatus.COMPLETED)
        assert StateMachine.is_terminal(AnalysisStatus.FAILED)
        assert not StateMachine.is_terminal(AnalysisStatus.INITIAL)
        assert not StateMachine.is_terminal(AnalysisStatus.ANALYZING)
    
    def test_assert_transition_raises(self):
        """测试assert转换抛出异常"""
        with pytest.raises(StateTransitionError):
            StateMachine.assert_transition(
                AnalysisStatus.INITIAL, AnalysisStatus.COMPLETED
            )
    
    def test_valid_sequence(self):
        """测试有效序列"""
        sequence = [
            AnalysisStatus.INITIAL,
            AnalysisStatus.ANALYZING,
            AnalysisStatus.RESEARCHING,
            AnalysisStatus.COMPLETED
        ]
        assert StateMachine.is_valid_sequence(sequence)
    
    def test_invalid_sequence(self):
        """测试无效序列"""
        sequence = [
            AnalysisStatus.INITIAL,
            AnalysisStatus.COMPLETED  # 跳过中间状态
        ]
        assert not StateMachine.is_valid_sequence(sequence)


class TestAnalysisStateStatusUpdate:
    """AnalysisState 状态更新测试"""
    
    def test_valid_status_update(self):
        """测试有效状态更新"""
        from shared.models import AnalysisState
        
        state = AnalysisState(
            trace_id="test123",
            stock_symbol="AAPL",
            analysis_date="2024-01-01"
        )
        
        # 有效转换
        state.update_status(AnalysisStatus.ANALYZING)
        assert state.status == AnalysisStatus.ANALYZING
        
        state.update_status(AnalysisStatus.RESEARCHING)
        assert state.status == AnalysisStatus.RESEARCHING
    
    def test_invalid_status_update_raises(self):
        """测试无效状态更新抛出异常"""
        from shared.models import AnalysisState
        
        state = AnalysisState(
            trace_id="test123",
            stock_symbol="AAPL",
            analysis_date="2024-01-01"
        )
        
        with pytest.raises(ValueError):
            state.update_status(AnalysisStatus.COMPLETED)  # 非法跳跃


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
