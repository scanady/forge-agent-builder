# MCP Server Design Principles

Best practices for building Model Context Protocol (MCP) servers with FastMCP, learned from the Requirements Analyst implementation.

---

## 1. Tool Naming & Metadata

### Use Kebab-Case Tool Names

MCP tool names must only contain: `A-Z`, `a-z`, `0-9`, underscore (`_`), dash (`-`), and dot (`.`). **Spaces are not allowed** and will cause validation warnings.

Use kebab-case for readable, spec-compliant names:

```python
# Good - kebab-case, spec-compliant
@mcp.tool(
    name="begin-requirements-interview",
    description="Initiates a collaborative interview to discover software requirements"
)
def begin_requirements_interview(project_name: Optional[str] = None) -> dict:

# Avoid - spaces cause validation warnings
@mcp.tool(
    name="Begin Requirements Interview",  # WARNING: spaces not allowed!
    description="..."
)

# Avoid - technical snake_case with no metadata
@mcp.tool()
def begin_requirements_interview(project_name: Optional[str] = None) -> dict:
```

### Decorator Parameters

| Parameter | Purpose | Example |
|-----------|---------|---------|
| `name` | Tool identifier (kebab-case) | `"begin-requirements-interview"` |
| `description` | Explanation of what the tool does | `"Initiates a collaborative interview..."` |

> **Note:** FastMCP only supports `name` and `description`. Parameters like `title` and `tags` are not supported and will cause errors.

### MCP Naming Rules

Per [SEP-986](https://modelcontextprotocol.io/specification/2025-11-25/server/tools#tool-names):
- Allowed characters: `A-Z`, `a-z`, `0-9`, `_`, `-`, `.`
- **No spaces allowed**
- Use kebab-case for readability: `analyze-document-for-requirements`

### Align Tool Names with User Goals

Name tools after what the user wants to accomplish, not technical operations:

| Avoid | Prefer |
|-------|--------|
| `start_session` | `begin-requirements-interview` |
| `send_message` | `discuss-requirements` |
| `upload_document` | `analyze-document-for-requirements` |
| `get_data` | `review-captured-requirements` |
| `export_markdown` | `generate-requirements-document` |
| `end_session` | `conclude-interview` |

---

## 2. Character Encoding

### Avoid Emojis and Special Characters

Windows terminals often use cp1252 encoding which cannot render Unicode emojis. This causes `UnicodeEncodeError` crashes:

```python
# Bad - crashes on Windows
print("🚀 Starting server...")
print("• Item one")

# Good - ASCII-safe alternatives
print("[Server] Starting...")
print("- Item one")
```

### Safe Alternatives

| Emoji | ASCII Alternative |
|-------|-------------------|
| 🚀 | `[Server]` or `>>` |
| ✓ | `[OK]` or `+` |
| ✗ | `[ERROR]` or `x` |
| • | `-` or `*` |
| → | `->` or `>` |

---

## 3. Output Streams

### Use stderr for stdio Transport

MCP's stdio transport reserves `stdout` exclusively for JSON-RPC messages. Any other output to stdout corrupts the protocol:

```python
if __name__ == "__main__":
    import sys
    
    # For stdio transport, use stderr for logging
    # For SSE transport, stdout is safe
    use_sse = "--sse" in sys.argv
    output = sys.stdout if use_sse else sys.stderr
    
    def log(msg: str = ""):
        print(msg, file=output)
    
    log("Server starting...")  # Safe for both transports
    
    if use_sse:
        mcp.run(transport="sse", host="127.0.0.1", port=8765)
    else:
        mcp.run()  # stdio mode
```

---

## 4. Startup Banner

### Display Helpful Information on Launch

When the server starts, display configuration info to stderr:

```python
log("=" * 60)
log("Requirements Analyst - MCP Server")
log("=" * 60)
log()
log("Server Name: requirements-analyst")
log(f"Transport:   {'SSE' if use_sse else 'stdio'}")
if use_sse:
    log(f"URL:         http://{host}:{port}/sse")
log()
log("Available Tools:")
log("  - begin-requirements-interview")
log("  - discuss-requirements")
log("  - review-captured-requirements")
log()
```

### Include Configuration Examples

For Claude Desktop integration, show the exact JSON config needed:

```python
project_root = Path(__file__).parent.parent.parent.absolute()
log("To use with Claude Desktop, add to your config:")
log('{')
log('  "mcpServers": {')
log('    "server-name": {')
log(f'      "command": "{sys.executable}",')
log('      "args": ["-m", "module.path.server"],')
log(f'      "cwd": "{project_root}",')
log('      "env": {')
log(f'        "PYTHONPATH": "{project_root}"')
log('      }')
log('    }')
log('  }')
log('}')
```

---

## 5. Module Resolution

### Set PYTHONPATH for Package Imports

When running as a module with `-m`, Python needs to find your packages. Include `PYTHONPATH` in the Claude Desktop config:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "/path/to/.venv/Scripts/python.exe",
      "args": ["-m", "src.my_agent.mcp_server"],
      "cwd": "/path/to/project",
      "env": {
        "PYTHONPATH": "/path/to/project"
      }
    }
  }
}
```

### Create `__init__.py` Files

Ensure all parent directories are Python packages:

```
src/
  __init__.py          # Required!
  my_agent/
    __init__.py
    mcp_server.py
```

---

## 6. Tool Documentation

### Write Comprehensive Docstrings

Tool descriptions appear in Claude's UI. Make them helpful:

```python
@mcp.tool(name="Analyze Document for Requirements")
def analyze_document_for_requirements(
    session_id: str, 
    document_name: str, 
    document_content: str
) -> dict:
    """
    Analyze a document to extract requirements.
    
    Can extract requirements from various document types:
    - Meeting notes and transcripts
    - User stories and feature requests
    - Existing specifications or RFPs
    - Email threads or Slack discussions
    
    Args:
        session_id: The session ID from 'begin-requirements-interview'.
        document_name: Name/title of the document (e.g., "kickoff-meeting-notes.md").
        document_content: The full text content of the document.
    
    Returns:
        - analysis: Summary of requirements found
        - requirements_discovered: Updated total count
    """
```

### Reference Tool Names Consistently in Documentation

Use the exact tool names in error messages and documentation:

```python
# Good - matches the actual tool name
"No active interview found. Start with 'begin-requirements-interview' first."

# Avoid - technical function name
"No active interview found. Call begin_requirements_interview first."
```

---

## 7. Server Instructions

### Provide Workflow Guidance

The FastMCP `instructions` parameter should explain the overall workflow:

```python
mcp = FastMCP(
    name="requirements-analyst",
    instructions="""
A professional requirements analyst that helps discover and document 
software requirements through structured interviews.

Workflow:
1. Begin with 'begin-requirements-interview' to start a new session
2. Use 'discuss-requirements' to describe your project and answer questions
3. Use 'analyze-document-for-requirements' to extract from existing docs
4. Use 'review-captured-requirements' to verify what's been recorded
5. Use 'generate-requirements-document' for the final deliverable
6. Use 'conclude-interview' when done
"""
)
```

---

## 8. Transport Options

### Support Multiple Transports

Offer both stdio (for Claude Desktop) and SSE (for HTTP clients):

```python
if __name__ == "__main__":
    use_sse = "--sse" in sys.argv
    
    if use_sse:
        # HTTP transport with SSE
        mcp.run(transport="sse", host="127.0.0.1", port=8765)
    else:
        # stdio transport for Claude Desktop
        mcp.run()
```

Usage:
```bash
# stdio mode (default) - for Claude Desktop
python -m src.my_agent.mcp_server

# SSE mode - for HTTP clients
python -m src.my_agent.mcp_server --sse
```

---

## 9. Session Management

### Use Stateful Sessions for Multi-Turn Interactions

Store session state in a module-level dictionary:

```python
_sessions: dict[str, tuple] = {}  # session_id -> (graph, config)

def _get_or_create_session(session_id: Optional[str] = None):
    if session_id and session_id in _sessions:
        return session_id, *_sessions[session_id]
    
    new_id = session_id or str(uuid.uuid4())
    graph = create_graph()
    config = {"configurable": {"thread_id": new_id}}
    _sessions[new_id] = (graph, config)
    return new_id, graph, config
```

### Return Session IDs for Continuity

First tool should return a session ID for subsequent calls:

```python
return {
    "session_id": session_id,  # User needs this for follow-up calls
    "greeting": response_text,
    "next_step": "Use 'Discuss Requirements' to continue"
}
```

---

## 10. Error Handling

### Return Structured Errors

Include error information in the response dict, don't raise exceptions:

```python
if session_id not in _sessions:
    return {
        "error": "No active interview found. Start with 'begin-requirements-interview' first.",
        "response": None,
        "requirements_discovered": 0
    }
```

### Provide Recovery Instructions

Tell users how to fix the problem:

```python
# Good
"error": "No active interview found. Start with 'begin-requirements-interview' first."

# Avoid
"error": "Session not found."
```

---

## Summary Checklist

Before deploying an MCP server:

- [ ] All tools have kebab-case `name` parameters (no spaces!)
- [ ] No emojis or special Unicode characters in output
- [ ] Startup banner prints to stderr (not stdout) for stdio mode
- [ ] PYTHONPATH included in Claude Desktop config example
- [ ] All parent directories have `__init__.py` files
- [ ] Comprehensive docstrings on all tools
- [ ] Error messages reference exact tool names
- [ ] Server instructions explain the workflow
- [ ] Both stdio and SSE transports supported
- [ ] Session IDs returned for stateful interactions
