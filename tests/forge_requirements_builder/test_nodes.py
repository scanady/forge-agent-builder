"""Unit tests for Graph Nodes."""

import pytest
import tempfile
import os
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime
from forge_requirements_builder.nodes import (
    orchestrator_node,
    discovery_node,
    authoring_node,
    quality_node,
    prioritization_node,
    synthesis_node
)
from forge_requirements_builder.state import (
    RequirementRaw, 
    UserStory, 
    QualityIssue,
    PrioritizedRequirement,
    create_project_state
)

# Mock the LLM to avoid actual API calls
@pytest.fixture
def mock_llm():
    with patch("forge_requirements_builder.nodes.llm") as mock:
        yield mock

# ============================================================================
# ORCHESTRATOR NODE TESTS
# ============================================================================

def test_orchestrator_node_initial_routing():
    """Test orchestrator routes to discovery on initial state."""
    state = create_project_state("Test", "Context")
    state["workflow_phase"] = "discovery"
    state["current_agent"] = "orchestrator"
    
    new_state = orchestrator_node(state)
    
    assert new_state["current_agent"] == "discovery_agent"
    assert new_state["workflow_phase"] == "discovery"


def test_orchestrator_node_discovery_to_authoring():
    """Test orchestrator transitions from discovery to authoring when complete."""
    state = create_project_state("Test", "Context")
    state["workflow_phase"] = "discovery"
    state["discovery_complete"] = True
    state["current_agent"] = "orchestrator"
    
    new_state = orchestrator_node(state)
    
    assert new_state["workflow_phase"] == "authoring"
    assert new_state["current_agent"] == "authoring_agent"


def test_orchestrator_node_authoring_to_quality():
    """Test orchestrator transitions from authoring to quality when complete."""
    state = create_project_state("Test", "Context")
    state["workflow_phase"] = "authoring"
    state["authoring_complete"] = True
    state["current_agent"] = "orchestrator"
    
    new_state = orchestrator_node(state)
    
    assert new_state["workflow_phase"] == "quality"
    assert new_state["current_agent"] == "quality_agent"


def test_orchestrator_node_quality_to_prioritization():
    """Test orchestrator transitions from quality to prioritization when resolved."""
    state = create_project_state("Test", "Context")
    state["workflow_phase"] = "quality"
    state["quality_issues_resolved"] = True
    state["current_agent"] = "orchestrator"
    
    new_state = orchestrator_node(state)
    
    assert new_state["workflow_phase"] == "prioritization"
    assert new_state["current_agent"] == "prioritization_agent"


def test_orchestrator_node_prioritization_to_synthesis():
    """Test orchestrator transitions from prioritization to synthesis when complete."""
    state = create_project_state("Test", "Context")
    state["workflow_phase"] = "prioritization"
    state["prioritization_complete"] = True
    state["current_agent"] = "orchestrator"
    
    new_state = orchestrator_node(state)
    
    assert new_state["workflow_phase"] == "synthesis"
    assert new_state["current_agent"] == "synthesis_node"


@patch("forge_requirements_builder.nodes.extract_from_document")
def test_orchestrator_file_upload(mock_extract):
    """Test orchestrator handles file upload and extracts requirements."""
    state = create_project_state("Test", "Context")
    state["conversation_history"].append({
        "role": "user",
        "content": "I have uploaded a file: /path/to/file.txt"
    })
    
    # Mock the extraction result
    mock_result = Mock()
    mock_result.requirements = [
        Mock(title="Req 1", description="Description 1", type="Functional"),
        Mock(title="Req 2", description="Description 2", type="Non-Functional")
    ]
    mock_extract.return_value = mock_result
    
    new_state = orchestrator_node(state)
    
    assert len(new_state["requirements_raw"]) == 2
    assert new_state["requirements_raw"][0].id == "REQ-001"
    assert new_state["requirements_raw"][0].title == "Req 1"
    assert new_state["requirements_raw"][1].id == "REQ-002"
    assert "Successfully processed file" in new_state["conversation_history"][-1]["content"]


def test_orchestrator_skip_to_authoring():
    """Test orchestrator handles explicit skip to authoring command."""
    state = create_project_state("Test", "Context")
    state["workflow_phase"] = "discovery"
    state["conversation_history"].append({
        "role": "user",
        "content": "skip to authoring"
    })
    
    new_state = orchestrator_node(state)
    
    assert new_state["workflow_phase"] == "authoring"
    assert new_state["current_agent"] == "authoring_agent"


def test_orchestrator_skip_to_quality():
    """Test orchestrator handles explicit skip to quality command."""
    state = create_project_state("Test", "Context")
    state["workflow_phase"] = "discovery"
    state["conversation_history"].append({
        "role": "user",
        "content": "skip to quality"
    })
    
    new_state = orchestrator_node(state)
    
    assert new_state["workflow_phase"] == "quality"
    assert new_state["current_agent"] == "quality_agent"


# ============================================================================
# DISCOVERY NODE TESTS
# ============================================================================

def test_discovery_node_basic_response(mock_llm):
    """Test discovery node generates appropriate response."""
    state = create_project_state("Test", "Context")
    state["conversation_history"].append({"role": "user", "content": "I need a login page."})
    
    # Mock LLM response
    mock_response = Mock()
    mock_response.content = "I understand. You need a login page. Can you tell me more about the authentication requirements?"
    mock_llm.invoke.return_value = mock_response
    
    new_state = discovery_node(state)
    
    assert len(new_state["conversation_history"]) == 2
    assert new_state["conversation_history"][-1]["role"] == "assistant"
    assert new_state["conversation_history"][-1]["agent"] == "Discovery Agent"


def test_discovery_node_marks_complete(mock_llm):
    """Test discovery node marks phase as complete when appropriate."""
    state = create_project_state("Test", "Context")
    state["conversation_history"].append({"role": "user", "content": "That's all the requirements."})
    
    # Mock LLM response with completion signal
    mock_response = Mock()
    mock_response.content = "Great! Discovery complete. Let's move to authoring."
    mock_llm.invoke.return_value = mock_response
    
    new_state = discovery_node(state)
    
    assert new_state["discovery_complete"] == True


def test_discovery_node_extracts_from_response(mock_llm):
    """Test discovery node extracts requirements from its own response."""
    state = create_project_state("Test", "Context")
    state["conversation_history"].append({"role": "user", "content": "Users need to login"})
    
    # Mock LLM response that lists a requirement
    mock_response = Mock()
    mock_response.content = """Thank you! I've captured this as a new requirement:
    
**User Authentication**: The system should allow users to login with credentials."""
    mock_llm.invoke.return_value = mock_response
    
    # Mock the extraction from the response
    with patch("forge_requirements_builder.nodes.extract_from_document") as mock_extract:
        mock_result = Mock()
        mock_result.requirements = [
            Mock(title="User Authentication", description="The system should allow users to login with credentials", type="Functional")
        ]
        mock_extract.return_value = mock_result
        
        new_state = discovery_node(state)
        
        assert len(new_state["requirements_raw"]) == 1
        assert new_state["requirements_raw"][0].title == "User Authentication"
        assert new_state["requirements_raw"][0].source == "Discovery Conversation"


def test_discovery_node_prevents_duplicates(mock_llm):
    """Test discovery node prevents duplicate requirements."""
    state = create_project_state("Test", "Context")
    # Add existing requirement
    state["requirements_raw"].append(
        RequirementRaw(
            id="REQ-001",
            title="User Login",
            description="Users must be able to login",
            type="Functional",
            source="Previous"
        )
    )
    state["conversation_history"].append({"role": "user", "content": "Users need login"})
    
    mock_response = Mock()
    mock_response.content = "I see you already mentioned login. Can you provide more details?"
    mock_llm.invoke.return_value = mock_response
    
    with patch("forge_requirements_builder.nodes.extract_from_document") as mock_extract:
        mock_result = Mock()
        mock_result.requirements = [
            Mock(title="User Login", description="Users must be able to login", type="Functional")
        ]
        mock_extract.return_value = mock_result
        
        new_state = discovery_node(state)
        
        # Should still have only 1 requirement (duplicate prevented)
        assert len(new_state["requirements_raw"]) == 1


# ============================================================================
# AUTHORING NODE TESTS
# ============================================================================

# ============================================================================
# AUTHORING NODE TESTS
# ============================================================================

def test_authoring_node_generates_stories(mock_llm):
    """Test authoring node generates user stories from requirements."""
    state = create_project_state("Test", "Context")
    state["requirements_raw"] = [
        RequirementRaw(id="REQ-001", title="Login", description="Users must login", type="Functional", source="User")
    ]
    
    # Mock LLM response - the authoring node will use the tool which returns structured data
    # But we need to ensure the node completes
    mock_response = Mock()
    mock_response.content = "Stories generated successfully."
    mock_llm.invoke.return_value = mock_response
    
    # The authoring_node calls llm.invoke and expects JSON response
    mock_response = Mock()
    mock_response.content = '''```json
    {
        "title": "User Login",
        "story_statement": "As a user, I want to login so that I can access my account",
        "acceptance_criteria": ["User can enter credentials", "System validates credentials"],
        "effort": "M"
    }
    ```'''
    mock_llm.invoke.return_value = mock_response
    
    new_state = authoring_node(state)
    
    assert len(new_state["user_stories"]) == 1
    assert new_state["user_stories"][0].title == "User Login"
    assert new_state["authoring_complete"] == True


def test_authoring_node_handles_multiple_requirements(mock_llm):
    """Test authoring node handles multiple requirements."""
    state = create_project_state("Test", "Context")
    state["requirements_raw"] = [
        RequirementRaw(id="REQ-001", title="Login", description="Users login", type="Functional", source="User"),
        RequirementRaw(id="REQ-002", title="Logout", description="Users logout", type="Functional", source="User")
    ]
    
    # Mock JSON responses for multiple calls
    mock_llm.invoke.side_effect = [
        Mock(content='```json\n{"title": "User Login", "story_statement": "As a user...", "acceptance_criteria": ["AC1"], "effort": "M"}\n```'),
        Mock(content='```json\n{"title": "User Logout", "story_statement": "As a user...", "acceptance_criteria": ["AC1"], "effort": "S"}\n```')
    ]
    
    new_state = authoring_node(state)
    
    assert len(new_state["user_stories"]) == 2
    assert new_state["authoring_complete"] == True


def test_authoring_node_skips_if_no_requirements(mock_llm):
    """Test authoring node handles empty requirements gracefully."""
    state = create_project_state("Test", "Context")
    state["requirements_raw"] = []
    state["conversation_history"].append({"role": "user", "content": "Generate stories"})
    
    mock_response = Mock()
    mock_response.content = "No requirements found to generate stories."
    mock_llm.invoke.return_value = mock_response
    
    new_state = authoring_node(state)
    
    assert len(new_state["user_stories"]) == 0
    assert new_state["authoring_complete"] == False


def test_authoring_node_doesnt_regenerate_existing_stories(mock_llm):
    """Test authoring node doesn't regenerate if stories already exist."""
    state = create_project_state("Test", "Context")
    state["requirements_raw"] = [
        RequirementRaw(id="REQ-001", title="Login", description="Users login", type="Functional", source="User")
    ]
    state["user_stories"] = [
        UserStory(
            id="STORY-001", requirement_id="REQ-001", title="Existing Story",
            story_statement="As a user...", acceptance_criteria=["AC1"],
            edge_cases=[], definition_of_done=[], effort_estimate="M"
        )
    ]
    
    mock_response = Mock()
    mock_response.content = "Stories already exist."
    mock_llm.invoke.return_value = mock_response
    
    new_state = authoring_node(state)
    
    # Should keep existing stories, not regenerate
    assert len(new_state["user_stories"]) == 1
    assert new_state["user_stories"][0].title == "Existing Story"


# ============================================================================
# QUALITY NODE TESTS
# ============================================================================

def test_quality_node_validates_requirements(mock_llm):
    """Test quality node validates requirements and finds issues."""
    state = create_project_state("Test", "Context")
    state["requirements_raw"] = [
        RequirementRaw(id="REQ-001", title="Fast", description="Be fast", type="Non-Functional", source="User")
    ]
    
    mock_response = Mock()
    mock_response.content = "Quality check complete. Found ambiguous requirements."
    mock_llm.invoke.return_value = mock_response
    
    new_state = quality_node(state)
    
    # "Be fast" should trigger ambiguity
    assert len(new_state["quality_issues"]) > 0
    assert any(issue.category == "Ambiguity" for issue in new_state["quality_issues"])


def test_quality_node_marks_complete_when_clean(mock_llm):
    """Test quality node marks complete when no critical issues."""
    state = create_project_state("Test", "Context")
    state["requirements_raw"] = [
        RequirementRaw(
            id="REQ-001",
            title="User Authentication",
            description="The system shall authenticate users using email and password with bcrypt hashing",
            type="Functional",
            source="User"
        )
    ]
    state["user_stories"] = [
        UserStory(
            id="STORY-001", requirement_id="REQ-001", title="User Login",
            story_statement="As a user, I want to login with email and password so that I can access my account",
            acceptance_criteria=["User can enter email", "System validates password", "User is redirected to dashboard"],
            edge_cases=["Invalid credentials show error message"],
            definition_of_done=["Unit tests pass", "Code reviewed"],
            effort_estimate="M"
        )
    ]
    
    mock_response = Mock()
    mock_response.content = "Quality check complete. No critical issues found."
    mock_llm.invoke.return_value = mock_response
    
    new_state = quality_node(state)
    
    # Good requirement should have minimal or no issues
    assert new_state["quality_complete"] == True


def test_quality_node_handles_user_acknowledging_risks(mock_llm):
    """Test quality node when user acknowledges risks - user can manually resolve issues."""
    state = create_project_state("Test", "Context")
    state["quality_issues"] = [
        QualityIssue(
            id="QA-001",
            location="REQ-001",
            category="Ambiguity",
            severity="Medium",
            description="Term 'fast' is ambiguous",
            recommended_fix="Specify performance requirements",
            status="Identified"
        )
    ]
    
    # User manually marks issues as resolved
    state["quality_issues_resolved"] = True
    state["quality_complete"] = True
    
    # Quality node doesn't re-run validation if already complete
    new_state = quality_node(state)
    
    # State should remain unchanged since already complete
    assert new_state["quality_complete"] == True
    assert new_state["quality_issues_resolved"] == True


# ============================================================================
# PRIORITIZATION NODE TESTS
# ============================================================================

def test_prioritization_node_prioritizes_requirements(mock_llm):
    """Test prioritization node ranks requirements."""
    state = create_project_state("Test", "Context")
    state["requirements_raw"] = [
        RequirementRaw(id="REQ-001", title="Login", description="Users login", type="Functional", source="User"),
        RequirementRaw(id="REQ-002", title="Reports", description="Generate reports", type="Functional", source="User")
    ]
    state["user_preferences"]["prioritization_framework"] = "MoSCoW"
    
    mock_response = Mock()
    mock_response.content = "Prioritization complete using MoSCoW framework."
    mock_llm.invoke.return_value = mock_response
    
    with patch("forge_requirements_builder.nodes.apply_prioritization_framework") as mock_prioritize:
        mock_result = Mock()
        mock_result.ranked_requirements = [
            PrioritizedRequirement(
                rank=1, requirement_id="REQ-001", title="Login",
                priority_level="Must Have", framework_score=95.0,
                phase="Phase 1", dependencies=[], enables=["REQ-002"],
                rationale="Foundation for all features"
            ),
            PrioritizedRequirement(
                rank=2, requirement_id="REQ-002", title="Reports",
                priority_level="Should Have", framework_score=70.0,
                phase="Phase 2", dependencies=["REQ-001"], enables=[],
                rationale="Important but not critical"
            )
        ]
        mock_prioritize.return_value = mock_result
        
        new_state = prioritization_node(state)
        
        assert len(new_state["prioritized_backlog"]) == 2
        assert new_state["prioritized_backlog"][0].rank == 1
        assert new_state["prioritized_backlog"][0].priority_level == "Must Have"
        assert new_state["prioritization_complete"] == True


def test_prioritization_node_uses_selected_framework(mock_llm):
    """Test prioritization node respects user's framework choice."""
    state = create_project_state("Test", "Context")
    state["requirements_raw"] = [
        RequirementRaw(id="REQ-001", title="Login", description="Users login", type="Functional", source="User")
    ]
    state["prioritization_framework"] = "RICE"
    
    mock_response = Mock()
    mock_response.content = "Using RICE framework."
    mock_llm.invoke.return_value = mock_response
    
    with patch("forge_requirements_builder.nodes.apply_prioritization_framework") as mock_prioritize:
        mock_result = Mock()
        mock_result.ranked_requirements = []
        mock_prioritize.return_value = mock_result
        new_state = prioritization_node(state)
        
        # Verify the framework was passed to the tool
        mock_prioritize.assert_called_once()
        call_args = mock_prioritize.call_args[0]
        assert call_args[0] == "RICE"  # First argument is the framework


# ============================================================================
# SYNTHESIS NODE TESTS
# ============================================================================

def test_synthesis_node_generates_deliverable(mock_llm):
    """Test synthesis node generates final markdown document."""
    state = create_project_state("Test Project", "Context")
    state["requirements_raw"] = [
        RequirementRaw(id="REQ-001", title="Login", description="Users login", type="Functional", source="User")
    ]
    state["user_stories"] = [
        UserStory(
            id="STORY-001", requirement_id="REQ-001", title="User Login",
            story_statement="As a user, I want to login", acceptance_criteria=["AC1"],
            edge_cases=[], definition_of_done=[], effort_estimate="M"
        )
    ]
    state["prioritized_backlog"] = [
        PrioritizedRequirement(
            rank=1, requirement_id="REQ-001", title="Login",
            priority_level="Must Have", framework_score=95.0,
            phase="Phase 1", dependencies=[], enables=[],
            rationale="Critical"
        )
    ]
    
    mock_response = Mock()
    mock_response.content = """# Requirements Document
    
## Executive Summary
This document captures the requirements for Test Project.

## Requirements
- REQ-001: Login

## User Stories
- STORY-001: User Login

## Prioritization
- Phase 1: Login (Must Have)
"""
    mock_llm.invoke.return_value = mock_response
    
    new_state = synthesis_node(state)
    
    assert new_state["final_deliverable"] != ""
    assert "# Requirements Document" in new_state["final_deliverable"]
    assert "Test Project" in new_state["final_deliverable"]
    assert new_state["synthesis_complete"] == True
    assert new_state["workflow_phase"] == "complete"


def test_synthesis_node_includes_all_sections(mock_llm):
    """Test synthesis node includes all required sections."""
    state = create_project_state("Test", "Context")
    state["requirements_raw"] = [
        RequirementRaw(id="REQ-001", title="Test", description="Test req", type="Functional", source="User")
    ]
    
    mock_response = Mock()
    mock_response.content = """# Requirements Document

## 1. Executive Summary
Summary

## 2. Project Context
Context

## 3. Functional Requirements
- REQ-001

## 4. Non-Functional Requirements
None

## 5. User Stories
Stories

## 6. Quality Analysis
Clean

## 7. Prioritization
Prioritized

## 8. Assumptions
None

## 9. Risks
None

## 10. Appendix
Additional info
"""
    mock_llm.invoke.return_value = mock_response
    
    new_state = synthesis_node(state)
    
    deliverable = new_state["final_deliverable"]
    assert "Executive Summary" in deliverable
    assert "Project Context" in deliverable
    assert "Functional Requirements" in deliverable
    assert "User Stories" in deliverable
    assert "Prioritization" in deliverable


# ============================================================================
# INTEGRATION TESTS ACROSS NODES
# ============================================================================

def test_full_workflow_simulation(mock_llm):
    """Test simulated flow through all nodes."""
    state = create_project_state("Test", "Context")
    
    # 1. Discovery
    state["conversation_history"].append({"role": "user", "content": "I need login"})
    mock_llm.invoke.return_value = Mock(content="Understood. Discovery complete.")
    state = discovery_node(state)
    
    # Manually add requirement since we're not fully mocking extraction
    state["requirements_raw"].append(
        RequirementRaw(id="REQ-001", title="Login", description="Login", type="Functional", source="User")
    )
    state["discovery_complete"] = True
    
    # 2. Orchestrator routes to Authoring
    state = orchestrator_node(state)
    assert state["workflow_phase"] == "authoring"
    
    # 3. Authoring
    mock_llm.invoke.return_value = Mock(content='```json\n{"title": "Login", "story_statement": "As a user...", "acceptance_criteria": ["AC1"], "effort": "M"}\n```')
    state = authoring_node(state)
    assert len(state["user_stories"]) == 1
    assert state["authoring_complete"] == True
    
    # Orchestrator should route to quality now
    state = orchestrator_node(state)
    assert state["workflow_phase"] == "quality"
    
    # 4. Quality
    state = quality_node(state)
    state["quality_issues_resolved"] = True
    
    # 5. Orchestrator routes to Prioritization
    state = orchestrator_node(state)
    assert state["workflow_phase"] == "prioritization"
    
    # 6. Prioritization
    with patch("forge_requirements_builder.nodes.apply_prioritization_framework") as mock_prioritize:
        mock_result = Mock()
        mock_result.ranked_requirements = [
            PrioritizedRequirement(
                rank=1, requirement_id="REQ-001", title="Login",
                priority_level="Must Have", framework_score=95.0,
                phase="Phase 1", dependencies=[], enables=[],
                rationale="Critical"
            )
        ]
        mock_prioritize.return_value = mock_result
        state = prioritization_node(state)
        assert len(state["prioritized_backlog"]) == 1
    
    # 7. Synthesis
    mock_llm.invoke.return_value = Mock(content="# Requirements\nDoc content")
    state = synthesis_node(state)
    assert state["final_deliverable"] != ""
    assert state["workflow_phase"] == "complete"
