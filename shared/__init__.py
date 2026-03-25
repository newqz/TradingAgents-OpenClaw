# -*- coding: utf-8 -*-
"""
shared package - 共享模块
"""

from .json_utils import (
    safe_json_parse,
    parse_with_validation,
    extract_json_from_text,
    robust_json_loads,
    JSONParseError,
)
from .state_machine import (
    StateMachine,
    StateTransitionError,
    validate_state_transition,
    validate,
    get_next_states,
)
from .interfaces import (
    BaseAnalyst,
    BaseResearcher,
    BaseTrader,
    BaseRiskManager,
    BaseDataProvider,
    validate_analyst,
    validate_trader,
)
from .logging_config import (
    setup_logging,
    get_logger,
    debug,
    info,
    warning,
    error,
    critical,
)
from .llm_client import (
    get_llm_client,
    get_model_for_provider,
)

__all__ = [
    # JSON utilities
    "safe_json_parse",
    "parse_with_validation", 
    "extract_json_from_text",
    "robust_json_loads",
    "JSONParseError",
    # State machine
    "StateMachine",
    "StateTransitionError",
    "validate_state_transition",
    "validate",
    "get_next_states",
    # Interfaces
    "BaseAnalyst",
    "BaseResearcher",
    "BaseTrader",
    "BaseRiskManager",
    "BaseDataProvider",
    "validate_analyst",
    "validate_trader",
    # Logging
    "setup_logging",
    "get_logger",
    "debug",
    "info",
    "warning",
    "error",
    "critical",
    # LLM Client
    "get_llm_client",
    "get_model_for_provider",
]
