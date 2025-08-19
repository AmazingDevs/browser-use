#!/usr/bin/env python3
"""
Context Aware Accumulator - Advanced context management for browser_use

This script implements sophisticated context management using memory chunking,
sliding window techniques, and quality maintenance as test cases accumulate.
Features JSON streaming for handling large outputs efficiently.

Author: Claude Code
Date: 2025-08-15
"""

import asyncio
import json
import hashlib
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Iterator, Tuple
from dataclasses import dataclass, asdict, field
from collections import deque
import pickle
import gzip
from abc import ABC, abstractmethod

# Browser_use imports
from browser_use import Agent, AgentSettings, BrowserProfile, BrowserSession
from browser_use.agent.views import AgentHistory, AgentHistoryList


@dataclass
class ContextChunk:
    """Represents a chunk of context data with metadata"""
    chunk_id: str
    content: Dict[str, Any]
    timestamp: datetime
    size_bytes: int
    importance_score: float
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class ContextWindow:
    """Sliding window of context chunks"""
    window_id: str
    chunks: deque
    max_size: int
    total_size_bytes: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class QualityMetrics:
    """Quality metrics for context management"""
    coherence_score: float
    completeness_score: float
    relevance_score: float
    compression_ratio: float
    access_efficiency: float
    degradation_rate: float


class ContextStrategy(ABC):
    """Abstract base class for context management strategies"""
    
    @abstractmethod
    async def should_evict(self, chunk: ContextChunk, window: ContextWindow) -> bool:
        """Determine if a chunk should be evicted"""
        pass
    
    @abstractmethod
    async def calculate_importance(self, chunk: ContextChunk, context: Dict[str, Any]) -> float:
        """Calculate importance score for a chunk"""
        pass


class LRUStrategy(ContextStrategy):
    """Least Recently Used context management strategy"""
    
    async def should_evict(self, chunk: ContextChunk, window: ContextWindow) -> bool:
        """Evict least recently used chunks when window is full"""
        if len(window.chunks) < window.max_size:
            return False
        
        # Find oldest accessed chunk
        oldest_chunk = min(window.chunks, key=lambda c: c.last_accessed or c.timestamp)
        return chunk.chunk_id == oldest_chunk.chunk_id
    
    async def calculate_importance(self, chunk: ContextChunk, context: Dict[str, Any]) -> float:
        """Calculate importance based on recency and access frequency"""
        now = datetime.now()
        time_factor = 1.0 / (1 + (now - chunk.timestamp).total_seconds() / 3600)  # Decay over hours
        access_factor = min(chunk.access_count / 10.0, 1.0)  # Normalize access count
        return (time_factor + access_factor) / 2.0


class SemanticStrategy(ContextStrategy):
    """Semantic similarity-based context management strategy"""
    
    def __init__(self, similarity_threshold: float = 0.7):
        self.similarity_threshold = similarity_threshold
        self.content_vectors = {}  # Simple content hash-based similarity
    
    async def should_evict(self, chunk: ContextChunk, window: ContextWindow) -> bool:
        """Evict chunks with low semantic relevance"""
        if len(window.chunks) < window.max_size:
            return False
        
        # Calculate semantic similarity to recent chunks
        recent_chunks = list(window.chunks)[-5:]  # Last 5 chunks
        similarity_scores = []
        
        for recent_chunk in recent_chunks:
            similarity = await self._calculate_similarity(chunk, recent_chunk)
            similarity_scores.append(similarity)
        
        avg_similarity = sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0
        return avg_similarity < self.similarity_threshold
    
    async def calculate_importance(self, chunk: ContextChunk, context: Dict[str, Any]) -> float:
        """Calculate importance based on semantic relevance"""
        # Simple implementation using content hash similarity
        content_str = json.dumps(chunk.content, sort_keys=True)
        content_hash = hashlib.md5(content_str.encode()).hexdigest()
        
        # In a real implementation, you'd use embeddings here
        base_score = len(chunk.content) / 1000.0  # Size-based relevance
        tag_bonus = len(chunk.tags) * 0.1  # Tag diversity bonus
        
        return min(base_score + tag_bonus, 1.0)
    
    async def _calculate_similarity(self, chunk1: ContextChunk, chunk2: ContextChunk) -> float:
        """Calculate similarity between two chunks"""
        # Simple hash-based similarity (in practice, use embeddings)
        hash1 = hashlib.md5(json.dumps(chunk1.content, sort_keys=True).encode()).hexdigest()
        hash2 = hashlib.md5(json.dumps(chunk2.content, sort_keys=True).encode()).hexdigest()
        
        # Hamming distance-based similarity
        diff_count = sum(c1 != c2 for c1, c2 in zip(hash1, hash2))
        return 1.0 - (diff_count / len(hash1))


class ContextAwareAccumulator:
    """
    Advanced context management system for browser_use
    
    Features:
    - Memory chunking with configurable strategies
    - Sliding window context management
    - Quality metrics and degradation tracking
    - JSON streaming for large datasets
    - Compression and efficient storage
    """
    
    def __init__(self,
                 max_memory_mb: int = 100,
                 chunk_size_kb: int = 10,
                 window_size: int = 50,
                 strategy: ContextStrategy = None,
                 storage_dir: str = "./context_storage"):
        """
        Initialize the context accumulator
        
        Args:
            max_memory_mb: Maximum memory usage in MB
            chunk_size_kb: Target chunk size in KB
            window_size: Maximum number of chunks in sliding window
            strategy: Context management strategy
            storage_dir: Directory for persistent storage
        """
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.chunk_size_bytes = chunk_size_kb * 1024
        self.window_size = window_size
        self.strategy = strategy or LRUStrategy()
        self.storage_dir = Path(storage_dir)
        
        # Create storage directory
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize context windows
        self.active_window = ContextWindow(
            window_id=str(uuid.uuid4()),
            chunks=deque(maxlen=window_size),
            max_size=window_size
        )
        
        self.archived_windows = []
        self.quality_metrics = QualityMetrics(
            coherence_score=1.0,
            completeness_score=1.0,
            relevance_score=1.0,
            compression_ratio=1.0,
            access_efficiency=1.0,
            degradation_rate=0.0
        )
        
        # Streaming configuration
        self.stream_buffer_size = 1024 * 1024  # 1MB buffer
        self.compression_enabled = True

    async def add_context(self, content: Dict[str, Any], tags: List[str] = None) -> str:
        """
        Add new context content with intelligent chunking
        
        Args:
            content: Context content to add
            tags: Optional tags for categorization
            
        Returns:
            Chunk ID of the added content
        """
        # Serialize content to estimate size
        content_json = json.dumps(content, ensure_ascii=False)
        content_size = len(content_json.encode('utf-8'))
        
        # Create chunks if content is too large
        if content_size > self.chunk_size_bytes:
            return await self._chunk_large_content(content, tags or [])
        else:
            return await self._add_single_chunk(content, content_size, tags or [])

    async def _chunk_large_content(self, content: Dict[str, Any], tags: List[str]) -> str:
        """Split large content into multiple chunks"""
        chunks_created = []
        
        # Strategy: Split by top-level keys if possible
        if isinstance(content, dict) and len(content) > 1:
            current_chunk = {}
            current_size = 0
            
            for key, value in content.items():
                item_json = json.dumps({key: value}, ensure_ascii=False)
                item_size = len(item_json.encode('utf-8'))
                
                if current_size + item_size > self.chunk_size_bytes and current_chunk:
                    # Save current chunk
                    chunk_id = await self._add_single_chunk(current_chunk, current_size, tags)
                    chunks_created.append(chunk_id)
                    current_chunk = {}
                    current_size = 0
                
                current_chunk[key] = value
                current_size += item_size
            
            # Add remaining chunk
            if current_chunk:
                chunk_id = await self._add_single_chunk(current_chunk, current_size, tags)
                chunks_created.append(chunk_id)
        
        else:
            # Fallback: Create single chunk (might exceed size limit)
            content_size = len(json.dumps(content, ensure_ascii=False).encode('utf-8'))
            chunk_id = await self._add_single_chunk(content, content_size, tags)
            chunks_created.append(chunk_id)
        
        return chunks_created[0] if chunks_created else ""

    async def _add_single_chunk(self, content: Dict[str, Any], size_bytes: int, tags: List[str]) -> str:
        """Add a single chunk to the context window"""
        chunk_id = str(uuid.uuid4())
        
        # Calculate importance score
        importance = await self.strategy.calculate_importance(
            ContextChunk(chunk_id, content, datetime.now(), size_bytes, 0.0),
            {"window_size": len(self.active_window.chunks)}
        )
        
        chunk = ContextChunk(
            chunk_id=chunk_id,
            content=content,
            timestamp=datetime.now(),
            size_bytes=size_bytes,
            importance_score=importance,
            tags=tags
        )
        
        # Check if we need to evict chunks
        await self._manage_window_capacity(chunk)
        
        # Add to active window
        self.active_window.chunks.append(chunk)
        self.active_window.total_size_bytes += size_bytes
        self.active_window.last_updated = datetime.now()
        
        # Update quality metrics
        await self._update_quality_metrics()
        
        return chunk_id

    async def _manage_window_capacity(self, new_chunk: ContextChunk):
        """Manage window capacity using the configured strategy"""
        # Check memory limit
        if self.active_window.total_size_bytes + new_chunk.size_bytes > self.max_memory_bytes:
            await self._archive_chunks()
        
        # Check chunk count limit
        while len(self.active_window.chunks) >= self.active_window.max_size:
            oldest_chunk = self.active_window.chunks.popleft()
            self.active_window.total_size_bytes -= oldest_chunk.size_bytes
            
            # Archive removed chunk
            await self._archive_chunk(oldest_chunk)

    async def _archive_chunks(self):
        """Archive older chunks to persistent storage"""
        chunks_to_archive = len(self.active_window.chunks) // 2  # Archive half
        archived_chunks = []
        
        for _ in range(chunks_to_archive):
            if self.active_window.chunks:
                chunk = self.active_window.chunks.popleft()
                self.active_window.total_size_bytes -= chunk.size_bytes
                archived_chunks.append(chunk)
        
        if archived_chunks:
            # Create archived window
            archived_window = ContextWindow(
                window_id=str(uuid.uuid4()),
                chunks=deque(archived_chunks),
                max_size=len(archived_chunks)
            )
            
            # Save to disk
            await self._save_archived_window(archived_window)
            self.archived_windows.append(archived_window.window_id)

    async def _archive_chunk(self, chunk: ContextChunk):
        """Archive a single chunk to storage"""
        archive_path = self.storage_dir / f"chunk_{chunk.chunk_id}.json.gz"
        
        chunk_data = asdict(chunk)
        chunk_data['timestamp'] = chunk.timestamp.isoformat()
        chunk_data['last_accessed'] = chunk.last_accessed.isoformat() if chunk.last_accessed else None
        
        # Compress and save
        if self.compression_enabled:
            with gzip.open(archive_path, 'wt', encoding='utf-8') as f:
                json.dump(chunk_data, f, ensure_ascii=False)
        else:
            with open(archive_path, 'w', encoding='utf-8') as f:
                json.dump(chunk_data, f, ensure_ascii=False, indent=2)

    async def _save_archived_window(self, window: ContextWindow):
        """Save archived window to storage"""
        window_path = self.storage_dir / f"window_{window.window_id}.pkl.gz"
        
        # Convert chunks to serializable format
        window_data = {
            'window_id': window.window_id,
            'chunks': [asdict(chunk) for chunk in window.chunks],
            'max_size': window.max_size,
            'total_size_bytes': window.total_size_bytes,
            'created_at': window.created_at.isoformat(),
            'last_updated': window.last_updated.isoformat()
        }
        
        # Compress and save
        with gzip.open(window_path, 'wb') as f:
            pickle.dump(window_data, f)

    async def get_context(self, max_chunks: int = None, tags: List[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve context with optional filtering
        
        Args:
            max_chunks: Maximum number of chunks to return
            tags: Filter by tags
            
        Returns:
            List of context content
        """
        relevant_chunks = []
        
        # Filter chunks by tags if specified
        for chunk in self.active_window.chunks:
            if tags and not any(tag in chunk.tags for tag in tags):
                continue
            
            # Update access tracking
            chunk.access_count += 1
            chunk.last_accessed = datetime.now()
            
            relevant_chunks.append(chunk.content)
            
            if max_chunks and len(relevant_chunks) >= max_chunks:
                break
        
        return relevant_chunks

    async def stream_context(self, chunk_filter: callable = None) -> Iterator[Dict[str, Any]]:
        """
        Stream context data for large datasets
        
        Args:
            chunk_filter: Optional filter function for chunks
            
        Yields:
            Context content chunks
        """
        for chunk in self.active_window.chunks:
            if chunk_filter and not chunk_filter(chunk):
                continue
            
            # Update access tracking
            chunk.access_count += 1
            chunk.last_accessed = datetime.now()
            
            yield chunk.content

    async def get_quality_metrics(self) -> QualityMetrics:
        """Get current quality metrics"""
        await self._update_quality_metrics()
        return self.quality_metrics

    async def _update_quality_metrics(self):
        """Update quality metrics based on current state"""
        if not self.active_window.chunks:
            return
        
        # Coherence: How well chunks relate to each other
        coherence_score = await self._calculate_coherence()
        
        # Completeness: How much of the original context is preserved
        completeness_score = await self._calculate_completeness()
        
        # Relevance: How relevant chunks are to recent activity
        relevance_score = await self._calculate_relevance()
        
        # Compression ratio
        total_chunks = len(self.active_window.chunks) + len(self.archived_windows)
        compression_ratio = len(self.active_window.chunks) / max(total_chunks, 1)
        
        # Access efficiency
        total_accesses = sum(chunk.access_count for chunk in self.active_window.chunks)
        access_efficiency = total_accesses / max(len(self.active_window.chunks), 1)
        
        # Degradation rate (how quickly quality decreases)
        time_span = (datetime.now() - self.active_window.created_at).total_seconds() / 3600  # hours
        degradation_rate = max(0, (1.0 - coherence_score) / max(time_span, 1))
        
        self.quality_metrics = QualityMetrics(
            coherence_score=coherence_score,
            completeness_score=completeness_score,
            relevance_score=relevance_score,
            compression_ratio=compression_ratio,
            access_efficiency=access_efficiency / 10.0,  # Normalize
            degradation_rate=degradation_rate
        )

    async def _calculate_coherence(self) -> float:
        """Calculate coherence score based on chunk relationships"""
        if len(self.active_window.chunks) < 2:
            return 1.0
        
        # Simple implementation: tag overlap between consecutive chunks
        coherence_scores = []
        chunks = list(self.active_window.chunks)
        
        for i in range(len(chunks) - 1):
            chunk1, chunk2 = chunks[i], chunks[i + 1]
            
            if not chunk1.tags or not chunk2.tags:
                coherence_scores.append(0.5)  # Neutral score
            else:
                overlap = len(set(chunk1.tags) & set(chunk2.tags))
                total_tags = len(set(chunk1.tags) | set(chunk2.tags))
                score = overlap / max(total_tags, 1)
                coherence_scores.append(score)
        
        return sum(coherence_scores) / len(coherence_scores)

    async def _calculate_completeness(self) -> float:
        """Calculate completeness score"""
        # Simple implementation: ratio of active to total chunks
        total_chunks = len(self.active_window.chunks) + len(self.archived_windows)
        return len(self.active_window.chunks) / max(total_chunks, 1)

    async def _calculate_relevance(self) -> float:
        """Calculate relevance score based on recent access patterns"""
        if not self.active_window.chunks:
            return 1.0
        
        now = datetime.now()
        relevance_scores = []
        
        for chunk in self.active_window.chunks:
            # Time-based relevance
            time_diff = (now - chunk.timestamp).total_seconds() / 3600  # hours
            time_relevance = 1.0 / (1 + time_diff / 24)  # Decay over days
            
            # Access-based relevance
            access_relevance = min(chunk.access_count / 5.0, 1.0)  # Normalize to max 5 accesses
            
            combined_relevance = (time_relevance + access_relevance) / 2
            relevance_scores.append(combined_relevance)
        
        return sum(relevance_scores) / len(relevance_scores)

    async def cleanup_expired_context(self, max_age_hours: int = 24):
        """Remove context chunks older than specified age"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        # Remove expired chunks from active window
        expired_chunks = []
        remaining_chunks = deque()
        
        for chunk in self.active_window.chunks:
            if chunk.timestamp < cutoff_time:
                expired_chunks.append(chunk)
            else:
                remaining_chunks.append(chunk)
        
        self.active_window.chunks = remaining_chunks
        self.active_window.total_size_bytes = sum(chunk.size_bytes for chunk in remaining_chunks)
        
        # Archive expired chunks
        for chunk in expired_chunks:
            await self._archive_chunk(chunk)
        
        print(f"Cleaned up {len(expired_chunks)} expired chunks")

    async def export_context_stream(self, output_path: str):
        """Export all context data as a JSON stream"""
        output_file = Path(output_path)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('[\n')
            
            first_chunk = True
            async for content in self.stream_context():
                if not first_chunk:
                    f.write(',\n')
                json.dump(content, f, ensure_ascii=False, indent=2)
                first_chunk = False
            
            f.write('\n]')
        
        print(f"Context exported to: {output_file}")


# Example usage
async def example_usage():
    """Example usage of ContextAwareAccumulator"""
    
    # Initialize with different strategies
    lru_accumulator = ContextAwareAccumulator(
        max_memory_mb=50,
        chunk_size_kb=5,
        window_size=20,
        strategy=LRUStrategy(),
        storage_dir="./context_lru"
    )
    
    semantic_accumulator = ContextAwareAccumulator(
        max_memory_mb=50,
        chunk_size_kb=5,
        window_size=20,
        strategy=SemanticStrategy(similarity_threshold=0.6),
        storage_dir="./context_semantic"
    )
    
    # Add context data
    test_contexts = [
        {"page": "login", "action": "fill_form", "elements": ["username", "password"]},
        {"page": "dashboard", "action": "navigate", "elements": ["menu", "sidebar"]},
        {"page": "profile", "action": "update", "elements": ["name", "email", "phone"]},
        {"page": "settings", "action": "configure", "elements": ["notifications", "privacy"]},
    ]
    
    for i, context in enumerate(test_contexts):
        chunk_id = await lru_accumulator.add_context(
            content=context,
            tags=[context["page"], context["action"]]
        )
        print(f"Added chunk {i+1}: {chunk_id}")
    
    # Retrieve context
    recent_context = await lru_accumulator.get_context(max_chunks=3)
    print(f"Retrieved {len(recent_context)} recent contexts")
    
    # Get quality metrics
    metrics = await lru_accumulator.get_quality_metrics()
    print(f"Quality metrics: coherence={metrics.coherence_score:.2f}, "
          f"relevance={metrics.relevance_score:.2f}")
    
    # Stream context
    print("Streaming context:")
    async for content in lru_accumulator.stream_context():
        print(f"  - {content['page']}: {content['action']}")
    
    # Export context
    await lru_accumulator.export_context_stream("context_export.json")
    
    # Cleanup old context
    await lru_accumulator.cleanup_expired_context(max_age_hours=1)


if __name__ == "__main__":
    print("Context Aware Accumulator - Example Usage")
    print("=" * 45)
    
    asyncio.run(example_usage())