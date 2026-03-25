# -*- coding: utf-8 -*-
"""
JSON解析工具模块
提供安全的JSON解析功能，支持验证和错误处理
"""

import json
import re
from typing import Any, Dict, Optional, Type, TypeVar
from functools import wraps

T = TypeVar('T')


class JSONParseError(Exception):
    """JSON解析错误"""
    def __init__(self, message: str, raw_text: str = ""):
        super().__init__(message)
        self.raw_text = raw_text


def safe_json_parse(
    text: str,
    default: Optional[Dict] = None,
    validate_keys: Optional[list] = None
) -> Optional[Dict]:
    """
    安全解析JSON字符串
    
    Args:
        text: 原始文本
        default: 解析失败时返回的默认值
        validate_keys: 需要验证的必填键列表
        
    Returns:
        解析后的字典，或默认值
        
    Example:
        >>> result = safe_json_parse(llm_output, default={}, validate_keys=["signal", "confidence"])
    """
    if not text or not isinstance(text, str):
        return default
    
    # 尝试直接解析
    try:
        result = json.loads(text)
        if isinstance(result, dict):
            # 验证必填键
            if validate_keys:
                missing = [k for k in validate_keys if k not in result]
                if missing:
                    print(f"[WARN] JSON missing required keys: {missing}")
                    return default
            return result
        else:
            print(f"[WARN] JSON parsed but not a dict: {type(result)}")
            return default
    except json.JSONDecodeError as e:
        print(f"[WARN] JSON decode error: {e}")
        
        # 尝试提取JSON块 (处理 ```json ... ``` 格式)
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if json_match:
            try:
                result = json.loads(json_match.group(1).strip())
                if validate_keys:
                    missing = [k for k in validate_keys if k not in result]
                    if missing:
                        print(f"[WARN] Extracted JSON missing keys: {missing}")
                        return default
                return result
            except json.JSONDecodeError:
                pass
        
        # 尝试提取裸JSON对象 { ... }
        brace_match = re.search(r'\{[\s\S]*\}', text)
        if brace_match:
            try:
                result = json.loads(brace_match.group())
                if validate_keys:
                    missing = [k for k in validate_keys if k not in result]
                    if missing:
                        print(f"[WARN] Extracted JSON missing keys: {missing}")
                        return default
                return result
            except json.JSONDecodeError:
                pass
        
        print(f"[WARN] All JSON extraction attempts failed")
        return default


def parse_with_validation(
    text: str,
    schema: Dict[str, type],
    default: Optional[Dict] = None
) -> Optional[Dict]:
    """
    解析JSON并进行类型验证
    
    Args:
        text: 原始文本
        schema: 期望的键类型映射 {"key": type}
        default: 解析失败时返回的默认值
        
    Returns:
        验证后的字典，或默认值
    """
    result = safe_json_parse(text, default={})
    if not result:
        return default
    
    validated = {}
    for key, expected_type in schema.items():
        if key in result:
            value = result[key]
            # 类型检查 (允许None)
            if value is not None and not isinstance(value, expected_type):
                print(f"[WARN] Type mismatch for '{key}': expected {expected_type}, got {type(value)}")
                # 尝试类型转换
                if expected_type == str:
                    value = str(value)
                elif expected_type == float:
                    try:
                        value = float(value)
                    except (ValueError, TypeError):
                        value = 0.0
                elif expected_type == int:
                    try:
                        value = int(value)
                    except (ValueError, TypeError):
                        value = 0
            validated[key] = value
        else:
            validated[key] = None
    
    return validated


def extract_json_from_text(text: str) -> Optional[str]:
    """
    从文本中提取JSON字符串
    
    处理以下格式:
    - ```json ... ```
    - ``` ... ```
    - 裸 { ... }
    """
    if not text:
        return None
    
    # 尝试 ```json ... ```
    match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if match:
        return match.group(1).strip()
    
    # 尝试裸 { ... }
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        return match.group()
    
    return None


def robust_json_loads(text: str, default: Any = None) -> Any:
    """
    健壮的JSON加载器，尝试多种提取策略
    
    Args:
        text: 原始文本
        default: 默认返回值
        
    Returns:
        解析后的对象，或默认值
    """
    if not text:
        return default
    
    # 直接解析
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        pass
    
    # 提取后解析
    extracted = extract_json_from_text(text)
    if extracted:
        try:
            return json.loads(extracted)
        except (json.JSONDecodeError, TypeError):
            pass
    
    return default
