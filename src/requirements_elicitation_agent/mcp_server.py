"""
MCP Server for Requirements Elicitation Agent.

Exposes the requirements elicitation agent as an MCP server using FastMCP.
This provides a programmatic interface for other tools to interact with the agent.
"""

import sys
import uuid
import functools
from pathlib import Path
from typing import Optional, Callable, Any
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from langchain_core.messages import HumanMessage, AIMessage

from .graph import create_graph

# Timeout configuration (in seconds)
TOOL_TIMEOUT = 120  # 2 minutes max per tool call

def _log(msg: str) -> None:
    """Log to stderr (safe for stdio transport)."""
    print(f"[requirements-analyst] {msg}", file=sys.stderr, flush=True)


def with_timeout(timeout_seconds: int = TOOL_TIMEOUT):
    """
    Decorator to add timeout handling to MCP tool functions.
    
    If the wrapped function takes longer than timeout_seconds,
    returns a graceful error response instead of hanging.
    """
    def decorator(func: Callable[..., dict]) -> Callable[..., dict]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> dict:
            _log(f"Starting {func.__name__}...")
            
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(func, *args, **kwargs)
                try:
                    result = future.result(timeout=timeout_seconds)
                    _log(f"Completed {func.__name__}")
                    return result
                except FuturesTimeoutError:
                    _log(f"TIMEOUT: {func.__name__} exceeded {timeout_seconds}s")
                    # Return a graceful error response
                    return {
                        "error": f"Request timed out after {timeout_seconds} seconds. The AI model may be slow. Please try again.",
                        "suggestion": "If this keeps happening, try shorter messages or break your request into smaller parts.",
                        "response": None
                    }
                except Exception as e:
                    _log(f"ERROR in {func.__name__}: {type(e).__name__}: {e}")
                    return {
                        "error": f"An error occurred: {type(e).__name__}: {str(e)}",
                        "response": None
                    }
        return wrapper
    return decorator

# Load environment variables
load_dotenv()

# MCP server instructions
MCP_INSTRUCTIONS = """
A professional requirements analyst that helps discover, capture, and document 
software requirements through structured interviews and document analysis.

Workflow:
1. Begin with 'begin-requirements-interview' to start a new elicitation session
2. Use 'discuss-requirements' to have a conversation - describe your project, features, 
   user needs, constraints, etc. The analyst will ask clarifying questions and capture requirements
3. Use 'analyze-document-for-requirements' to extract requirements from existing documents
   like meeting notes, specs, or user stories
4. Use 'review-captured-requirements' anytime to see what's been discovered so far
5. Use 'generate-requirements-document' to get a formatted requirements specification
6. Use 'conclude-interview' when done

Focuses on discovering WHAT the system should do (functional requirements) and 
HOW WELL it should perform (non-functional requirements), while deferring implementation 
details to the development team.
"""

# Store sessions (thread_id -> graph instance)
_sessions: dict[str, tuple] = {}  # thread_id -> (graph, config)


def _get_or_create_session(session_id: Optional[str] = None) -> tuple[str, Any, dict]:
    """Get existing session or create a new one."""
    if session_id and session_id in _sessions:
        graph, config = _sessions[session_id]
        return session_id, graph, config
    
    # Create new session
    new_id = session_id or str(uuid.uuid4())
    graph = create_graph()
    config = {"configurable": {"thread_id": new_id}}
    _sessions[new_id] = (graph, config)
    return new_id, graph, config


def _register_tools(server: FastMCP) -> None:
    """Register all MCP tools with the server."""
    
    @server.tool(
        name="begin-requirements-interview",
        description="Initiates a collaborative interview to discover and document software requirements through structured conversation"
    )
    def begin_requirements_interview(project_name: Optional[str] = None) -> dict:
        """
        Start a new requirements elicitation interview.
        
        The analyst will introduce themselves and begin discovering your software requirements
        through a collaborative conversation, asking about your project goals,
        users, features, and constraints.
        
        Args:
            project_name: Optional name for the project being analyzed.
        
        Returns:
            - session_id: Keep this to continue the conversation
            - greeting: Introduction and opening questions
        """
        @with_timeout(TOOL_TIMEOUT)
        def _execute():
            session_id, graph, config = _get_or_create_session()
            
            # Initialize the session to get the greeting
            init_message = "__init__"
            if project_name:
                init_message = f"__init__ for project: {project_name}"
            
            state = {"messages": [HumanMessage(content=init_message)]}
            
            response_text = ""
            for event in graph.stream(state, config, stream_mode="values"):
                if "messages" in event and event["messages"]:
                    last_msg = event["messages"][-1]
                    if isinstance(last_msg, AIMessage):
                        response_text = last_msg.content
            
            return {
                "session_id": session_id,
                "greeting": response_text,
                "next_step": "Use 'discuss-requirements' to describe your project and continue the conversation"
            }
        
        return _execute()

    @server.tool(
        name="discuss-requirements",
        description="Share project details, answer questions, and discuss features. The analyst will ask clarifying questions and capture requirements as you talk."
    )
    def elicit_requirements(session_id: str, message: str) -> dict:
        """
        Continue the requirements discovery conversation.
        
        Share information about your project - describe features you need, user workflows,
        business rules, performance expectations, or any constraints. The analyst will:
        - Ask clarifying questions to understand the full picture
        - Identify implicit requirements you might have missed
        - Capture requirements in a structured format
        
        Args:
            session_id: The session ID from 'begin-requirements-interview'.
            message: Describe your needs, answer questions, or ask for clarification.
        
        Returns:
            - response: Follow-up questions or acknowledgments
            - requirements_discovered: Number of requirements captured so far
        """
        if session_id not in _sessions:
            return {
                "error": f"No active interview found. Start with 'begin-requirements-interview' first.",
                "response": None,
                "requirements_discovered": 0
            }
        
        @with_timeout(TOOL_TIMEOUT)
        def _execute():
            graph, config = _sessions[session_id]
            state = {"messages": [HumanMessage(content=message)]}
            
            response_text = ""
            for event in graph.stream(state, config, stream_mode="values"):
                if "messages" in event and event["messages"]:
                    last_msg = event["messages"][-1]
                    if isinstance(last_msg, AIMessage):
                        response_text = last_msg.content
            
            # Get current requirements count
            current_state = graph.get_state(config)
            req_count = len(current_state.values.get("requirements", []))
            
            return {
                "response": response_text,
                "requirements_discovered": req_count
            }
        
        return _execute()

    @server.tool(
        name="analyze-document-for-requirements",
        description="Upload meeting notes, specs, user stories, or other documents to analyze and extract requirements automatically"
    )
    def analyze_document_for_requirements(session_id: str, document_name: str, document_content: str) -> dict:
        """
        Analyze a document to extract requirements.
        
        Can extract requirements from various document types:
        - Meeting notes and transcripts
        - User stories and feature requests
        - Existing specifications or RFPs
        - Email threads or Slack discussions
        - Competitor analysis or research notes
        
        Args:
            session_id: The session ID from 'begin-requirements-interview'.
            document_name: Name/title of the document (e.g., "kickoff-meeting-notes.md").
            document_content: The full text content of the document.
        
        Returns:
            - analysis: Summary of requirements found in the document
            - requirements_discovered: Updated total count of captured requirements
        """
        if session_id not in _sessions:
            return {
                "error": f"No active interview found. Start with 'begin-requirements-interview' first.",
                "analysis": None,
                "requirements_discovered": 0
            }
        
        @with_timeout(TOOL_TIMEOUT)
        def _execute():
            import tempfile
            
            graph, config = _sessions[session_id]
            
            # Create a temporary file for the agent to process
            temp_dir = Path(tempfile.gettempdir())
            temp_path = temp_dir / document_name
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(document_content)
            
            file_message = f"I uploaded a file: {temp_path}"
            state = {"messages": [HumanMessage(content=file_message)]}
            
            response_text = ""
            for event in graph.stream(state, config, stream_mode="values"):
                if "messages" in event and event["messages"]:
                    last_msg = event["messages"][-1]
                    if isinstance(last_msg, AIMessage):
                        response_text = last_msg.content
            
            # Get current requirements count
            current_state = graph.get_state(config)
            req_count = len(current_state.values.get("requirements", []))
            
            return {
                "analysis": response_text,
                "requirements_discovered": req_count
            }
        
        return _execute()

    @server.tool(
        name="review-captured-requirements",
        description="View the complete list of requirements captured from your conversation and documents, organized by category"
    )
    def review_captured_requirements(session_id: str) -> dict:
        """
        Review all requirements discovered so far in this session.
        
        Returns the raw list of requirements captured from your
        conversation and any documents analyzed. Use this to verify what's been
        recorded before generating the final document.
        
        Args:
            session_id: The session ID from 'begin-requirements-interview'.
        
        Returns:
            - requirements: List of all captured requirements
            - count: Total number of requirements
            - coverage_areas: Categories of requirements discovered
        """
        if session_id not in _sessions:
            return {
                "error": f"No active interview found. Start with 'begin-requirements-interview' first.",
                "requirements": [],
                "count": 0
            }
        
        graph, config = _sessions[session_id]
        current_state = graph.get_state(config)
        requirements = current_state.values.get("requirements", [])
        
        # Categorize requirements by type if possible
        categories = set()
        for req in requirements:
            # Requirements are dicts with 'description', 'category', etc.
            req_text = req.get("description", "") if isinstance(req, dict) else str(req)
            req_text_lower = req_text.lower()
            
            # Also use the category field if available
            if isinstance(req, dict) and req.get("category"):
                categories.add(req["category"])
            
            if "performance" in req_text_lower or "speed" in req_text_lower or "latency" in req_text_lower:
                categories.add("Performance")
            if "security" in req_text_lower or "auth" in req_text_lower or "encrypt" in req_text_lower:
                categories.add("Security")
            if "user" in req_text_lower or "interface" in req_text_lower or "ui" in req_text_lower:
                categories.add("User Experience")
            if "data" in req_text_lower or "store" in req_text_lower or "database" in req_text_lower:
                categories.add("Data Management")
            if "api" in req_text_lower or "integrat" in req_text_lower:
                categories.add("Integration")
        
        if not categories:
            categories = {"General"}
        
        return {
            "requirements": requirements,
            "count": len(requirements),
            "coverage_areas": list(categories)
        }

    @server.tool(
        name="generate-requirements-document",
        description="Generate a professional requirements document suitable for stakeholder review or development handoff, organized by category"
    )
    def generate_requirements_document(session_id: str, format: str = "markdown") -> dict:
        """
        Generate a formatted requirements specification document.
        
        Creates a professional requirements document from all discovered requirements,
        organized by category with proper formatting suitable for stakeholder review
        or development handoff.
        
        Args:
            session_id: The session ID from 'begin-requirements-interview'.
            format: Output format - currently supports "markdown" (default).
        
        Returns:
            - document: The formatted requirements specification
            - requirements_count: Number of requirements included
        """
        if session_id not in _sessions:
            return {
                "error": f"No active interview found. Start with 'begin-requirements-interview' first.",
                "document": None,
                "requirements_count": 0
            }
        
        @with_timeout(TOOL_TIMEOUT)
        def _execute():
            graph, config = _sessions[session_id]
            
            # Generate the output
            state = {"messages": [HumanMessage(content="show requirements")]}
            
            response_text = ""
            for event in graph.stream(state, config, stream_mode="values"):
                if "messages" in event and event["messages"]:
                    last_msg = event["messages"][-1]
                    if isinstance(last_msg, AIMessage):
                        response_text = last_msg.content
            
            current_state = graph.get_state(config)
            req_count = len(current_state.values.get("requirements", []))
            
            return {
                "document": response_text,
                "requirements_count": req_count,
                "format": format
            }
        
        return _execute()

    @server.tool(
        name="conclude-interview",
        description="Complete the interview and clean up session resources. Make sure to save the requirements document first."
    )
    def conclude_interview(session_id: str) -> dict:
        """
        End the requirements interview and clean up the session.
        
        Call this when you're done gathering requirements. Make sure to save
        the generated requirements document before concluding.
        
        Args:
            session_id: The session ID to end.
        
        Returns:
            - summary: Brief summary of what was accomplished
        """
        if session_id in _sessions:
            graph, config = _sessions[session_id]
            current_state = graph.get_state(config)
            req_count = len(current_state.values.get("requirements", []))
            
            del _sessions[session_id]
            return {
                "summary": f"Interview concluded. Captured {req_count} requirements.",
                "requirements_captured": req_count,
                "session_ended": True
            }
        else:
            return {
                "summary": "No active interview found with that session ID.",
                "session_ended": False
            }


def create_mcp_server(host: str = "127.0.0.1", port: int = 8000) -> FastMCP:
    """Create and configure the MCP server with tools."""
    server = FastMCP(
        name="requirements-analyst",
        instructions=MCP_INSTRUCTIONS,
        host=host,
        port=port
    )
    _register_tools(server)
    return server


# Create default MCP server for imports
mcp = create_mcp_server()


def _parse_args():
    """Parse command line arguments for transport configuration."""
    import argparse
    parser = argparse.ArgumentParser(
        description="Requirements Analyst MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Transport Options:
  stdio   Use standard input/output (default, for Claude Desktop)
  http    Use HTTP Streamable protocol (for REST-style clients)

Examples:
  python -m src.requirements_elicitation_agent.mcp_server
  python -m src.requirements_elicitation_agent.mcp_server --transport http --port 8000
        """
    )
    parser.add_argument(
        "--transport", "-t",
        choices=["stdio", "http", "streamable-http"],
        default="stdio",
        help="Transport protocol to use (default: stdio)"
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8000,
        help="Port for HTTP transport (default: 8000)"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind for HTTP transport (default: 0.0.0.0)"
    )
    return parser.parse_args()


# Run the server when executed directly
if __name__ == "__main__":
    args = _parse_args()
    
    # Normalize transport name
    transport = args.transport
    if transport == "http":
        transport = "streamable-http"
    
    # For stdio transport, stdout is reserved for JSON-RPC - use stderr for info
    # For HTTP transport, we can use stdout
    output = sys.stdout if transport != "stdio" else sys.stderr
    
    def log(msg: str = ""):
        print(msg, file=output)
    
    log("=" * 60)
    log("Requirements Analyst - MCP Server")
    log("=" * 60)
    log()
    log("Server Name: requirements-analyst")
    log(f"Timeout:     {TOOL_TIMEOUT} seconds per tool call")
    log(f"Transport:   {transport}")
    
    if transport == "streamable-http":
        log(f"URL:         http://{args.host}:{args.port}/mcp")
    
    log()
    log("Available Tools:")
    log("  - begin-requirements-interview      - Start a new elicitation session")
    log("  - discuss-requirements              - Discover requirements through conversation")
    log("  - analyze-document-for-requirements - Extract requirements from documents")
    log("  - review-captured-requirements      - See what's been captured")
    log("  - generate-requirements-document    - Create formatted spec document")
    log("  - conclude-interview                - End the session")
    log()
    
    if transport == "stdio":
        project_root = Path(__file__).parent.parent.parent.absolute()
        log("To use with Claude Desktop, add to your config:")
        log('{')                                                                         
        log('  "mcpServers": {')
        log('    "requirements-analyst": {')
        log(f'      "command": "{sys.executable}",')
        log('      "args": ["-m", "src.requirements_elicitation_agent.mcp_server"],')
        log(f'      "cwd": "{project_root}",')
        log('      "env": {')
        log(f'        "PYTHONPATH": "{project_root}"')
        log('      }')
        log('    }')
        log('  }')
        log('}')
        log()
        log(f"Project root: {project_root}")
        log()
        log("Or run with HTTP transport:")
        log("  python -m src.requirements_elicitation_agent.mcp_server --transport http --port 8000")
        log()
    elif transport == "streamable-http":
        log("HTTP Streamable Transport:")
        log(f"  POST requests to http://{args.host}:{args.port}/mcp")
        log()
        log("Example (curl):")
        log('  curl -X POST http://localhost:8000/mcp \\')
        log('    -H "Content-Type: application/json" \\')
        log('    -d \'{"jsonrpc":"2.0","method":"tools/list","id":1}\'')
        log()
    
    log("Server running... (Press Ctrl+C to stop)")
    log("=" * 60)
    output.flush()
    
    # Create server with appropriate host/port for the transport
    if transport == "stdio":
        server = mcp  # Use default server for stdio
        server.run()
    else:
        # Create a new server with the specified host/port for HTTP
        server = create_mcp_server(host=args.host, port=args.port)
        server.run(transport=transport)