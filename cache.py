"""Smart caching system for frequently asked questions."""

import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

# Cache directory
CACHE_DIR = Path(".cache")
CACHE_DIR.mkdir(exist_ok=True)

# Cache expiration time (30 minutes)
CACHE_EXPIRATION = timedelta(minutes=30)


def get_cache_key(message: str) -> str:
    """Generate cache key from message."""
    normalized = message.lower().strip()
    return hashlib.md5(normalized.encode()).hexdigest()


def get_from_cache(message: str) -> Optional[str]:
    """Get response from cache if available and not expired."""
    cache_key = get_cache_key(message)
    cache_file = CACHE_DIR / f"{cache_key}.json"
    
    if not cache_file.exists():
        return None
    
    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Check if expired
        cached_time = datetime.fromisoformat(data["timestamp"])
        if datetime.now() - cached_time > CACHE_EXPIRATION:
            cache_file.unlink()  # Delete expired cache
            return None
        
        return data["response"]
    
    except Exception:
        return None


def save_to_cache(message: str, response: str):
    """Save response to cache."""
    cache_key = get_cache_key(message)
    cache_file = CACHE_DIR / f"{cache_key}.json"
    
    try:
        data = {
            "message": message,
            "response": response,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    except Exception:
        pass  # Silently fail if caching fails


def clear_expired_cache():
    """Clear all expired cache entries."""
    for cache_file in CACHE_DIR.glob("*.json"):
        try:
            with open(cache_file, "r") as f:
                data = json.load(f)
            
            cached_time = datetime.fromisoformat(data["timestamp"])
            if datetime.now() - cached_time > CACHE_EXPIRATION:
                cache_file.unlink()
        
        except Exception:
            continue


def get_cache_stats() -> Dict[str, int]:
    """Get cache statistics."""
    cache_files = list(CACHE_DIR.glob("*.json"))
    
    valid_count = 0
    expired_count = 0
    
    for cache_file in cache_files:
        try:
            with open(cache_file, "r") as f:
                data = json.load(f)
            
            cached_time = datetime.fromisoformat(data["timestamp"])
            if datetime.now() - cached_time > CACHE_EXPIRATION:
                expired_count += 1
            else:
                valid_count += 1
        except Exception:
            expired_count += 1
    
    return {
        "total_entries": len(cache_files),
        "valid_entries": valid_count,
        "expired_entries": expired_count
    }
