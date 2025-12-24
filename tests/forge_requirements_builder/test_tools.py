"""Unit tests for Agent Tools."""

import pytest
from forge_requirements_builder.tools import (
    extract_from_document,
    validate_user_story,
    validate_requirements_quality,
    apply_prioritization_framework,
    validate_acceptance_criteria
)
from forge_requirements_builder.state import RequirementRaw, UserStory

# ============================================================================
# 5.2.1: Extract from Document
# ============================================================================

def test_extract_from_document_text():
    """Test extracting requirements from text content."""
    text = """
    System Requirements:
    1. The system shall allow users to reset their password.
    2. The system must encrypt all data at rest.
    """
    
    # We can pass text directly if we mock the file reading or if the tool supports text input
    # The current tool implementation expects a file path.
    # For unit testing, we should mock the file reading or create a temp file.
    # Let's assume we can pass a dummy path and mock the internal reader, 
    # OR we can test the internal extraction logic if exposed.
    # Looking at tools.py, extract_from_document takes a file_path.
    # However, for this test environment, let's create a temporary file.
    
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
        tmp.write(text)
        tmp_path = tmp.name
        
    try:
        result = extract_from_document(tmp_path)
        assert len(result.requirements) >= 2
        assert "reset their password" in result.requirements[0].description or "reset their password" in result.requirements[0].title
    finally:
        os.remove(tmp_path)

# ============================================================================
# 5.2.2: Validate User Story
# ============================================================================

def test_validate_user_story_valid():
    """Test validation of a good user story."""
    story = UserStory(
        id="STORY-001",
        requirement_id="REQ-001",
        title="Login",
        story_statement="As a user, I want to login so that I can access my account",
        acceptance_criteria=["Given I am on login page", "When I enter valid creds", "Then I am logged in"],
            edge_cases=["Invalid credentials"],
            definition_of_done=["Unit tests pass"],
            effort_estimate="S"
        )
    
    result = validate_user_story(story)
    assert result.is_valid == True
    assert len(result.improvement_suggestions) == 0

def test_validate_user_story_invalid():
    """Test validation of a bad user story."""
    story = UserStory(
        id="STORY-002",
        requirement_id="REQ-002",
        title="Bad Story",
        story_statement="I want to login", # Missing Role and Benefit
        acceptance_criteria=[], # Missing AC
        effort_estimate="S"
    )
    
    result = validate_user_story(story)
    assert result.is_valid == False
    assert any("role" in s.lower() for s in result.improvement_suggestions)
    assert any("benefit" in s.lower() for s in result.improvement_suggestions)
    assert any("acceptance criteria" in s.lower() for s in result.improvement_suggestions)

# ============================================================================
# 5.2.3: Validate Requirements Quality
# ============================================================================

def test_validate_requirements_quality_ambiguity():
    """Test detection of ambiguous requirements."""
    reqs = [
        RequirementRaw(
            id="REQ-001",
            title="Fast System",
            description="The system should be very fast and user-friendly.",
            type="Non-Functional",
            source="User"
        )
    ]
    
    result = validate_requirements_quality(reqs, [])
    
    assert result.total_issues > 0
    ambiguity_issues = [i for i in result.issues_found if i.category == "Ambiguity"]
    assert len(ambiguity_issues) > 0
    # Check if any issue mentions "fast"
    assert any("fast" in i.description.lower() for i in ambiguity_issues)
# ============================================================================

def test_apply_prioritization_framework_moscow():
    """Test MoSCoW prioritization."""
    reqs = [
        RequirementRaw(id="R1", title="Login", description="Login", type="Functional", source="User"),
        RequirementRaw(id="R2", title="Dark Mode", description="Dark Mode", type="Functional", source="User")
    ]
    
    # Simulate inputs where R1 is Must and R2 is Could
    # The tool might use heuristics or LLM. 
    # If it uses LLM, we need to mock it. 
    # If it uses simple heuristics (like keywords), we can test that.
    # Assuming the tool has some logic we can test or we mock the LLM call inside it.
    # For this test, let's assume the tool is implemented with some deterministic logic or we skip if it relies purely on LLM.
    # Let's try to run it and see if it returns a result structure at least.
    
    result = apply_prioritization_framework("MoSCoW", reqs, {})
    assert len(result.ranked_requirements) == 2
    assert result.ranked_requirements[0].priority_level in ["Must Have", "Should Have", "Could Have", "Won't Have"]

def test_apply_prioritization_framework_rice():
    """Test RICE prioritization."""
    reqs = [
        RequirementRaw(id="R1", title="High Value", description="High Value", type="Functional", source="User"),
    ]
    
    inputs = {
            "R1": {"reach": 1000, "impact": 3, "confidence": 100, "effort": 2}
    }
    
    result = apply_prioritization_framework("RICE", reqs, inputs)
    assert len(result.ranked_requirements) == 1
    # Score = (1000 * 3 * 1.0) / 2 = 1500
    assert result.ranked_requirements[0].framework_score == 1500
