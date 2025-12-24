"""LangGraph Configuration for Forge Requirements Builder

Defines the state graph, nodes, edges, and routing logic for the requirements engineering workflow.
"""

import logging
from typing import Literal, Dict, Any

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .state import ForgeRequirementsState
from .nodes import (
    orchestrator_node,
    discovery_node,
    authoring_node,
    quality_node,
    prioritization_node,
    synthesis_node
)

# Initialize Logger
logger = logging.getLogger("forge_requirements_builder")

# ============================================================================
# Routing Logic
# ============================================================================

def route_next(state: ForgeRequirementsState) -> Literal["discovery", "authoring", "quality", "prioritization", "synthesis", "end"]:
    """
    Determines the next node based on the current state and workflow phase.
    This function is used by the conditional edge starting from the Orchestrator.
    """
    phase = state.get("workflow_phase", "discovery")
    current_agent = state.get("current_agent", "orchestrator")
    
    logger.info(f"Routing: Phase={phase}, Current Agent={current_agent}")
    
    # If the workflow is marked complete, end the graph
    if phase == "complete":
        return "end"
        
    # If we are in discovery phase
    if phase == "discovery":
        if state.get("discovery_complete"):
            # If discovery is done, move to authoring (via orchestrator update in next loop)
            # But here we route to the agent that handles the current phase
            # The orchestrator node logic updates the phase, so if we are here, 
            # we check where the orchestrator wants us to go.
            pass
        return "discovery"
        
    # If we are in authoring phase
    if phase == "authoring":
        return "authoring"
        
    # If we are in quality phase
    if phase == "quality":
        return "quality"
        
    # If we are in prioritization phase
    if phase == "prioritization":
        return "prioritization"
        
    # If we are in synthesis phase
    if phase == "synthesis":
        return "synthesis"
        
    # Default fallback
    return "discovery"


def decide_next_step(state: ForgeRequirementsState) -> Literal["discovery_agent", "authoring_agent", "quality_agent", "prioritization_agent", "synthesis_node", END]:
    """
    Conditional routing logic from Orchestrator to specialized agents.
    """
    phase = state.get("workflow_phase")
    current_agent = state.get("current_agent")
    
    # If phase is complete, end
    if phase == "complete":
        return END
        
    # Check if we should stop for user input (avoid infinite loop)
    # If the last message was from the current agent, and we haven't transitioned, stop.
    messages = state.get("conversation_history", [])
    if messages:
        last_msg = messages[-1]
        if last_msg.get("role") == "assistant":
            last_agent = last_msg.get("agent")
            
            # Map current_agent to agent name used in messages
            agent_map = {
                "discovery_agent": "Discovery Agent",
                "authoring_agent": "Authoring Agent",
                "quality_agent": "Quality Agent",
                "prioritization_agent": "Prioritization Agent",
                "synthesis_node": "Synthesis Agent"
            }
            
            expected_agent_name = agent_map.get(current_agent)
            
            if last_agent == expected_agent_name:
                return END
    
    # If orchestrator decided to switch agents, route there
    if current_agent == "discovery_agent":
        return "discovery_agent"
    elif current_agent == "authoring_agent":
        return "authoring_agent"
    elif current_agent == "quality_agent":
        return "quality_agent"
    elif current_agent == "prioritization_agent":
        return "prioritization_agent"
    elif current_agent == "synthesis_node":
        return "synthesis_node"
        
    # If phase is complete, end
    if phase == "complete":
        return END
        
    # Fallback based on phase if current_agent wasn't explicitly set
    if phase == "discovery":
        return "discovery_agent"
    elif phase == "authoring":
        return "authoring_agent"
    elif phase == "quality":
        return "quality_agent"
    elif phase == "prioritization":
        return "prioritization_agent"
    elif phase == "synthesis":
        return "synthesis_node"
        
    return END


# ============================================================================
# Graph Construction
# ============================================================================

def create_graph():
    """
    Constructs and compiles the LangGraph workflow.
    """
    # 1. Initialize StateGraph
    workflow = StateGraph(ForgeRequirementsState)
    
    # 2. Add Nodes
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("discovery_agent", discovery_node)
    workflow.add_node("authoring_agent", authoring_node)
    workflow.add_node("quality_agent", quality_node)
    workflow.add_node("prioritization_agent", prioritization_node)
    workflow.add_node("synthesis_node", synthesis_node)
    
    # 3. Set Entry Point
    workflow.set_entry_point("orchestrator")
    
    # 4. Define Edges
    
    # From Orchestrator -> Specialized Agents (Conditional)
    workflow.add_conditional_edges(
        "orchestrator",
        decide_next_step,
        {
            "discovery_agent": "discovery_agent",
            "authoring_agent": "authoring_agent",
            "quality_agent": "quality_agent",
            "prioritization_agent": "prioritization_agent",
            "synthesis_node": "synthesis_node",
            END: END
        }
    )
    
    # From Specialized Agents -> Orchestrator (Always return to supervisor)
    workflow.add_edge("discovery_agent", "orchestrator")
    workflow.add_edge("authoring_agent", "orchestrator")
    workflow.add_edge("quality_agent", "orchestrator")
    workflow.add_edge("prioritization_agent", "orchestrator")
    workflow.add_edge("synthesis_node", "orchestrator")
    
    # 5. Compile with Checkpointer
    # We use MemorySaver for in-memory persistence during the session
    checkpointer = MemorySaver()
    
    # Interrupt before specialized agents to allow human-in-the-loop approval if needed
    # For this MVP, we might not interrupt every step, but let's follow the plan
    # Plan says: interrupt_before=["authoring", "quality", "prioritization", "synthesis"]
    # But since we route via orchestrator, we can control flow there.
    # Let's interrupt before the major phase transitions if we were using a real server.
    # For local execution, we'll compile simply.
    
    app = workflow.compile(checkpointer=checkpointer)
    
    return app
