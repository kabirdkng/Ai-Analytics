"""
Simple cache service to avoid repeated expensive API calls
"""
import asyncio
from typing import Dict, Optional
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)

class CacheService:
    def __init__(self):
        self._cache = {}
        self._cache_ttl = {}
        self.default_ttl = 300  # 5 minutes
    
    def _is_expired(self, key: str) -> bool:
        """Check if cache entry is expired"""
        if key not in self._cache_ttl:
            return True
        return datetime.now() > self._cache_ttl[key]
    
    def get(self, key: str) -> Optional[Dict]:
        """Get cached data if available and not expired"""
        if key in self._cache and not self._is_expired(key):
            logger.info(f"Cache hit for {key}")
            return self._cache[key]
        return None
    
    def set(self, key: str, value: Dict, ttl: Optional[int] = None) -> None:
        """Set cache entry with TTL"""
        ttl = ttl or self.default_ttl
        self._cache[key] = value
        self._cache_ttl[key] = datetime.now() + timedelta(seconds=ttl)
        logger.info(f"Cached data for {key}, expires in {ttl}s")
    
    def delete(self, key: str) -> None:
        """Delete cache entry"""
        if key in self._cache:
            del self._cache[key]
        if key in self._cache_ttl:
            del self._cache_ttl[key]
    
    def clear(self) -> None:
        """Clear all cache"""
        self._cache.clear()
        self._cache_ttl.clear()

# Global cache instance
cache = CacheService()