#!/usr/bin/env python3
"""
Performance optimizations for GovQuery backend
"""

import asyncio
import time
from functools import lru_cache
from typing import Dict, Any, List
import json
import os

# Global cache for schemas
_schema_cache: Dict[str, Dict[str, Any]] = {}
_cache_timestamps: Dict[str, float] = {}
CACHE_TTL = 300  # 5 minutes

@lru_cache(maxsize=128)
def get_cached_schema(table_code: str) -> Dict[str, Any]:
    """Get schema with LRU caching"""
    schema_path = f"schemas/{table_code}.json"
    
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema {table_code} not found")
    
    with open(schema_path, 'r') as f:
        return json.load(f)

def get_schema_with_ttl(table_code: str) -> Dict[str, Any]:
    """Get schema with TTL-based caching"""
    current_time = time.time()
    
    # Check if we have a cached version that's still valid
    if (table_code in _schema_cache and 
        table_code in _cache_timestamps and
        current_time - _cache_timestamps[table_code] < CACHE_TTL):
        return _schema_cache[table_code]
    
    # Load fresh schema
    schema_path = f"schemas/{table_code}.json"
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema {table_code} not found")
    
    with open(schema_path, 'r') as f:
        schema = json.load(f)
    
    # Cache it
    _schema_cache[table_code] = schema
    _cache_timestamps[table_code] = current_time
    
    return schema

def preload_common_schemas():
    """Preload commonly used schemas"""
    common_tables = ["B01001", "B19013", "B02001", "B15003", "DP02"]
    
    for table_code in common_tables:
        try:
            get_schema_with_ttl(table_code)
            print(f"✅ Preloaded schema: {table_code}")
        except FileNotFoundError:
            print(f"⚠️ Schema not found: {table_code}")

def clear_cache():
    """Clear all caches"""
    global _schema_cache, _cache_timestamps
    _schema_cache.clear()
    _cache_timestamps.clear()
    get_cached_schema.cache_clear()
    print("🧹 Cache cleared")

def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics"""
    return {
        "schema_cache_size": len(_schema_cache),
        "lru_cache_size": get_cached_schema.cache_info().currsize,
        "lru_cache_hits": get_cached_schema.cache_info().hits,
        "lru_cache_misses": get_cached_schema.cache_info().misses,
        "cache_hit_rate": get_cached_schema.cache_info().hits / 
                         max(1, get_cached_schema.cache_info().hits + get_cached_schema.cache_info().misses)
    }

# Performance monitoring
class PerformanceMonitor:
    def __init__(self):
        self.request_times: List[float] = []
        self.error_count = 0
        self.total_requests = 0
    
    def record_request(self, duration: float, success: bool = True):
        self.request_times.append(duration)
        self.total_requests += 1
        if not success:
            self.error_count += 1
        
        # Keep only last 100 requests
        if len(self.request_times) > 100:
            self.request_times = self.request_times[-100:]
    
    def get_stats(self) -> Dict[str, Any]:
        if not self.request_times:
            return {"avg_response_time": 0, "error_rate": 0}
        
        avg_time = sum(self.request_times) / len(self.request_times)
        error_rate = self.error_count / max(1, self.total_requests)
        
        return {
            "avg_response_time": avg_time,
            "error_rate": error_rate,
            "total_requests": self.total_requests,
            "recent_requests": len(self.request_times)
        }

# Global performance monitor
perf_monitor = PerformanceMonitor()

# Decorator for timing functions
def time_function(func):
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            perf_monitor.record_request(time.time() - start_time, success=True)
            return result
        except Exception as e:
            perf_monitor.record_request(time.time() - start_time, success=False)
            raise e
    
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            perf_monitor.record_request(time.time() - start_time, success=True)
            return result
        except Exception as e:
            perf_monitor.record_request(time.time() - start_time, success=False)
            raise e
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper

if __name__ == "__main__":
    # Test the performance optimizations
    print("🚀 Testing performance optimizations...")
    
    # Preload schemas
    preload_common_schemas()
    
    # Test caching
    start = time.time()
    schema1 = get_schema_with_ttl("B01001")
    first_load = time.time() - start
    
    start = time.time()
    schema2 = get_schema_with_ttl("B01001")
    cached_load = time.time() - start
    
    print(f"📊 First load: {first_load:.3f}s")
    print(f"📊 Cached load: {cached_load:.3f}s")
    if cached_load > 0:
        print(f"📊 Speedup: {first_load/cached_load:.1f}x")
    else:
        print("📊 Speedup: N/A (cached load too fast to measure)")
    
    # Show cache stats
    print(f"📈 Cache stats: {get_cache_stats()}")
    print(f"📈 Performance stats: {perf_monitor.get_stats()}")
