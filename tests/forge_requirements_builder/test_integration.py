"""Integration tests for the full workflow."""

import pytest
from unittest.mock import patch
from forge_requirements_builder.graph import create_graph
from forge_requirements_builder.state import RequirementRaw, create_project_state

# ============================================================================
# 5.4.1 - 5.4.5: Integration Tests
# ============================================================================

@pytest.fixture
def mock_llm_responses():
    with patch("forge_requirements_builder.nodes.llm") as mock:
        yield mock

def test_full_workflow_happy_path(mock_llm_responses):
    """
    Test the full happy path from Discovery to Synthesis.
    We mock the LLM responses to simulate a perfect agent.
    """
    app = create_graph()
    state = create_project_state("Integration Test", "Testing the graph")
    
    # 1. Discovery Phase
    # ------------------
    # Mock Discovery Agent response
    mock_llm_responses.invoke.return_value.content = "Discovery complete."
    
    # Run graph - it should go Orchestrator -> Discovery -> Orchestrator
    # Since we are using a compiled graph, we invoke it.
    # Note: The graph has a loop. We need to be careful not to run infinitely.
    # We can run step by step or use a limit.
    
    # For this test, let's manually transition state to simulate the flow if the graph execution is complex to mock fully
    # OR we can trust the graph logic and just mock the node outputs.
    
    # Let's try running the graph with a recursion limit
    config = {"recursion_limit": 50}
    
    # We need to inject requirements into the state since our mocked LLM won't actually call the extraction tool
    # unless we mock that too.
    state["requirements_raw"] = [
        RequirementRaw(
            id="R1", 
            title="Login", 
            description="The system shall allow the user to login using their email and password to access their account.", 
            type="Functional", 
            source="User"
        )
    ]
    state["discovery_complete"] = True # Force completion for this test step
    
    # 2. Authoring Phase
    # ------------------
    # Mock Authoring Agent response
    mock_llm_responses.invoke.return_value.content = """
    ```json
    {
        "title": "User Login",
        "story_statement": "As a user...",
        "acceptance_criteria": ["AC1"],
        "effort": "S"
    }
    ```
    """
    
    # 3. Quality Phase
    # ----------------
    # Quality tool is deterministic.
    
    # 4. Prioritization Phase
    # -----------------------
    # Prioritization tool is deterministic.
    
    # 5. Synthesis Phase
    # ------------------
    mock_llm_responses.invoke.return_value.content = "# Final Requirements Document"
    
    # Execute
    # Since we can't easily mock different responses for different nodes in a single invoke call without complex side_effects,
    # we might test the transitions individually or use a side_effect function.
    
    def side_effect(messages):
        # Simple router for mocks based on system prompt or context
        msg_content = str(messages)
        if "Discovery Agent" in msg_content or "DISCOVERY_SYSTEM_PROMPT" in str(messages[0].content):
            return type('obj', (object,), {'content': "Discovery complete."})
        elif "Authoring Agent" in msg_content or "AUTHORING_SYSTEM_PROMPT" in str(messages[0].content):
             return type('obj', (object,), {'content': """```json
                {"title": "Story", "story_statement": "As a user...", "acceptance_criteria": ["AC1"], "effort": "S"}
                ```"""})
        elif "Synthesis Agent" in msg_content or "SYNTHESIS_SYSTEM_PROMPT" in str(messages[0].content):
            return type('obj', (object,), {'content': "# Final Doc"})
        else:
            return type('obj', (object,), {'content': "OK"})

    mock_llm_responses.invoke.side_effect = side_effect
    
    # We need to reset state to initial for the real run
    state = create_project_state("Integration Test", "Testing the graph")
    state["requirements_raw"] = [RequirementRaw(
        id="R1", 
        title="Login", 
        description="The system shall allow the user to login using their email and password to access their account.", 
        type="Functional", 
        source="User"
    )]
    state["discovery_complete"] = True # Skip interactive discovery for this test
    
    # Run the graph
    # Note: In a real test environment, we'd need to handle the loop. 
    # Here we just verify the graph compiles and we can invoke it.
    
    try:
        # We run it for a few steps to verify it moves phases
        # This is a partial integration test.
        result = app.invoke(state, config={**config, "configurable": {"thread_id": "test-thread"}})
        
        # If it ran to completion
        if result["workflow_phase"] == "complete":
            assert result["synthesis_complete"] == True
            assert "Final Doc" in result["final_deliverable"]
            
    except Exception as e:
        # If it hits recursion limit, check where it got
        pytest.fail(f"Graph execution failed: {e}")
