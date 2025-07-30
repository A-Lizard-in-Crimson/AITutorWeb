# Distributed Memory API Specification
*Version: 1.0*
*Created: 2025-07-30T05:40:00Z*
*Type: Technical Specification*

## Overview

The Distributed Memory API provides a unified interface for all system components (Chats, Agents, Functions, APIs) to read and write to a shared memory layer, effectively extending context windows and enabling seamless handoffs between systems.

## Core Architecture

### API Design Principles
1. **RESTful + WebSocket Hybrid**: REST for CRUD operations, WebSocket for real-time updates
2. **Stateless Components**: All state externalized to the memory layer
3. **Event-Driven**: All memory changes broadcast to subscribers
4. **Hierarchical Storage**: Three-tier system (Immediate, Working, Long-term)
5. **Tag-Based Organization**: Leverages existing Meta Tag System

## API Endpoints

### Memory Management

#### 1. Context Operations
```
GET    /api/v1/memory/context/{session_id}
POST   /api/v1/memory/context
PUT    /api/v1/memory/context/{session_id}
DELETE /api/v1/memory/context/{session_id}
```

#### 2. Query Operations
```
GET    /api/v1/memory/query?tags={tags}&level={level}&since={timestamp}
POST   /api/v1/memory/search
```

#### 3. Handoff Operations
```
POST   /api/v1/memory/handoff
GET    /api/v1/memory/handoff/{handoff_id}
```

#### 4. Agent Operations
```
GET    /api/v1/memory/agent/{agent_id}/state
POST   /api/v1/memory/agent/{agent_id}/update
GET    /api/v1/memory/agent/{agent_id}/history
```

#### 5. Subscription Management
```
POST   /api/v1/memory/subscribe
DELETE /api/v1/memory/subscribe/{subscription_id}
GET    /api/v1/memory/subscriptions
```

## Data Models

### 1. Memory Entry
```json
{
  "id": "uuid",
  "timestamp": "2025-07-30T05:40:00Z",
  "source": {
    "type": "chat|agent|function|api",
    "id": "source_identifier",
    "session": "session_id"
  },
  "level": "immediate|working|longterm",
  "data": {
    "content": {},
    "meta_tags": ["TAG1", "TAG2"],
    "references": ["ref_id1", "ref_id2"]
  },
  "ttl": 3600,
  "visibility": "private|shared|public"
}
```

### 2. Context Package
```json
{
  "session_id": "CHAT-2025-07-30-002",
  "context": {
    "immediate": {
      "current_focus": {},
      "working_set": {},
      "active_agents": []
    },
    "working": {
      "project_state": {},
      "discovered_patterns": [],
      "key_decisions": []
    },
    "references": {
      "files": [],
      "previous_sessions": [],
      "related_agents": []
    }
  },
  "metadata": {
    "platform": "claude",
    "window_usage": "moderate",
    "last_checkpoint": "timestamp"
  }
}
```

### 3. Handoff Package
```json
{
  "handoff_id": "uuid",
  "from": {
    "type": "chat",
    "id": "session_id",
    "platform": "claude"
  },
  "to": {
    "type": "agent|chat|function",
    "id": "target_id"
  },
  "context": {},
  "instructions": "Continue with implementation...",
  "priority": "immediate|normal|background",
  "expiry": "timestamp"
}
```

## WebSocket Events

### Event Types
```javascript
// Memory update event
{
  "event": "memory.updated",
  "level": "immediate|working|longterm",
  "data": {
    "entry_id": "uuid",
    "source": {},
    "changes": {}
  }
}

// Handoff request
{
  "event": "handoff.requested",
  "data": {
    "handoff_id": "uuid",
    "from": {},
    "to": {},
    "priority": "immediate"
  }
}

// Agent state change
{
  "event": "agent.state_changed",
  "data": {
    "agent_id": "id",
    "old_state": {},
    "new_state": {}
  }
}
```

## Storage Implementation

### Level 1: Immediate Context (Redis)
```python
# Key structure
immediate:{session_id}:focus     # Current focus
immediate:{session_id}:working   # Working set
immediate:{agent_id}:state       # Agent state

# TTL: 24 hours default
```

### Level 2: Working Memory (PostgreSQL)
```sql
CREATE TABLE working_memory (
  id UUID PRIMARY KEY,
  source_type VARCHAR(50),
  source_id VARCHAR(255),
  session_id VARCHAR(255),
  data JSONB,
  meta_tags TEXT[],
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  ttl INTEGER DEFAULT 604800  -- 7 days
);

CREATE INDEX idx_meta_tags ON working_memory USING GIN(meta_tags);
CREATE INDEX idx_session ON working_memory(session_id);
CREATE INDEX idx_source ON working_memory(source_type, source_id);
```

### Level 3: Long-term Storage (Files + Cloud)
- Google Docs for documentation
- GitHub for code artifacts
- Local filesystem for immediate access
- S3/GCS for large data sets

## Authentication & Security

### API Key Management
```http
Authorization: Bearer {api_key}
X-Memory-Session: {session_id}
X-Memory-Source: {source_identifier}
```

### Access Control
```json
{
  "access_rules": {
    "read": ["self", "authorized_agents"],
    "write": ["self"],
    "delete": ["self", "admin"],
    "share": ["self"]
  }
}
```

## Rate Limiting

### Tier Structure
```yaml
free_tier:
  requests_per_minute: 60
  storage_mb: 100
  sessions: 5

standard_tier:
  requests_per_minute: 300
  storage_mb: 1000
  sessions: 50

unlimited_tier:
  requests_per_minute: -1
  storage_mb: -1
  sessions: -1
```

## Client Libraries

### Python Client
```python
from distributed_memory import MemoryClient

client = MemoryClient(api_key="...")
context = client.load_context(session_id="CHAT-2025-07-30-002")
client.update_focus({"primary": "New focus area"})
```

### JavaScript Client
```javascript
import { MemoryClient } from '@distributed-memory/client';

const client = new MemoryClient({ apiKey: '...' });
const context = await client.loadContext(sessionId);
await client.updateFocus({ primary: 'New focus area' });
```

### n8n Node
```javascript
// Custom n8n node for memory operations
class DistributedMemoryNode {
  async execute() {
    const memory = new MemoryClient(this.credentials);
    const context = await memory.loadContext(
      this.getNodeParameter('sessionId')
    );
    // Process with context
    return this.prepareOutputData([{ json: context }]);
  }
}
```

## Deployment Architecture

### Docker Compose Stack
```yaml
version: '3.8'
services:
  api:
    image: distributed-memory-api:latest
    environment:
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://...
    ports:
      - "8080:8080"
  
  redis:
    image: redis:7-alpine
    volumes:
      - redis-data:/data
  
  postgres:
    image: postgres:15
    volumes:
      - postgres-data:/var/lib/postgresql/data
  
  websocket:
    image: distributed-memory-ws:latest
    ports:
      - "8081:8081"
```

## Performance Considerations

### Caching Strategy
1. **Edge Cache**: CloudFlare for read-heavy operations
2. **Application Cache**: Redis for session data
3. **Query Cache**: PostgreSQL query results
4. **Client Cache**: Local storage for offline capability

### Optimization Techniques
- Batch operations for multiple updates
- Compression for large payloads
- Partial updates using JSON Patch
- Background sync for non-critical updates

## Monitoring & Observability

### Key Metrics
```yaml
metrics:
  - memory_operations_per_second
  - context_reconstruction_time
  - handoff_success_rate
  - storage_usage_by_level
  - active_sessions_count
  - websocket_connections
```

### Logging Format
```json
{
  "timestamp": "2025-07-30T05:40:00Z",
  "level": "INFO",
  "service": "memory-api",
  "operation": "context_load",
  "session_id": "...",
  "duration_ms": 45,
  "status": "success"
}
```

## Error Handling

### Standard Error Response
```json
{
  "error": {
    "code": "CONTEXT_NOT_FOUND",
    "message": "Context for session not found",
    "details": {
      "session_id": "...",
      "suggestion": "Initialize context first"
    }
  },
  "request_id": "uuid"
}
```

### Error Codes
- `CONTEXT_NOT_FOUND`: Context doesn't exist
- `MEMORY_LIMIT_EXCEEDED`: Storage quota exceeded
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INVALID_HANDOFF`: Handoff validation failed
- `PERMISSION_DENIED`: Insufficient access rights

## Migration Path

### Phase 1: Local Development
1. File-based storage implementation
2. Basic REST API
3. Simple Python/JS clients

### Phase 2: Cloud Deployment
1. Redis + PostgreSQL backend
2. WebSocket support
3. Authentication system

### Phase 3: Production Scale
1. Multi-region deployment
2. Advanced caching
3. Analytics and monitoring

### Phase 4: Enterprise Features
1. Private deployments
2. Compliance features
3. Advanced access control

---
*Next Step: Implement Phase 1 prototype with file-based storage*
