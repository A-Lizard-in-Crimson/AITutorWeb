"""
Distributed Memory System - Phase 1 Prototype
File-based implementation for local development
"""

import json
import os
import uuid
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import fnmatch

class MemoryLevel(Enum):
    IMMEDIATE = "immediate"
    WORKING = "working"
    LONGTERM = "longterm"

class SourceType(Enum):
    CHAT = "chat"
    AGENT = "agent"
    FUNCTION = "function"
    API = "api"

@dataclass
class MemorySource:
    type: SourceType
    id: str
    session: Optional[str] = None

@dataclass
class MemoryEntry:
    id: str
    timestamp: str
    source: MemorySource
    level: MemoryLevel
    data: Dict[str, Any]
    ttl: Optional[int] = None
    visibility: str = "private"
    
    def is_expired(self) -> bool:
        if not self.ttl:
            return False
        created = datetime.fromisoformat(self.timestamp.replace('Z', '+00:00'))
        return datetime.now() > created + timedelta(seconds=self.ttl)

class FileBasedMemoryStore:
    """Phase 1: File-based storage implementation"""
    
    def __init__(self, base_path: str = "/Users/robertbenn/Desktop/Claude Files/MEMORY_STORE"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Create level directories
        for level in MemoryLevel:
            (self.base_path / level.value).mkdir(exist_ok=True)
        
        # Create indices directory
        (self.base_path / "indices").mkdir(exist_ok=True)
        
        # Lock for thread safety
        self.lock = threading.Lock()
        
    def _get_file_path(self, level: MemoryLevel, entry_id: str) -> Path:
        return self.base_path / level.value / f"{entry_id}.json"
    
    def _get_index_path(self, index_type: str) -> Path:
        return self.base_path / "indices" / f"{index_type}.json"
    
    def _load_index(self, index_type: str) -> Dict:
        index_path = self._get_index_path(index_type)
        if index_path.exists():
            with open(index_path, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_index(self, index_type: str, index_data: Dict):
        with self.lock:
            with open(self._get_index_path(index_type), 'w') as f:
                json.dump(index_data, f, indent=2)
    
    def _update_indices(self, entry: MemoryEntry, action: str = "add"):
        # Update session index
        session_index = self._load_index("sessions")
        if entry.source.session:
            if action == "add":
                if entry.source.session not in session_index:
                    session_index[entry.source.session] = []
                session_index[entry.source.session].append(entry.id)
            elif action == "remove":
                if entry.source.session in session_index:
                    session_index[entry.source.session].remove(entry.id)
        self._save_index("sessions", session_index)
        
        # Update tag index
        tag_index = self._load_index("tags")
        tags = entry.data.get("meta_tags", [])
        for tag in tags:
            if action == "add":
                if tag not in tag_index:
                    tag_index[tag] = []
                tag_index[tag].append(entry.id)
            elif action == "remove":
                if tag in tag_index:
                    tag_index[tag].remove(entry.id)
        self._save_index("tags", tag_index)
        
        # Update source index
        source_index = self._load_index("sources")
        source_key = f"{entry.source.type.value}:{entry.source.id}"
        if action == "add":
            if source_key not in source_index:
                source_index[source_key] = []
            source_index[source_key].append(entry.id)
        elif action == "remove":
            if source_key in source_index:
                source_index[source_key].remove(entry.id)
        self._save_index("sources", source_index)
    
    def save_entry(self, entry: MemoryEntry) -> bool:
        try:
            file_path = self._get_file_path(entry.level, entry.id)
            
            # Convert to dict for JSON serialization
            entry_dict = {
                "id": entry.id,
                "timestamp": entry.timestamp,
                "source": {
                    "type": entry.source.type.value,
                    "id": entry.source.id,
                    "session": entry.source.session
                },
                "level": entry.level.value,
                "data": entry.data,
                "ttl": entry.ttl,
                "visibility": entry.visibility
            }
            
            with self.lock:
                with open(file_path, 'w') as f:
                    json.dump(entry_dict, f, indent=2)
            
            self._update_indices(entry, "add")
            return True
            
        except Exception as e:
            print(f"Error saving entry: {e}")
            return False
    
    def load_entry(self, level: MemoryLevel, entry_id: str) -> Optional[MemoryEntry]:
        try:
            file_path = self._get_file_path(level, entry_id)
            if not file_path.exists():
                return None
            
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Reconstruct MemoryEntry
            source = MemorySource(
                type=SourceType(data["source"]["type"]),
                id=data["source"]["id"],
                session=data["source"]["session"]
            )
            
            entry = MemoryEntry(
                id=data["id"],
                timestamp=data["timestamp"],
                source=source,
                level=MemoryLevel(data["level"]),
                data=data["data"],
                ttl=data.get("ttl"),
                visibility=data.get("visibility", "private")
            )
            
            # Check if expired
            if entry.is_expired():
                self.delete_entry(level, entry_id)
                return None
            
            return entry
            
        except Exception as e:
            print(f"Error loading entry: {e}")
            return None
    
    def delete_entry(self, level: MemoryLevel, entry_id: str) -> bool:
        try:
            entry = self.load_entry(level, entry_id)
            if entry:
                self._update_indices(entry, "remove")
            
            file_path = self._get_file_path(level, entry_id)
            if file_path.exists():
                file_path.unlink()
            return True
            
        except Exception as e:
            print(f"Error deleting entry: {e}")
            return False
    
    def query_by_session(self, session_id: str) -> List[MemoryEntry]:
        session_index = self._load_index("sessions")
        entry_ids = session_index.get(session_id, [])
        
        entries = []
        for entry_id in entry_ids:
            # Try all levels
            for level in MemoryLevel:
                entry = self.load_entry(level, entry_id)
                if entry:
                    entries.append(entry)
                    break
        
        return entries
    
    def query_by_tags(self, tags: List[str]) -> List[MemoryEntry]:
        tag_index = self._load_index("tags")
        entry_ids = set()
        
        for tag in tags:
            # Support wildcard matching
            if '*' in tag:
                for indexed_tag, ids in tag_index.items():
                    if fnmatch.fnmatch(indexed_tag, tag):
                        entry_ids.update(ids)
            else:
                entry_ids.update(tag_index.get(tag, []))
        
        entries = []
        for entry_id in entry_ids:
            for level in MemoryLevel:
                entry = self.load_entry(level, entry_id)
                if entry:
                    entries.append(entry)
                    break
        
        return entries
    
    def clean_expired(self):
        """Remove expired entries"""
        cleaned = 0
        for level in MemoryLevel:
            level_path = self.base_path / level.value
            for file_path in level_path.glob("*.json"):
                entry_id = file_path.stem
                entry = self.load_entry(level, entry_id)
                if entry and entry.is_expired():
                    self.delete_entry(level, entry_id)
                    cleaned += 1
        return cleaned

class DistributedMemoryAPI:
    """Main API interface for the distributed memory system"""
    
    def __init__(self, store: Optional[FileBasedMemoryStore] = None):
        self.store = store or FileBasedMemoryStore()
        
    def create_context(self, session_id: str, source: MemorySource, 
                      initial_focus: Dict[str, Any]) -> str:
        """Initialize a new context for a session"""
        context_id = str(uuid.uuid4())
        
        entry = MemoryEntry(
            id=context_id,
            timestamp=datetime.utcnow().isoformat() + 'Z',
            source=source,
            level=MemoryLevel.IMMEDIATE,
            data={
                "type": "context",
                "session_id": session_id,
                "current_focus": initial_focus,
                "working_set": {},
                "meta_tags": ["CONTEXT", f"SESSION_{session_id}"]
            },
            ttl=86400  # 24 hours
        )
        
        self.store.save_entry(entry)
        return context_id
    
    def update_focus(self, session_id: str, new_focus: Dict[str, Any]) -> bool:
        """Update the current focus for a session"""
        entries = self.store.query_by_session(session_id)
        context_entries = [e for e in entries if e.data.get("type") == "context"]
        
        if not context_entries:
            return False
        
        # Update the most recent context
        context = context_entries[-1]
        context.data["current_focus"] = new_focus
        context.timestamp = datetime.utcnow().isoformat() + 'Z'
        
        return self.store.save_entry(context)
    
    def add_to_working_set(self, session_id: str, key: str, value: Any) -> bool:
        """Add item to working set"""
        entries = self.store.query_by_session(session_id)
        context_entries = [e for e in entries if e.data.get("type") == "context"]
        
        if not context_entries:
            return False
        
        context = context_entries[-1]
        if "working_set" not in context.data:
            context.data["working_set"] = {}
        
        context.data["working_set"][key] = value
        context.timestamp = datetime.utcnow().isoformat() + 'Z'
        
        return self.store.save_entry(context)
    
    def save_pattern(self, source: MemorySource, pattern: Dict[str, Any], 
                    tags: List[str]) -> str:
        """Save a discovered pattern to working memory"""
        pattern_id = str(uuid.uuid4())
        
        entry = MemoryEntry(
            id=pattern_id,
            timestamp=datetime.utcnow().isoformat() + 'Z',
            source=source,
            level=MemoryLevel.WORKING,
            data={
                "type": "pattern",
                "pattern": pattern,
                "meta_tags": tags + ["PATTERN"]
            },
            ttl=604800  # 7 days
        )
        
        self.store.save_entry(entry)
        return pattern_id
    
    def create_handoff(self, from_source: MemorySource, to_type: str,
                      context: Dict[str, Any], instructions: str) -> str:
        """Create a handoff package for context transfer"""
        handoff_id = str(uuid.uuid4())
        
        entry = MemoryEntry(
            id=handoff_id,
            timestamp=datetime.utcnow().isoformat() + 'Z',
            source=from_source,
            level=MemoryLevel.IMMEDIATE,
            data={
                "type": "handoff",
                "from": asdict(from_source),
                "to": {"type": to_type},
                "context": context,
                "instructions": instructions,
                "meta_tags": ["HANDOFF", f"FROM_{from_source.type.value}"]
            },
            ttl=3600  # 1 hour
        )
        
        self.store.save_entry(entry)
        return handoff_id
    
    def load_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load complete context for a session"""
        entries = self.store.query_by_session(session_id)
        
        if not entries:
            return None
        
        # Separate by type
        context_entries = [e for e in entries if e.data.get("type") == "context"]
        pattern_entries = [e for e in entries if e.data.get("type") == "pattern"]
        
        if not context_entries:
            return None
        
        # Get most recent context
        context = context_entries[-1]
        
        # Build complete context package
        return {
            "session_id": session_id,
            "context": {
                "immediate": {
                    "current_focus": context.data.get("current_focus", {}),
                    "working_set": context.data.get("working_set", {})
                },
                "working": {
                    "patterns": [e.data["pattern"] for e in pattern_entries]
                }
            },
            "metadata": {
                "last_updated": context.timestamp,
                "entry_count": len(entries)
            }
        }
    
    def query(self, tags: Optional[List[str]] = None, 
             session_id: Optional[str] = None,
             level: Optional[MemoryLevel] = None,
             since: Optional[datetime] = None) -> List[MemoryEntry]:
        """Flexible query interface"""
        results = []
        
        if session_id:
            results = self.store.query_by_session(session_id)
        elif tags:
            results = self.store.query_by_tags(tags)
        else:
            # Return recent entries from all levels
            for memory_level in MemoryLevel:
                level_path = self.store.base_path / memory_level.value
                for file_path in sorted(level_path.glob("*.json"), 
                                      key=lambda p: p.stat().st_mtime, 
                                      reverse=True)[:20]:
                    entry = self.store.load_entry(memory_level, file_path.stem)
                    if entry:
                        results.append(entry)
        
        # Filter by level if specified
        if level:
            results = [e for e in results if e.level == level]
        
        # Filter by timestamp if specified
        if since:
            results = [e for e in results 
                      if datetime.fromisoformat(e.timestamp.replace('Z', '+00:00')) > since]
        
        return sorted(results, key=lambda e: e.timestamp, reverse=True)

# Example usage and testing
if __name__ == "__main__":
    # Initialize API
    api = DistributedMemoryAPI()
    
    # Create a chat source
    chat_source = MemorySource(
        type=SourceType.CHAT,
        id="claude-001",
        session="CHAT-2025-07-30-002"
    )
    
    # Create initial context
    context_id = api.create_context(
        session_id="CHAT-2025-07-30-002",
        source=chat_source,
        initial_focus={
            "primary": "Testing distributed memory system",
            "context": "Phase 1 implementation"
        }
    )
    
    print(f"Created context: {context_id}")
    
    # Update focus
    api.update_focus(
        session_id="CHAT-2025-07-30-002",
        new_focus={
            "primary": "Testing memory queries",
            "status": "successful"
        }
    )
    
    # Add to working set
    api.add_to_working_set(
        session_id="CHAT-2025-07-30-002",
        key="test_results",
        value={"phase1": "operational", "storage": "file-based"}
    )
    
    # Save a pattern
    pattern_id = api.save_pattern(
        source=chat_source,
        pattern={
            "name": "Context Persistence Pattern",
            "description": "File-based storage enables simple persistence"
        },
        tags=["TECHNICAL.STORAGE", "INNOVATION.SIMPLE"]
    )
    
    print(f"Saved pattern: {pattern_id}")
    
    # Load complete context
    loaded_context = api.load_context("CHAT-2025-07-30-002")
    print(f"Loaded context: {json.dumps(loaded_context, indent=2)}")
    
    # Query by tags
    pattern_entries = api.query(tags=["PATTERN"])
    print(f"Found {len(pattern_entries)} pattern entries")
    
    # Create handoff
    handoff_id = api.create_handoff(
        from_source=chat_source,
        to_type="agent",
        context=loaded_context,
        instructions="Continue testing the distributed memory system"
    )
    
    print(f"Created handoff: {handoff_id}")
    
    # Clean expired entries
    cleaned = api.store.clean_expired()
    print(f"Cleaned {cleaned} expired entries")
