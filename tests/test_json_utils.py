# -*- coding: utf-8 -*-
"""
JSON Utils Tests
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.json_utils import safe_json_parse, extract_json_from_text


class TestSafeJsonParse:
    """safe_json_parse 测试"""
    
    def test_valid_json(self):
        """测试有效JSON"""
        result = safe_json_parse('{"signal": "buy", "confidence": 0.8}')
        assert result is not None
        assert result["signal"] == "buy"
        assert result["confidence"] == 0.8
    
    def test_json_in_code_block(self):
        """测试代码块中的JSON"""
        text = '\`\`\`json\n{"signal": "sell"}\n\`\`\`'
        result = safe_json_parse(text)
        assert result is not None
        assert result["signal"] == "sell"
    
    def test_invalid_json_returns_default(self):
        """测试无效JSON返回默认值"""
        result = safe_json_parse("not json", default=None)
        assert result is None
    
    def test_missing_required_keys(self):
        """测试缺少必填字段"""
        result = safe_json_parse(
            '{"signal": "buy"}',
            validate_keys=["signal", "confidence", "reasoning"]
        )
        assert result is None
    
    def test_confidence_bounds(self):
        """测试置信度边界"""
        # 超出范围的置信度应该在解析后的数据中保留原始值
        result = safe_json_parse('{"signal": "buy", "confidence": 1.5}')
        assert result is not None
        assert result["confidence"] == 1.5


class TestExtractJsonFromText:
    """extract_json_from_text 测试"""
    
    def test_extract_from_plain_text(self):
        """从纯文本提取JSON"""
        text = '{"key": "value"}'
        result = extract_json_from_text(text)
        assert result == {"key": "value"}
    
    def test_extract_from_code_block(self):
        """从代码块提取JSON"""
        text = 'Here is the result:\n\`\`\`json\n{"data": 123}\n\`\`\`'
        result = extract_json_from_text(text)
        assert result == {"data": 123}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
