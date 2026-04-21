"""
Analytics and Audit System
Tracks queries, performance, hallucinations, and user activity
"""
import json
import time
import os
from typing import Dict, List, Optional
from collections import defaultdict, Counter
from datetime import datetime, timedelta

class AnalyticsEngine:
    """
    Comprehensive analytics for RAG system
    """
    def __init__(self, log_file: str = "logs/analytics.json"):
        self.log_file = log_file
        self.session_data = []
        self.query_logs = []
        self.hallucination_logs = []
        self.performance_metrics = []
        self._load_from_disk()
    
    def _load_from_disk(self):
        """Load analytics data from disk"""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r') as f:
                    data = json.load(f)
                    self.query_logs = data.get("query_logs", [])
                    self.hallucination_logs = data.get("hallucination_logs", [])
                    self.performance_metrics = data.get("performance_metrics", [])
            except Exception as e:
                print(f"Error loading analytics: {e}")
    
    def _save_to_disk(self):
        """Persist analytics data to disk"""
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        try:
            with open(self.log_file, 'w') as f:
                json.dump({
                    "query_logs": self.query_logs[-10000:],  # Keep last 10k
                    "hallucination_logs": self.hallucination_logs[-1000:],
                    "performance_metrics": self.performance_metrics[-5000:]
                }, f, indent=2)
        except Exception as e:
            print(f"[Analytics] Error saving analytics: {e}")
    
    def log_query(self, user_id: str, role: str, query: str, response: str, 
                  sources: List[str], status: str, response_time: float = 0,
                  cached: bool = False):
        """Log a query event"""
        log_entry = {
            "timestamp": time.time(),
            "datetime": datetime.now().isoformat(),
            "user_id": user_id,
            "role": role,
            "query": query,
            "query_length": len(query),
            "response_length": len(response),
            "sources_count": len(sources),
            "sources": sources,
            "status": status,
            "response_time_ms": round(response_time * 1000, 2),
            "cached": cached
        }
        self.query_logs.append(log_entry)
        
        # Save immediately after each query for real-time analytics
        self._save_to_disk()
    
    def log_hallucination(self, query: str, response: str, reason: str, 
                         role: str, blocked: bool = True):
        """Log a hallucination detection event"""
        log_entry = {
            "timestamp": time.time(),
            "datetime": datetime.now().isoformat(),
            "query": query,
            "response_preview": response[:200],
            "reason": reason,
            "role": role,
            "blocked": blocked
        }
        self.hallucination_logs.append(log_entry)
        self._save_to_disk()
    
    def log_performance(self, operation: str, duration_ms: float, metadata: Dict = None):
        """Log performance metrics"""
        log_entry = {
            "timestamp": time.time(),
            "operation": operation,
            "duration_ms": round(duration_ms, 2),
            "metadata": metadata or {}
        }
        self.performance_metrics.append(log_entry)
    
    def get_query_stats(self, hours: int = 24) -> Dict:
        """Get query statistics for the last N hours"""
        cutoff = time.time() - (hours * 3600)
        recent_queries = [q for q in self.query_logs if q["timestamp"] > cutoff]
        
        if not recent_queries:
            return {
                "total_queries": 0,
                "cached_queries": 0,
                "non_cached_queries": 0,
                "avg_response_time_ms": 0,
                "avg_non_cached_response_time_ms": 0,
                "cache_hit_rate": 0,
                "successful_queries": 0,
                "success_rate": 0,
                "queries_by_role": {},
                "queries_by_status": {}
            }
        
        total = len(recent_queries)
        cached = sum(1 for q in recent_queries if q.get("cached", False))
        # Count all queries with "Success" in status as successful
        successful = sum(1 for q in recent_queries if "Success" in q["status"])
        
        # Calculate average for all queries
        avg_time = sum(q["response_time_ms"] for q in recent_queries) / total
        
        # Calculate average for non-cached queries only (more meaningful metric)
        non_cached_queries = [q for q in recent_queries if not q.get("cached", False)]
        avg_non_cached_time = sum(q["response_time_ms"] for q in non_cached_queries) / len(non_cached_queries) if non_cached_queries else 0
        
        return {
            "total_queries": total,
            "cached_queries": cached,
            "non_cached_queries": len(non_cached_queries),
            "cache_hit_rate": round(cached / total * 100, 2) if total > 0 else 0,
            "successful_queries": successful,
            "success_rate": round(successful / total * 100, 2) if total > 0 else 0,
            "avg_response_time_ms": round(avg_time, 2),
            "avg_non_cached_response_time_ms": round(avg_non_cached_time, 2),
            "queries_by_role": self._count_by_field(recent_queries, "role"),
            "queries_by_status": self._count_by_field(recent_queries, "status")
        }
    
    def get_top_queries(self, limit: int = 10, hours: int = 24) -> List[Dict]:
        """Get most frequent queries"""
        cutoff = time.time() - (hours * 3600)
        recent_queries = [q for q in self.query_logs if q["timestamp"] > cutoff]
        
        query_counter = Counter(q["query"] for q in recent_queries)
        
        return [
            {"query": query, "count": count}
            for query, count in query_counter.most_common(limit)
        ]
    
    def get_failed_queries(self, limit: int = 20, hours: int = 24) -> List[Dict]:
        """Get recent failed queries"""
        cutoff = time.time() - (hours * 3600)
        failed = [
            q for q in self.query_logs 
            if q["timestamp"] > cutoff and q["status"] != "Success"
        ]
        
        return sorted(failed, key=lambda x: x["timestamp"], reverse=True)[:limit]
    
    def get_hallucination_stats(self, hours: int = 24) -> Dict:
        """Get hallucination detection statistics"""
        cutoff = time.time() - (hours * 3600)
        recent = [h for h in self.hallucination_logs if h["timestamp"] > cutoff]
        
        if not recent:
            return {
                "total_detections": 0,
                "blocked_count": 0,
                "detection_rate": 0
            }
        
        total_queries = len([q for q in self.query_logs if q["timestamp"] > cutoff])
        blocked = sum(1 for h in recent if h.get("blocked", True))
        
        return {
            "total_detections": len(recent),
            "blocked_count": blocked,
            "detection_rate": round(len(recent) / total_queries * 100, 2) if total_queries > 0 else 0,
            "reasons": self._count_by_field(recent, "reason"),
            "by_role": self._count_by_field(recent, "role")
        }
    
    def get_source_usage(self, limit: int = 10, hours: int = 24) -> List[Dict]:
        """Get most referenced source documents"""
        cutoff = time.time() - (hours * 3600)
        recent_queries = [q for q in self.query_logs if q["timestamp"] > cutoff]
        
        source_counter = Counter()
        for query in recent_queries:
            for source in query.get("sources", []):
                source_counter[source] += 1
        
        return [
            {"source": source, "reference_count": count}
            for source, count in source_counter.most_common(limit)
        ]
    
    def get_performance_stats(self, hours: int = 24) -> Dict:
        """Get performance statistics"""
        cutoff = time.time() - (hours * 3600)
        recent = [p for p in self.performance_metrics if p["timestamp"] > cutoff]
        
        if not recent:
            return {"operations": {}}
        
        ops = defaultdict(list)
        for metric in recent:
            ops[metric["operation"]].append(metric["duration_ms"])
        
        return {
            "operations": {
                op: {
                    "count": len(durations),
                    "avg_ms": round(sum(durations) / len(durations), 2),
                    "min_ms": round(min(durations), 2),
                    "max_ms": round(max(durations), 2)
                }
                for op, durations in ops.items()
            }
        }
    
    def get_user_activity(self, hours: int = 24) -> Dict:
        """Get user activity statistics"""
        cutoff = time.time() - (hours * 3600)
        recent_queries = [q for q in self.query_logs if q["timestamp"] > cutoff]
        
        user_stats = defaultdict(lambda: {"queries": 0, "roles": set()})
        for query in recent_queries:
            user_id = query["user_id"]
            user_stats[user_id]["queries"] += 1
            user_stats[user_id]["roles"].add(query["role"])
        
        return {
            "total_users": len(user_stats),
            "active_users": [
                {
                    "user_id": user_id,
                    "query_count": stats["queries"],
                    "roles": list(stats["roles"])
                }
                for user_id, stats in sorted(
                    user_stats.items(),
                    key=lambda x: x[1]["queries"],
                    reverse=True
                )[:20]
            ]
        }
    
    def get_timeline_data(self, hours: int = 24, interval_minutes: int = 60) -> List[Dict]:
        """Get query timeline data for charting"""
        cutoff = time.time() - (hours * 3600)
        recent_queries = [q for q in self.query_logs if q["timestamp"] > cutoff]
        
        interval_seconds = interval_minutes * 60
        buckets = defaultdict(lambda: {"queries": 0, "cached": 0, "failed": 0})
        
        for query in recent_queries:
            bucket_time = int(query["timestamp"] / interval_seconds) * interval_seconds
            buckets[bucket_time]["queries"] += 1
            if query.get("cached", False):
                buckets[bucket_time]["cached"] += 1
            # Count as failed if status doesn't contain "Success"
            if "Success" not in query["status"]:
                buckets[bucket_time]["failed"] += 1
        
        return [
            {
                "timestamp": bucket_time,
                "datetime": datetime.fromtimestamp(bucket_time).isoformat(),
                **stats
            }
            for bucket_time, stats in sorted(buckets.items())
        ]
    
    def _count_by_field(self, items: List[Dict], field: str) -> Dict[str, int]:
        """Helper to count items by a specific field"""
        counter = Counter(item.get(field, "unknown") for item in items)
        return dict(counter)
    
    def export_report(self, hours: int = 24) -> Dict:
        """Export comprehensive analytics report"""
        cutoff = time.time() - (hours * 3600)
        recent_queries = [q for q in self.query_logs if q["timestamp"] > cutoff]
        
        # Adjust timeline interval based on time range for better visualization
        if hours <= 1:
            interval_minutes = 5  # 5-minute intervals for 1 hour
        elif hours <= 24:
            interval_minutes = 60  # 1-hour intervals for 24 hours
        else:
            interval_minutes = 360  # 6-hour intervals for 7 days
        
        return {
            "report_generated": datetime.now().isoformat(),
            "time_range_hours": hours,
            "query_stats": self.get_query_stats(hours),
            "query_logs": recent_queries,  # Include recent query logs for detailed view
            "top_queries": self.get_top_queries(10, hours),
            "failed_queries": self.get_failed_queries(10, hours),
            "hallucination_stats": self.get_hallucination_stats(hours),
            "source_usage": self.get_source_usage(10, hours),
            "performance_stats": self.get_performance_stats(hours),
            "user_activity": self.get_user_activity(hours),
            "timeline": self.get_timeline_data(hours, interval_minutes)
        }

# Global analytics instance
analytics_engine = AnalyticsEngine()
