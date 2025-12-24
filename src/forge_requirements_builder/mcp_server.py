import asyncio
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

from forge_requirements_builder.state import create_project_state, ForgeRequirementsState
from forge_requirements_builder.graph import create_graph
from forge_requirements_builder.utils import ProjectLogger

# Load environment variables
load_dotenv()

# Initialize MCP Server
mcp = FastMCP("Forge Requirements Agent")

# Initialize Logger
logger = logging.getLogger("forge_requirements_builder.mcp")

def run_agent_workflow(
    project_name: str, 
    initial_context: str, 
    target_phase: str,
    user_input: Optional[str] = None
) -> Dict[str, Any]:
    """
    Helper to run the LangGraph workflow for a specific phase.
    """
    # Create initial state
    state = create_project_state(project_name, initial_context)
    
    # If we have specific user input, add it to history
    if user_input:
        state["conversation_history"].append({
            "role": "user", 
            "content": user_input,
            "timestamp": datetime.now().isoformat()
        })
    
    # Set the target phase if needed, or let the orchestrator decide
    # For direct agent access, we might want to force the phase
    if target_phase:
        state["workflow_phase"] = target_phase
        # We might need to set current_agent too if we want to bypass orchestrator logic
        # But the graph starts at orchestrator.
        
    # Create and run graph
    graph = create_graph()
    
    # We use a temporary thread_id for this stateless execution
    config = {"configurable": {"thread_id": "mcp-session"}}
    
    final_state = graph.invoke(state, config=config)
    return final_state

@mcp.tool()
def run_discovery(project_name: str, context: str, user_input: str) -> str:
    """
    Run the Discovery Agent to elicit requirements.
    
    Args:
        project_name: Name of the project
        context: Initial project context
        user_input: User's input or answer to a question
        
    Returns:
        The agent's response and current requirements count.
    """
    final_state = run_agent_workflow(project_name, context, "discovery", user_input)
    
    # Extract response
    last_msg = final_state["conversation_history"][-1]
    req_count = len(final_state.get("requirements_raw", []))
    
    return f"Agent Response: {last_msg['content']}\n\nRequirements Captured: {req_count}"

@mcp.tool()
def run_authoring(project_name: str, requirements: List[Dict[str, Any]]) -> str:
    """
    Run the Authoring Agent to generate user stories from requirements.
    
    Args:
        project_name: Name of the project
        requirements: List of raw requirements (dicts)
        
    Returns:
        Generated user stories.
    """
    # Initialize state with provided requirements
    state = create_project_state(project_name, "MCP Request")
    # Convert dicts to RequirementRaw objects if needed, or let Pydantic handle it
    # The state expects RequirementRaw objects.
    from forge_requirements_builder.state import RequirementRaw
    
    req_objs = []
    for r in requirements:
        # Ensure all fields are present or handle defaults
        if "id" not in r: r["id"] = f"REQ-{len(req_objs)+1}"
        if "type" not in r: r["type"] = "Functional"
        if "source" not in r: r["source"] = "MCP"
        req_objs.append(RequirementRaw(**r))
        
    state["requirements_raw"] = req_objs
    state["discovery_complete"] = True
    state["workflow_phase"] = "authoring"
    
    graph = create_graph()
    config = {"configurable": {"thread_id": "mcp-session"}}
    final_state = graph.invoke(state, config=config)
    
    stories = final_state.get("user_stories", [])
    return json.dumps([s.model_dump() for s in stories], indent=2)

@mcp.tool()
def run_quality_check(project_name: str, user_stories: List[Dict[str, Any]]) -> str:
    """
    Run the Quality Agent to check user stories for issues.
    
    Args:
        project_name: Name of the project
        user_stories: List of user stories
        
    Returns:
        List of quality issues found.
    """
    state = create_project_state(project_name, "MCP Request")
    
    from forge_requirements_builder.state import UserStory
    story_objs = [UserStory(**s) for s in user_stories]
    
    state["user_stories"] = story_objs
    state["authoring_complete"] = True
    state["workflow_phase"] = "quality"
    
    graph = create_graph()
    config = {"configurable": {"thread_id": "mcp-session"}}
    final_state = graph.invoke(state, config=config)
    
    issues = final_state.get("quality_issues", [])
    return json.dumps([i.model_dump() for i in issues], indent=2)

@mcp.tool()
def run_prioritization(project_name: str, requirements: List[Dict[str, Any]], framework: str = "MoSCoW") -> str:
    """
    Run the Prioritization Agent to rank requirements.
    
    Args:
        project_name: Name of the project
        requirements: List of requirements
        framework: Prioritization framework (MoSCoW, RICE, etc.)
        
    Returns:
        Prioritized backlog.
    """
    state = create_project_state(project_name, "MCP Request")
    
    from forge_requirements_builder.state import RequirementRaw
    req_objs = []
    for r in requirements:
        if "id" not in r: r["id"] = f"REQ-{len(req_objs)+1}"
        if "type" not in r: r["type"] = "Functional"
        if "source" not in r: r["source"] = "MCP"
        req_objs.append(RequirementRaw(**r))
        
    state["requirements_raw"] = req_objs
    state["quality_issues_resolved"] = True
    state["workflow_phase"] = "prioritization"
    state["prioritization_framework"] = framework
    
    graph = create_graph()
    config = {"configurable": {"thread_id": "mcp-session"}}
    final_state = graph.invoke(state, config=config)
    
    backlog = final_state.get("prioritized_backlog", [])
    return json.dumps([b.model_dump() for b in backlog], indent=2)

if __name__ == "__main__":
    mcp.run()
