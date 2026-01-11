"""Advanced caching system for bot responses."""

import hashlib
import json
import time
from pathlib import Path
from typing import Dict, Optional, Union


class ResponseCache:
    """Simple file-based cache for frequent queries."""
    
    def __init__(self, cache_dir: str = "./cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.hits = 0
        self.misses = 0
    
    def _get_cache_key(self, query: str) -> str:
        """Generate cache key from query."""
        normalized = query.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def get(self, query: str, max_age: int = 1800) -> Optional[str]:
        """Get cached response if exists and not expired."""
        key = self._get_cache_key(query)
        cache_file = self.cache_dir / f"{key}.json"
        
        if not cache_file.exists():
            self.misses += 1
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check expiration
            age = time.time() - data['timestamp']
            if age > max_age:
                cache_file.unlink()  # Delete expired cache
                self.misses += 1
                return None
            
            self.hits += 1
            return data['response']
        except Exception:
            self.misses += 1
            return None
    
    def set(self, query: str, response: str):
        """Save response to cache."""
        key = self._get_cache_key(query)
        cache_file = self.cache_dir / f"{key}.json"
        
        data = {
            'query': query,
            'response': response,
            'timestamp': time.time()
        }
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
    
    def get_stats(self) -> Dict[str, Union[int, str]]:
        """Get cache statistics."""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        
        return {
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': f"{hit_rate:.1f}%",
            'cached_items': len(list(self.cache_dir.glob('*.json')))
        }


# Global cache instance
cache = ResponseCache()
