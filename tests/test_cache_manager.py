# -*- coding: utf-8 -*-
"""
Cache Manager Tests
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skills.skill_tao_data.data_provider import CacheManager


class TestCacheManager:
    """CacheManager 测试"""
    
    def test_basic_cache(self):
        """测试基本缓存功能"""
        cache = CacheManager(enabled=True)
        
        # 设置缓存
        cache.set("test_method", "test_value", symbol="TEST")
        
        # 获取缓存
        result = cache.get("test_method", symbol="TEST")
        assert result == "test_value"
    
    def test_cache_disabled(self):
        """测试禁用缓存"""
        cache = CacheManager(enabled=False)
        
        cache.set("test_method", "test_value", symbol="TEST")
        result = cache.get("test_method", symbol="TEST")
        
        assert result is None  # 禁用后不返回缓存
    
    def test_lru_eviction(self):
        """测试LRU淘汰"""
        cache = CacheManager(enabled=True, maxsize=10)
        
        # 填充超过容量
        for i in range(15):
            cache.set("method", f"value_{i}", key=i)
        
        stats = cache.get_stats()
        assert stats["size"] == 10  # 不超过容量
        assert cache.get("method", key=0) is None  # 最早的被淘汰
    
    def test_ttl_expiration(self):
        """测试TTL过期"""
        import time
        cache = CacheManager(enabled=True, ttl_minutes=0.001)  # 1ms过期
        
        cache.set("method", "value", key="test")
        time.sleep(0.01)  # 等待过期
        
        result = cache.get("method", key="test")
        assert result is None  # 已过期
    
    def test_get_stats(self):
        """测试统计信息"""
        cache = CacheManager(enabled=True, maxsize=100, ttl_minutes=60)
        
        cache.set("method", "value", symbol="AAPL")
        stats = cache.get_stats()
        
        assert stats["maxsize"] == 100
        assert stats["ttl_minutes"] == 60
        assert stats["size"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
