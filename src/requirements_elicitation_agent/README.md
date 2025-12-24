# Forge Requirements Assistant

A LangGraph-powered AI agent that helps discover and capture software requirements through interactive discovery sessions and document analysis.

## Features

- **Interactive Discovery**: Structured interview process using layered questioning techniques
- **Document Analysis**: Extract requirements from meeting notes, specifications, and other documents
- **Gap Analysis**: Proactively identifies missing requirement areas (security, performance, etc.)
- **Conflict Detection**: Automatically flags contradictory requirements
- **Risk Warnings**: Alerts on potential security or viability issues
- **Adaptive Communication**: Adjusts questioning style based on user expertise
- **Raw Requirements Export**: Generates structured Markdown output ready for formal PRD creation

## Installation

1. Clone the repository:
```bash
cd forge-agent-builder
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -e .
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

## Usage

### Streamlit Web Interface

Run the interactive web interface:

```bash
streamlit run src/requirements_elicitation_agent/streamlit_app.py
```

Then open your browser to http://localhost:8501

### Command Line Interface

Run the agent in CLI mode:

```bash
python -m src.requirements_elicitation_agent.main
```

### MCP Server

Expose the agent as an MCP (Model Context Protocol) server for integration with other tools:

```bash
python -m src.requirements_elicitation_agent.mcp_server
```

Or add to your MCP client configuration (e.g., Claude Desktop):

```json
{
  "mcpServers": {
    "riley-requirements-analyst": {
      "command": "python",
      "args": ["-m", "src.requirements_elicitation_agent.mcp_server"],
      "cwd": "/path/to/forge-agent-builder"
    }
  }
}
```

**Available MCP Tools:**
- `begin-requirements-interview` - Start a new requirements elicitation session
- `discuss-requirements` - Discover requirements through conversation
- `analyze-document-for-requirements` - Extract requirements from documents
- `review-captured-requirements` - See captured requirements
- `generate-requirements-document` - Create formatted spec document
- `conclude-interview` - End a session and clean up

#### HTTP Streamable MCP Server Integration

For web-based clients or REST-style API integrations:

```bash
# Run as HTTP server on port 8000
python -m src.requirements_elicitation_agent.mcp_server --transport http --port 8000
```

**Client Integration Example (curl):**

```bash
# List available tools
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'

# Start a session
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"begin-requirements-interview","arguments":{}},"id":2}'

# Send a message (replace SESSION_ID with actual ID from previous response)
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"discuss-requirements","arguments":{"session_id":"SESSION_ID","message":"I need a user login system"}},"id":3}'
```

**Client Integration Example (JavaScript/TypeScript):**

```typescript
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";

// Connect to the HTTP MCP server
const transport = new StreamableHTTPClientTransport(
  new URL("http://localhost:8000/mcp")
);

const client = new Client(
  { name: "my-requirements-app", version: "1.0.0" },
  { capabilities: {} }
);

await client.connect(transport);

// List available tools
const tools = await client.listTools();

// Start a session
const startResult = await client.callTool({
  name: "begin-requirements-interview",
  arguments: {}
});

const sessionId = JSON.parse(startResult.content[0].text).session_id;

// Send a message
const messageResult = await client.callTool({
  name: "discuss-requirements",
  arguments: {
    session_id: sessionId,
    message: "I need to build a user authentication system"
  }
});

// Get requirements
const reqsResult = await client.callTool({
  name: "review-captured-requirements",
  arguments: { session_id: sessionId }
});

// Clean up
await client.callTool({
  name: "conclude-interview",
  arguments: { session_id: sessionId }
});
```

**Client Integration Example (Python):**

```python
import requests
import json

base_url = "http://localhost:8000/mcp"
headers = {"Content-Type": "application/json"}

# Initialize connection
response = requests.post(base_url, headers=headers, json={
    "jsonrpc": "2.0",
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "clientInfo": {"name": "my-app", "version": "1.0.0"},
        "capabilities": {}
    },
    "id": 1
})

# Start a requirements session
response = requests.post(base_url, headers=headers, json={
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "begin-requirements-interview",
        "arguments": {"project_name": "My Project"}
    },
    "id": 2
})
result = response.json()["result"]["content"][0]["text"]
session_id = json.loads(result)["session_id"]

# Continue the conversation
response = requests.post(base_url, headers=headers, json={
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "discuss-requirements",
        "arguments": {
            "session_id": session_id,
            "message": "We need secure user authentication with OAuth support"
        }
    },
    "id": 3
})

# Get captured requirements
response = requests.post(base_url, headers=headers, json={
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "review-captured-requirements",
        "arguments": {"session_id": session_id}
    },
    "id": 4
})
requirements = response.json()
```

#### Transport Comparison

| Transport | Use Case | Endpoint |
|-----------|----------|----------|
| `stdio` (default) | Claude Desktop, local tools | stdin/stdout |
| `http` | Web apps, REST APIs | `/mcp` |

### Programmatic Usage

```python
from src.requirements_elicitation_agent import create_graph
from langchain_core.messages import HumanMessage

# Create the agent
graph = create_graph()
config = {"configurable": {"thread_id": "my-session"}}

# Initialize
for event in graph.stream({}, config, stream_mode="values"):
    print(event["messages"][-1].content)

# Send messages
state = {"messages": [HumanMessage(content="I need a login system")]}
for event in graph.stream(state, config, stream_mode="values"):
    print(event["messages"][-1].content)
```

## Architecture

The agent is built with:

- **LangGraph**: State machine orchestration
- **OpenAI GPT-4o**: Language model for generation and structured output
- **Pydantic**: Schema validation
- **Streamlit**: Web interface

### Key Components

- `state.py`: State schema definitions
- `nodes.py`: Core agent logic
- `graph.py`: Graph orchestration
- `tools.py`: Tool definitions
- `streamlit_app.py`: Web UI
- `main.py`: CLI interface

## Persona & Behavior

The agent embodies the **"Requirement Architect"** persona with facilitative tone, 
structured approach, and adaptive communication. See `../../agent-specs/requirements-elicitation-agent/persona.md`

## Testing

Run the test suite:

```bash
pytest tests/requirements_elicitation_agent/ -v
```

## License

See LICENSE file in repository root.
