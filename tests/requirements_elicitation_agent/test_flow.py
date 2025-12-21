"""
Integration tests for full conversation flow.

Tests that the graph properly routes between nodes and captures requirements.
"""

import pytest
import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
from src.requirements_elicitation_agent.graph import create_graph

# Load environment variables
load_dotenv()


def test_first_message_gets_greeting():
    """Test that the first message triggers initializer and gets a greeting."""
    graph = create_graph()
    config = {"configurable": {"thread_id": "test-001"}}
    
    # First user message
    state = {"messages": [HumanMessage(content="hi")]}
    result = graph.invoke(state, config)
    
    # Should have greeting response
    assert len(result["messages"]) >= 2
    assert isinstance(result["messages"][-1], AIMessage)
    assert "Forge Requirements Assistant" in result["messages"][-1].content
    assert result["current_phase"] == "init"


def test_phase_transitions_to_elicitation():
    """Test that after greeting, phase transitions to elicitation when user responds."""
    graph = create_graph()
    config = {"configurable": {"thread_id": "test-002"}}
    
    # First interaction - greeting
    state = {"messages": [HumanMessage(content="hello")]}
    result = graph.invoke(state, config)
    assert result["current_phase"] == "init"
    
    # User chooses interactive discovery
    state = {"messages": [HumanMessage(content="I want interactive discovery")]}
    result = graph.invoke(state, config)
    
    # Phase should be elicitation and interviewer should have asked a question
    assert result["current_phase"] == "elicitation", "Phase should be 'elicitation' after interviewer runs"
    assert len(result["messages"]) >= 2
    assert isinstance(result["messages"][-1], AIMessage)


def test_requirements_are_captured():
    """Test that requirements are actually recorded when user provides information."""
    graph = create_graph()
    config = {"configurable": {"thread_id": "test-003"}}
    
    # Initialize session
    state = {"messages": [HumanMessage(content="hi")]}
    result = graph.invoke(state, config)
    
    # Start interactive discovery
    state = {"messages": [HumanMessage(content="interactive discovery")]}
    result = graph.invoke(state, config)
    assert result["current_phase"] == "elicitation", "Should be in elicitation phase"
    
    # User provides a requirement
    state = {"messages": [HumanMessage(content="Users should be able to log in with email and password")]}
    result = graph.invoke(state, config)
    
    # Should have captured at least one requirement
    assert "requirements" in result, "State should have requirements list"
    assert len(result["requirements"]) > 0, "Should have captured at least one requirement"
    assert any("log in" in req["description"].lower() or "email" in req["description"].lower() 
               for req in result["requirements"]), "Should have captured the login requirement"


def test_multiple_requirements_captured():
    """Test that multiple rounds of Q&A capture multiple requirements."""
    graph = create_graph()
    config = {"configurable": {"thread_id": "test-004"}}
    
    # Initialize and start
    graph.invoke({"messages": [HumanMessage(content="hi")]}, config)
    graph.invoke({"messages": [HumanMessage(content="interactive")]}, config)
    
    # Provide multiple requirements over several turns
    requirements_inputs = [
        "Users need to authenticate with OAuth2",
        "The system should support 10,000 concurrent users",
        "All data must be encrypted at rest"
    ]
    
    for req_input in requirements_inputs:
        result = graph.invoke({"messages": [HumanMessage(content=req_input)]}, config)
    
    # Should have captured multiple requirements
    assert len(result["requirements"]) >= 2, f"Should have captured at least 2 requirements, got {len(result['requirements'])}"


def test_router_handles_show_requirements():
    """Test that asking to show requirements routes to output_generator."""
    graph = create_graph()
    config = {"configurable": {"thread_id": "test-005"}}
    
    # Set up some requirements
    graph.invoke({"messages": [HumanMessage(content="hi")]}, config)
    graph.invoke({"messages": [HumanMessage(content="interactive")]}, config)
    graph.invoke({"messages": [HumanMessage(content="Users can create accounts")]}, config)
    
    # Ask to show requirements
    result = graph.invoke({"messages": [HumanMessage(content="show me the requirements")]}, config)
    
    # Should have output
    last_message = result["messages"][-1]
    assert isinstance(last_message, AIMessage)
    # Output should contain requirement formatting
    assert "REQ-" in last_message.content or "requirement" in last_message.content.lower()


def test_state_persists_across_turns():
    """Test that state (requirements, phase, etc) persists between turns."""
    graph = create_graph()
    config = {"configurable": {"thread_id": "test-006"}}
    
    # First turn
    result1 = graph.invoke({"messages": [HumanMessage(content="hi")]}, config)
    phase1 = result1["current_phase"]
    
    # Second turn - state should persist
    result2 = graph.invoke({"messages": [HumanMessage(content="interactive")]}, config)
    
    # Messages should accumulate, not reset
    assert len(result2["messages"]) > len(result1["messages"]), "Messages should accumulate"
    assert result2["current_phase"] == "elicitation", "Phase should progress to elicitation"
    
    # Third turn - add requirement (use specific requirement to avoid vague clarification)
    result3 = graph.invoke({"messages": [HumanMessage(content="Users must be able to login with email and password")]}, config)
    
    # Requirements should persist
    assert len(result3["requirements"]) > 0, f"Requirements should be captured, got: {result3['messages'][-1].content[:200]}"
    
    # Fourth turn - requirements should still be there
    result4 = graph.invoke({"messages": [HumanMessage(content="Tell me more about user roles")]}, config)
    assert len(result4["requirements"]) == len(result3["requirements"]), "Requirements should persist"


def test_no_infinite_loops():
    """Test that the graph doesn't get stuck in infinite loops."""
    graph = create_graph()
    config = {"configurable": {"thread_id": "test-007"}}
    
    # Run several turns
    graph.invoke({"messages": [HumanMessage(content="hi")]}, config)
    result = graph.invoke({"messages": [HumanMessage(content="interactive")]}, config)
    
    initial_phase = result["current_phase"]
    
    # Next user input - use specific requirement to avoid vague clarification
    result = graph.invoke({"messages": [HumanMessage(content="Users must be able to create profile with username and email")]}, config)
    
    # Should have progressed (either stayed in elicitation with new requirement, or moved to gap analysis)
    assert result["current_phase"] in ["elicitation", "gap_analysis"], "Should be in a valid phase"
    assert len(result["requirements"]) > 0, f"Should have captured requirement, got: {result['messages'][-1].content[:200]}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
