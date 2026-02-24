import json
import os
from datetime import datetime, timedelta

class CacheManager:
    """Manages caching of API calls to avoid rate limiting"""
    
    def __init__(self, cache_dir="./cache"):
        self.cache_dir = cache_dir
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
    
    def get_cache_file(self, key: str) -> str:
        """Get cache file path for a key"""
        return os.path.join(self.cache_dir, f"{key}.json")
    
    def set(self, key: str, value: dict, ttl_hours: int = 24):
        cache_file = self.get_cache_file(key)
        cache_data = {
            "value": value,
            "timestamp": datetime.now().isoformat(),
            "ttl_hours": ttl_hours
        }
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f)
    
    def get(self, key: str):
        cache_file = self.get_cache_file(key)
        
        if not os.path.exists(cache_file):
            return None
        
        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            
            timestamp = datetime.fromisoformat(cache_data["timestamp"])
            ttl_hours = cache_data["ttl_hours"]
            expiry_time = timestamp + timedelta(hours=ttl_hours)
            
            if datetime.now() > expiry_time:
                os.remove(cache_file)
                return None
            
            return cache_data["value"]
        except Exception as e:
            print(f"Error reading cache for {key}: {e}")
            return None
    
    def clear(self):
        """Clear all cache files"""
        for file in os.listdir(self.cache_dir):
            if file.endswith('.json'):
                os.remove(os.path.join(self.cache_dir, file))
    
    def clear_key(self, key: str):
        """Clear cache for a specific key"""
        cache_file = self.get_cache_file(key)
        if os.path.exists(cache_file):
            os.remove(cache_file)

cache_manager = CacheManager()