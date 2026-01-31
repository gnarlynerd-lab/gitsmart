"""
Storage - Handles knowledge storage and retrieval for GitSmart
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

from .exceptions import StorageError


@dataclass
class Memory:
    """Represents a stored decision or note"""
    id: str
    content: str
    enhanced_content: Optional[str]
    memory_type: str  # decision, note, bug, meeting
    context: Dict[str, Any]
    tags: List[str]
    created_at: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Memory':
        return cls(**data)


@dataclass
class QueryRecord:
    """Represents a stored query and response"""
    id: str
    question: str
    response: str
    context: Dict[str, Any]
    created_at: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QueryRecord':
        return cls(**data)


class KnowledgeStorage:
    """Manages storage of GitSmart knowledge and memories"""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path).resolve()
        self.gitsmart_dir = self.repo_path / ".gitsmart"
        
        # Storage directories
        self.knowledge_dir = self.gitsmart_dir / "knowledge"
        self.cache_dir = self.gitsmart_dir / "cache"
        self.logs_dir = self.gitsmart_dir / "logs"
        
        # Storage files
        self.memories_file = self.knowledge_dir / "memories.json"
        self.queries_file = self.knowledge_dir / "queries.json"
        self.explanations_file = self.knowledge_dir / "explanations.json"
        
        # Ensure directories exist
        self._ensure_directories()
        
        # In-memory caches for performance
        self._memories_cache: Optional[List[Memory]] = None
        self._queries_cache: Optional[List[QueryRecord]] = None
    
    def store_memory(
        self,
        content: str,
        enhanced_content: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        memory_type: str = "decision",
        tags: Optional[List[str]] = None
    ) -> str:
        """Store a memory (decision, note, etc.)"""
        
        memory_id = str(uuid.uuid4())
        
        memory = Memory(
            id=memory_id,
            content=content,
            enhanced_content=enhanced_content,
            memory_type=memory_type,
            context=context or {},
            tags=tags or [],
            created_at=datetime.now(timezone.utc).isoformat()
        )
        
        # Add to memories
        memories = self._load_memories()
        memories.append(memory)
        self._save_memories(memories)
        
        # Clear cache to force reload
        self._memories_cache = None
        
        return memory_id
    
    def search_memories(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search stored memories for relevant content"""
        memories = self._load_memories()
        
        query_lower = query.lower()
        scored_memories = []
        
        for memory in memories:
            score = 0
            
            # Search in content
            if query_lower in memory.content.lower():
                score += 5
            
            # Search in enhanced content
            if memory.enhanced_content and query_lower in memory.enhanced_content.lower():
                score += 3
            
            # Search in tags
            for tag in memory.tags:
                if query_lower in tag.lower():
                    score += 2
            
            # Search in context (commit messages, file names, etc.)
            context_text = str(memory.context).lower()
            if query_lower in context_text:
                score += 1
            
            if score > 0:
                scored_memories.append((score, memory))
        
        # Sort by score and return
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        return [memory.to_dict() for score, memory in scored_memories[:limit]]
    
    def get_memories_by_type(self, memory_type: str) -> List[Dict[str, Any]]:
        """Get all memories of a specific type"""
        memories = self._load_memories()
        return [m.to_dict() for m in memories if m.memory_type == memory_type]
    
    def get_recent_memories(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent memories"""
        memories = self._load_memories()
        # Sort by creation time (most recent first)
        sorted_memories = sorted(memories, key=lambda m: m.created_at, reverse=True)
        return [m.to_dict() for m in sorted_memories[:limit]]
    
    def store_query(self, question: str, response: str, context: Dict[str, Any]) -> str:
        """Store a query and its response for learning"""
        
        query_id = str(uuid.uuid4())
        
        query_record = QueryRecord(
            id=query_id,
            question=question,
            response=response,
            context=context,
            created_at=datetime.now(timezone.utc).isoformat()
        )
        
        # Add to queries
        queries = self._load_queries()
        queries.append(query_record)
        
        # Keep only the last 1000 queries to prevent unbounded growth
        if len(queries) > 1000:
            queries = queries[-1000:]
        
        self._save_queries(queries)
        
        # Clear cache
        self._queries_cache = None
        
        return query_id
    
    def store_explanation(self, filepath: str, explanation: str, context: Dict[str, Any]) -> None:
        """Store a file explanation for future reference"""
        
        explanations = self._load_explanations()
        
        explanations[filepath] = {
            'explanation': explanation,
            'context': context,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        self._save_explanations(explanations)
    
    def get_explanation(self, filepath: str) -> Optional[Dict[str, Any]]:
        """Get stored explanation for a file"""
        explanations = self._load_explanations()
        return explanations.get(filepath)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get storage statistics"""
        
        memories = self._load_memories()
        queries = self._load_queries()
        explanations = self._load_explanations()
        
        # Calculate cache size
        cache_size = self._calculate_cache_size()
        
        # Recent activity
        recent_memories = sorted(memories, key=lambda m: m.created_at, reverse=True)[:5]
        last_activity = recent_memories[0].created_at if recent_memories else None
        
        return {
            'decision_count': len([m for m in memories if m.memory_type == 'decision']),
            'total_memories': len(memories),
            'query_count': len(queries),
            'explanation_count': len(explanations),
            'cache_size': cache_size,
            'last_activity': last_activity,
            'recent_decisions': [m.content for m in recent_memories if m.memory_type == 'decision']
        }
    
    def cleanup_old_data(self, days_to_keep: int = 90) -> None:
        """Clean up old data to prevent unbounded growth"""
        
        cutoff_date = datetime.now(timezone.utc).timestamp() - (days_to_keep * 24 * 60 * 60)
        
        # Clean up old queries (keep memories as they're more valuable)
        queries = self._load_queries()
        filtered_queries = []
        
        for query in queries:
            query_time = datetime.fromisoformat(query.created_at.replace('Z', '+00:00')).timestamp()
            if query_time > cutoff_date:
                filtered_queries.append(query)
        
        if len(filtered_queries) != len(queries):
            self._save_queries(filtered_queries)
            self._queries_cache = None
    
    def _load_memories(self) -> List[Memory]:
        """Load memories from storage"""
        if self._memories_cache is not None:
            return self._memories_cache
        
        if not self.memories_file.exists():
            self._memories_cache = []
            return self._memories_cache
        
        try:
            with open(self.memories_file, 'r') as f:
                data = json.load(f)
                self._memories_cache = [Memory.from_dict(item) for item in data]
                return self._memories_cache
        except Exception as e:
            raise StorageError(f"Failed to load memories: {e}")
    
    def _save_memories(self, memories: List[Memory]) -> None:
        """Save memories to storage"""
        try:
            data = [memory.to_dict() for memory in memories]
            with open(self.memories_file, 'w') as f:
                json.dump(data, f, indent=2)
            self._memories_cache = memories
        except Exception as e:
            raise StorageError(f"Failed to save memories: {e}")
    
    def _load_queries(self) -> List[QueryRecord]:
        """Load queries from storage"""
        if self._queries_cache is not None:
            return self._queries_cache
        
        if not self.queries_file.exists():
            self._queries_cache = []
            return self._queries_cache
        
        try:
            with open(self.queries_file, 'r') as f:
                data = json.load(f)
                self._queries_cache = [QueryRecord.from_dict(item) for item in data]
                return self._queries_cache
        except Exception as e:
            raise StorageError(f"Failed to load queries: {e}")
    
    def _save_queries(self, queries: List[QueryRecord]) -> None:
        """Save queries to storage"""
        try:
            data = [query.to_dict() for query in queries]
            with open(self.queries_file, 'w') as f:
                json.dump(data, f, indent=2)
            self._queries_cache = queries
        except Exception as e:
            raise StorageError(f"Failed to save queries: {e}")
    
    def _load_explanations(self) -> Dict[str, Any]:
        """Load explanations from storage"""
        if not self.explanations_file.exists():
            return {}
        
        try:
            with open(self.explanations_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            raise StorageError(f"Failed to load explanations: {e}")
    
    def _save_explanations(self, explanations: Dict[str, Any]) -> None:
        """Save explanations to storage"""
        try:
            with open(self.explanations_file, 'w') as f:
                json.dump(explanations, f, indent=2)
        except Exception as e:
            raise StorageError(f"Failed to save explanations: {e}")
    
    def _ensure_directories(self) -> None:
        """Ensure all required directories exist"""
        for directory in [self.knowledge_dir, self.cache_dir, self.logs_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _calculate_cache_size(self) -> str:
        """Calculate total cache size"""
        total_size = 0
        
        for directory in [self.knowledge_dir, self.cache_dir, self.logs_dir]:
            if directory.exists():
                for file in directory.rglob('*'):
                    if file.is_file():
                        try:
                            total_size += file.stat().st_size
                        except OSError:
                            pass
        
        # Convert to human readable format
        for unit in ['B', 'KB', 'MB', 'GB']:
            if total_size < 1024:
                return f"{total_size:.1f}{unit}"
            total_size /= 1024
        
        return f"{total_size:.1f}TB"