# LOCAL CANVAS PROTOCOL
*External Document Generation for Distributed Memory*
*Created: 2025-07-30*

## PURPOSE
Distribute memory and processing load by generating documents externally rather than in chat canvas.

## DIRECTIVE FOR ALL CHATS/AGENTS

### When to Use Local Canvas
- Any document > 50 lines
- Code implementations
- Technical specifications  
- Architecture documentation
- Session summaries
- Configuration files
- Any artifact that needs persistence

### File Structure
```
/AI Tutor/Local Canvas/
├── specifications/     # Technical specs, APIs, protocols
├── code/              # Implementations, scripts
├── configurations/    # JSON, YAML configs
├── summaries/         # Session summaries, reports  
├── architectures/     # System designs, diagrams
└── templates/         # Reusable document templates
```

### Naming Convention
```
[YYYY-MM-DD]_[TYPE]_[description].[ext]

Types:
- SPEC: Specification
- CODE: Implementation
- CONFIG: Configuration
- ARCH: Architecture
- SUMM: Summary
- TEMP: Template
- TEST: Test file
```

### Examples
```
2025-07-30_SPEC_memory_api.md
2025-07-30_CODE_memory_handler.py
2025-07-30_CONFIG_redis_setup.json
2025-07-30_ARCH_distributed_system.mermaid
```

## IMPLEMENTATION

### For Claude/GPT Chats
Instead of creating artifacts or large responses:
```python
# OLD: Display in chat
# return huge_content_block

# NEW: Write to Local Canvas
write_file(
    "/AI Tutor/Local Canvas/[appropriate_folder]/[filename]",
    content
)
return "Created: [filename] in Local Canvas - [brief description]"
```

### For n8n Workflows
```javascript
// Add Local Canvas node to all workflows
const saveToCanvas = (content, type, description) => {
  const timestamp = new Date().toISOString().split('T')[0];
  const filename = `${timestamp}_${type}_${description}`;
  const path = `/AI Tutor/Local Canvas/${type.toLowerCase()}/${filename}`;
  
  await $fs.write(path, content);
  return { saved: path, size: content.length };
};
```

### For Python Functions
```python
from pathlib import Path
from datetime import datetime

class LocalCanvas:
    BASE_PATH = Path("/AI Tutor/Local Canvas")
    
    @classmethod
    def save(cls, content, doc_type, description, extension):
        date = datetime.now().strftime("%Y-%m-%d")
        filename = f"{date}_{doc_type}_{description}.{extension}"
        
        # Ensure subdirectory exists
        subdir = cls.BASE_PATH / doc_type.lower()
        subdir.mkdir(exist_ok=True)
        
        # Write file
        filepath = subdir / filename
        filepath.write_text(content)
        
        return str(filepath)
```

## BENEFITS

1. **Memory Distribution**: Keeps chat contexts lean
2. **Persistence**: Documents survive session ends
3. **Cross-Chat Access**: Any chat can read previous work
4. **Version History**: Natural versioning through timestamps
5. **External Processing**: Can be processed by other tools
6. **Reduced Crashes**: Less memory pressure on chat platform

## RETRIEVAL

### List Canvas Contents
```python
list_directory("/AI Tutor/Local Canvas/")
```

### Read Specific Document  
```python
read_file("/AI Tutor/Local Canvas/specifications/2025-07-30_SPEC_memory_api.md")
```

### Search Canvas
```python
search_files("/AI Tutor/Local Canvas/", pattern="memory")
```

## INTEGRATION WITH MEMORY SYSTEM

Local Canvas becomes part of Level 2 (Working Memory):
- Level 1: current_focus.json (immediate)
- Level 2: Local Canvas documents (working)
- Level 3: Google Docs archive (permanent)

## DIRECTIVE SUMMARY

**FROM NOW ON**: 
- Generate substantial documents in Local Canvas, not chat
- Use standardized naming and organization
- Return brief summaries with file locations
- This applies to ALL chats and agents in the system

---
*"Distribute everything - memory, processing, and artifacts"*