"""
Query Cache System with Similarity Detection
Caches responses to avoid redundant LLM calls for similar queries
"""
import json
import time
import hashlib
from typing import Optional, Dict, List, Tuple
from difflib import SequenceMatcher
import os

class QueryCache:
    """
    In-memory cache for query responses with similarity detection
    """
    def __init__(self, similarity_threshold=0.85, max_cache_size=1000, ttl_seconds=3600):
        self.cache: Dict[str, Dict] = {}
        self.similarity_threshold = similarity_threshold
        self.max_cache_size = max_cache_size
        self.ttl_seconds = ttl_seconds
        self.stats = {
            "hits": 0,
            "misses": 0,
            "similarity_hits": 0,
            "evictions": 0
        }
        
    def _normalize_query(self, query: str) -> str:
        """Normalize query for better matching"""
        return query.lower().strip()
    
    def _compute_hash(self, query: str, role: str, model: str) -> str:
        """Compute cache key hash"""
        key = f"{query}|{role}|{model}"
        return hashlib.md5(key.encode()).hexdigest()
    
    def _compute_similarity(self, query1: str, query2: str) -> float:
        """Compute similarity between two queries"""
        return SequenceMatcher(None, query1, query2).ratio()
    
    def _find_similar_query(self, query: str, role: str, model: str) -> Optional[Tuple[str, Dict]]:
        """Find a similar cached query above threshold"""
        normalized_query = self._normalize_query(query)
        
        for cache_key, cache_entry in self.cache.items():
            if cache_entry["role"] != role or cache_entry["model"] != model:
                continue
                
            cached_query = self._normalize_query(cache_entry["query"])
            similarity = self._compute_similarity(normalized_query, cached_query)
            
            if similarity >= self.similarity_threshold:
                return cache_key, cache_entry
        
        return None
    
    def _is_expired(self, cache_entry: Dict) -> bool:
        """Check if cache entry has expired"""
        if self.ttl_seconds <= 0:
            return False
        return time.time() - cache_entry["timestamp"] > self.ttl_seconds
    
    def _evict_oldest(self):
        """Evict oldest cache entry when size limit is reached"""
        if not self.cache:
            return
        
        oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]["timestamp"])
        del self.cache[oldest_key]
        self.stats["evictions"] += 1
    
    def get(self, query: str, role: str, model: str) -> Optional[str]:
        """
        Get cached response for query
        Returns None if not found or expired
        """
        # Try exact match first
        cache_key = self._compute_hash(query, role, model)
        
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            if not self._is_expired(entry):
                self.stats["hits"] += 1
                entry["access_count"] += 1
                entry["last_accessed"] = time.time()
                return entry["response"]
            else:
                # Remove expired entry
                del self.cache[cache_key]
        
        # Try similarity match
        similar = self._find_similar_query(query, role, model)
        if similar:
            cache_key, entry = similar
            if not self._is_expired(entry):
                self.stats["similarity_hits"] += 1
                entry["access_count"] += 1
                entry["last_accessed"] = time.time()
                return entry["response"]
            else:
                del self.cache[cache_key]
        
        self.stats["misses"] += 1
        return None
    
    def set(self, query: str, role: str, model: str, response: str):
        """Cache a query response"""
        # Enforce size limit
        if len(self.cache) >= self.max_cache_size:
            self._evict_oldest()
        
        cache_key = self._compute_hash(query, role, model)
        self.cache[cache_key] = {
            "query": query,
            "role": role,
            "model": model,
            "response": response,
            "timestamp": time.time(),
            "last_accessed": time.time(),
            "access_count": 0
        }
    
    def invalidate(self, query: str = None, role: str = None):
        """
        Invalidate cache entries
        If query is provided, invalidate that specific query
        If role is provided, invalidate all queries for that role
        If neither, clear entire cache
        """
        if query and role:
            # Invalidate specific query
            for model in ["llama3", "mistral", "deepseek-r1:7b"]:
                cache_key = self._compute_hash(query, role, model)
                if cache_key in self.cache:
                    del self.cache[cache_key]
        elif role:
            # Invalidate all queries for role
            keys_to_delete = [k for k, v in self.cache.items() if v["role"] == role]
            for key in keys_to_delete:
                del self.cache[key]
        else:
            # Clear entire cache
            self.cache.clear()
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "total_entries": len(self.cache),
            "total_requests": total_requests,
            "cache_hits": self.stats["hits"],
            "cache_misses": self.stats["misses"],
            "similarity_hits": self.stats["similarity_hits"],
            "hit_rate_percent": round(hit_rate, 2),
            "evictions": self.stats["evictions"],
            "max_size": self.max_cache_size
        }
    
    def get_top_queries(self, limit: int = 10) -> List[Dict]:
        """Get most frequently accessed queries"""
        sorted_entries = sorted(
            self.cache.values(),
            key=lambda x: x["access_count"],
            reverse=True
        )
        
        return [
            {
                "query": entry["query"],
                "role": entry["role"],
                "access_count": entry["access_count"],
                "last_accessed": entry["last_accessed"]
            }
            for entry in sorted_entries[:limit]
        ]
    
    def save_to_disk(self, filepath: str = "logs/query_cache.json"):
        """Persist cache to disk"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump({
                "cache": self.cache,
                "stats": self.stats
            }, f, indent=2)
    
    def load_from_disk(self, filepath: str = "logs/query_cache.json"):
        """Load cache from disk"""
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                data = json.load(f)
                self.cache = data.get("cache", {})
                self.stats = data.get("stats", self.stats)

# Global cache instance
query_cache = QueryCache(
    similarity_threshold=0.85,
    max_cache_size=1000,
    ttl_seconds=3600  # 1 hour TTL
)
