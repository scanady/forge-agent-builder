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
- `start_session` - Start a new requirements elicitation session
- `send_message` - Send a message to Riley in an existing session
- `upload_document` - Upload document content for requirement extraction
- `get_requirements` - Get all captured requirements
- `export_requirements_markdown` - Export requirements as formatted Markdown
- `end_session` - End a session and clean up

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
