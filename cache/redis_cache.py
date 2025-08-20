"""
Redis Cache Implementation for Voice Cloning System
Provides caching for frequently accessed data, audio synthesis results, and translations
"""

import json
import pickle
import hashlib
from typing import Any, Optional, Union, Dict, List
from datetime import datetime, timedelta
import redis
from redis.exceptions import RedisError, ConnectionError, TimeoutError
import logging
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class CacheStrategy(Enum):
    """Cache strategy types"""
    LRU = "lru"
    TTL = "ttl"
    SLIDING = "sliding"

@dataclass
class CacheConfig:
    """Cache configuration settings"""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    max_connections: int = 10
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    retry_on_timeout: bool = True
    health_check_interval: int = 30
    default_ttl: int = 3600  # 1 hour
    max_memory_policy: str = "allkeys-lru"
    compression_threshold: int = 1024  # bytes

class RedisCache:
    """Redis cache implementation with advanced features"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.redis_client: Optional[redis.Redis] = None
        self._connect()
        self._configure()
    
    def _connect(self) -> None:
        """Establish Redis connection"""
        try:
            self.redis_client = redis.Redis(
                host=self.config.host,
                port=self.config.port,
                db=self.config.db,
                password=self.config.password,
                max_connections=self.config.max_connections,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout,
                retry_on_timeout=self.config.retry_on_timeout,
                health_check_interval=self.config.health_check_interval,
                decode_responses=False  # Keep as bytes for pickle
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Redis connection established successfully")
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
        except Exception as e:
            logger.error(f"Unexpected error connecting to Redis: {e}")
            self.redis_client = None
    
    def _configure(self) -> None:
        """Configure Redis settings"""
        if not self.redis_client:
            return
        
        try:
            # Set memory policy
            self.redis_client.config_set("maxmemory-policy", self.config.max_memory_policy)
            
            # Enable compression if available
            if hasattr(self.redis_client, 'config_set'):
                self.redis_client.config_set("compression", "yes")
                self.redis_client.config_set("compression-threshold", str(self.config.compression_threshold))
            
            logger.info("Redis configuration applied successfully")
        except Exception as e:
            logger.warning(f"Failed to configure Redis: {e}")
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from prefix and arguments"""
        key_parts = [prefix]
        
        # Add positional arguments
        for arg in args:
            if isinstance(arg, (str, int, float, bool)):
                key_parts.append(str(arg))
            else:
                # Hash complex objects
                key_parts.append(hashlib.md5(pickle.dumps(arg)).hexdigest()[:8])
        
        # Add keyword arguments
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            for key, value in sorted_kwargs:
                if isinstance(value, (str, int, float, bool)):
                    key_parts.append(f"{key}:{value}")
                else:
                    key_parts.append(f"{key}:{hashlib.md5(pickle.dumps(value)).hexdigest()[:8]}")
        
        return ":".join(key_parts)
    
    def _serialize(self, value: Any) -> bytes:
        """Serialize value for storage"""
        if isinstance(value, (str, int, float, bool, type(None))):
            return json.dumps(value).encode('utf-8')
        else:
            return pickle.dumps(value)
    
    def _deserialize(self, value: bytes) -> Any:
        """Deserialize value from storage"""
        try:
            # Try JSON first
            return json.loads(value.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            try:
                # Fall back to pickle
                return pickle.loads(value)
            except Exception as e:
                logger.error(f"Failed to deserialize value: {e}")
                return None
    
    def _should_compress(self, data: bytes) -> bool:
        """Check if data should be compressed"""
        return len(data) > self.config.compression_threshold
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache"""
        if not self.redis_client:
            return default
        
        try:
            value = self.redis_client.get(key)
            if value is None:
                return default
            
            # Check if compressed
            if value.startswith(b'COMPRESSED:'):
                import gzip
                compressed_data = value[12:]  # Remove 'COMPRESSED:' prefix
                value = gzip.decompress(compressed_data)
            
            return self._deserialize(value)
        except Exception as e:
            logger.error(f"Failed to get key {key}: {e}")
            return default
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, 
            strategy: CacheStrategy = CacheStrategy.TTL) -> bool:
        """Set value in cache"""
        if not self.redis_client:
            return False
        
        try:
            serialized_value = self._serialize(value)
            
            # Compress if needed
            if self._should_compress(serialized_value):
                import gzip
                compressed_data = gzip.compress(serialized_value)
                serialized_value = b'COMPRESSED:' + compressed_data
            
            # Set with TTL
            ttl = ttl or self.config.default_ttl
            
            if strategy == CacheStrategy.TTL:
                return self.redis_client.setex(key, ttl, serialized_value)
            elif strategy == CacheStrategy.SLIDING:
                # Set with TTL and enable key expiration events
                pipe = self.redis_client.pipeline()
                pipe.setex(key, ttl, serialized_value)
                pipe.expire(key, ttl)
                pipe.execute()
                return True
            else:  # LRU
                return self.redis_client.set(key, serialized_value)
                
        except Exception as e:
            logger.error(f"Failed to set key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.redis_client:
            return False
        
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"Failed to delete key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.redis_client:
            return False
        
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Failed to check key {key}: {e}")
            return False
    
    def expire(self, key: str, ttl: int) -> bool:
        """Set expiration for key"""
        if not self.redis_client:
            return False
        
        try:
            return bool(self.redis_client.expire(key, ttl))
        except Exception as e:
            logger.error(f"Failed to set expiration for key {key}: {e}")
            return False
    
    def ttl(self, key: str) -> int:
        """Get TTL for key"""
        if not self.redis_client:
            return -1
        
        try:
            return self.redis_client.ttl(key)
        except Exception as e:
            logger.error(f"Failed to get TTL for key {key}: {e}")
            return -1
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment counter value"""
        if not self.redis_client:
            return None
        
        try:
            return self.redis_client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Failed to increment key {key}: {e}")
            return None
    
    def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values from cache"""
        if not self.redis_client:
            return {}
        
        try:
            values = self.redis_client.mget(keys)
            result = {}
            for key, value in zip(keys, values):
                if value is not None:
                    result[key] = self._deserialize(value)
            return result
        except Exception as e:
            logger.error(f"Failed to get many keys: {e}")
            return {}
    
    def set_many(self, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set multiple values in cache"""
        if not self.redis_client:
            return False
        
        try:
            pipe = self.redis_client.pipeline()
            ttl = ttl or self.config.default_ttl
            
            for key, value in data.items():
                serialized_value = self._serialize(value)
                
                if self._should_compress(serialized_value):
                    import gzip
                    compressed_data = gzip.compress(serialized_value)
                    serialized_value = b'COMPRESSED:' + compressed_data
                
                pipe.setex(key, ttl, serialized_value)
            
            pipe.execute()
            return True
        except Exception as e:
            logger.error(f"Failed to set many keys: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear keys matching pattern"""
        if not self.redis_client:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Failed to clear pattern {pattern}: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.redis_client:
            return {}
        
        try:
            info = self.redis_client.info()
            return {
                'connected_clients': info.get('connected_clients', 0),
                'used_memory': info.get('used_memory', 0),
                'used_memory_peak': info.get('used_memory_peak', 0),
                'total_commands_processed': info.get('total_commands_processed', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'uptime_in_seconds': info.get('uptime_in_seconds', 0),
                'db_size': self.redis_client.dbsize()
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}
    
    def health_check(self) -> bool:
        """Check cache health"""
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def close(self) -> None:
        """Close Redis connection"""
        if self.redis_client:
            try:
                self.redis_client.close()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")

# Cache decorators for easy use
def cached(ttl: int = 3600, key_prefix: str = "cache", 
           strategy: CacheStrategy = CacheStrategy.TTL):
    """Decorator to cache function results"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # This would need the cache instance to be available
            # Implementation depends on how cache is configured
            return func(*args, **kwargs)
        return wrapper
    return decorator

def cache_invalidate(pattern: str):
    """Decorator to invalidate cache after function execution"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            # This would need the cache instance to be available
            # Implementation depends on how cache is configured
            return result
        return wrapper
    return decorator
