"""
Tests specifically for multi-requirement extraction.

These tests verify that complex user statements with multiple requirements
are properly broken down and recorded individually.
"""

import pytest
import uuid
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
from src.requirements_elicitation_agent.graph import create_graph

# Load environment variables
load_dotenv()


def test_extracts_multiple_roles():
    """Test that multiple user roles mentioned in one message are captured separately."""
    graph = create_graph()
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}  # Fresh UUID
    
    # Initialize
    graph.invoke({"messages": [HumanMessage(content="hi")]}, config)
    graph.invoke({"messages": [HumanMessage(content="interactive")]}, config)
    
    # Complex input with multiple roles
    complex_input = "Compliance users need to review products for regulatory compliance. Underwriters review eligibility requirements. Actuaries develop rate tables."
    result = graph.invoke({"messages": [HumanMessage(content=complex_input)]}, config)
    
    # Debug output
    print(f"\nResult requirements: {len(result.get('requirements', []))}")
    print(f"Last message: {result['messages'][-1].content[:200] if result.get('messages') else 'None'}")
    
    # Should extract at least 2-3 requirements
    assert len(result["requirements"]) >= 2, f"Should extract multiple requirements, got {len(result['requirements'])}"
    
    # Check that different roles are mentioned
    req_text = " ".join([r["description"].lower() for r in result["requirements"]])
    roles_found = sum([
        1 if "compliance" in req_text else 0,
        1 if "underwriter" in req_text else 0,
        1 if "actuar" in req_text else 0
    ])
    assert roles_found >= 2, f"Should mention at least 2 different roles, found: {roles_found}"


def test_extracts_api_and_integration_requirements():
    """Test that API/integration requirements are captured."""
    graph = create_graph()
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}  # Fresh UUID
    
    # Initialize and start
    graph.invoke({"messages": [HumanMessage(content="hi")]}, config)
    graph.invoke({"messages": [HumanMessage(content="interactive")]}, config)
    
    # Input with API and integration details
    api_input = "Systems use the application via APIs to provide quotes and product information"
    result = graph.invoke({"messages": [HumanMessage(content=api_input)]}, config)
    
    # Should capture API requirement
    assert len(result["requirements"]) >= 1
    req_text = " ".join([r["description"].lower() for r in result["requirements"]])
    assert "api" in req_text or "external" in req_text or "system" in req_text


def test_workflow_stages_captured():
    """Test that complex workflow descriptions are captured as requirements."""
    graph = create_graph()
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}  # Fresh UUID
    
    # Initialize
    graph.invoke({"messages": [HumanMessage(content="hi")]}, config)
    graph.invoke({"messages": [HumanMessage(content="interactive")]}, config)
    
    # Complex workflow description
    workflow = """
    Stage 1 - Internal Design: Product Manager starts the design. 
    Actuaries calculate pricing. Lawyers write the contract.
    Stage 2 - Government Approval: Compliance Team files with Department of Insurance.
    Stage 3 - Build: IT programs the systems, Marketing creates brochures.
    """
    result = graph.invoke({"messages": [HumanMessage(content=workflow)]}, config)
    
    # Should extract multiple requirements from workflow
    assert len(result["requirements"]) >= 3, f"Expected at least 3 requirements from workflow, got {len(result['requirements'])}"


def test_paraphrase_confirmation_records_all():
    """Test that when user confirms paraphrased requirements, ALL are recorded."""
    graph = create_graph()
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}  # Fresh UUID
    
    # Initialize
    graph.invoke({"messages": [HumanMessage(content="hi")]}, config)
    graph.invoke({"messages": [HumanMessage(content="interactive")]}, config)
    
    # Use specific requirements that won't trigger vagueness detection
    # Each role has a clear action with object
    complex_input = """
    Product managers must create new insurance products with coverage limits and deductibles.
    Actuaries must calculate premium rates using risk assessment data.
    Legal team must draft policy contracts for each product type.
    """
    result1 = graph.invoke({"messages": [HumanMessage(content=complex_input)]}, config)
    
    # Check if it asked for confirmation or recorded directly
    if result1.get("pending_paraphrase"):
        # Confirm
        result2 = graph.invoke({"messages": [HumanMessage(content="yes")]}, config)
        assert len(result2["requirements"]) >= 2, "Should record multiple requirements after confirmation"
    else:
        # Recorded directly - expect at least 2 (LLM may combine some)
        assert len(result1["requirements"]) >= 2, f"Should record multiple requirements directly, got {len(result1['requirements'])}: {result1['messages'][-1].content[:200]}"


def test_incremental_requirements_accumulate():
    """Test that requirements accumulate across multiple turns."""
    graph = create_graph()
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}  # Fresh UUID
    
    # Initialize
    graph.invoke({"messages": [HumanMessage(content="hi")]}, config)
    graph.invoke({"messages": [HumanMessage(content="interactive")]}, config)
    
    # First requirement
    result1 = graph.invoke({"messages": [HumanMessage(content="Users need to log in with SSO")]}, config)
    count1 = len(result1.get("requirements", []))
    
    # Second requirement  
    result2 = graph.invoke({"messages": [HumanMessage(content="Admins can manage user permissions")]}, config)
    count2 = len(result2.get("requirements", []))
    
    # Third requirement
    result3 = graph.invoke({"messages": [HumanMessage(content="System must generate audit logs")]}, config)
    count3 = len(result3.get("requirements", []))
    
    # Requirements should accumulate
    assert count1 >= 1, "First turn should capture at least 1 requirement"
    assert count2 >= count1, "Second turn should maintain or add requirements"
    assert count3 >= 2, "Third turn should have at least 2 requirements total"
    assert count3 >= count1, "Requirements should not decrease"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
