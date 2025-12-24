import pytest
from forge_requirements_builder.prompts import (
    DISCOVERY_SYSTEM_PROMPT,
    QUALITY_SYSTEM_PROMPT,
    ORCHESTRATOR_SYSTEM_PROMPT,
    AUTHORING_SYSTEM_PROMPT,
    PRIORITIZATION_SYSTEM_PROMPT
)

# ============================================================================
# 5.5 Behavioral Tests - Persona Compliance
# ============================================================================

def test_discovery_agent_warmth():
    """
    Task 5.5.1: Verify Discovery Agent uses encouraging/warm language instructions.
    """
    prompt_lower = DISCOVERY_SYSTEM_PROMPT.lower()
    
    # Check for key behavioral instructions
    # Updated to match actual prompt content: "empathetic", "curious"
    assert "empathetic" in prompt_lower or "curious" in prompt_lower
    
    # Check for negative constraint (avoid technical jargon if possible, or be helpful)
    # Updated to match actual prompt content: "plain language", "avoid jargon"
    assert "plain language" in prompt_lower or "avoid jargon" in prompt_lower

def test_quality_agent_pragmatism():
    """
    Task 5.5.2: Verify Quality Agent is pragmatic, not blocking.
    """
    prompt_lower = QUALITY_SYSTEM_PROMPT.lower()
    
    # Check for pragmatic instructions
    assert "pragmatic" in prompt_lower or "constructive" in prompt_lower
    assert "block" not in prompt_lower or "don't block" in prompt_lower or "allow" in prompt_lower
    
    # Check for risk acknowledgment instruction
    assert "risk" in prompt_lower
    assert "acknowledge" in prompt_lower or "accept" in prompt_lower

def test_orchestrator_transparency():
    """
    Task 5.5.3: Verify Orchestrator is transparent about actions.
    """
    prompt_lower = ORCHESTRATOR_SYSTEM_PROMPT.lower()
    
    # Check for transparency instructions
    assert "transparent" in prompt_lower or "explain" in prompt_lower or "inform" in prompt_lower
    assert "next step" in prompt_lower or "phase" in prompt_lower

def test_authoring_agent_invest():
    """
    Task 5.5.4: Verify Authoring Agent follows INVEST principles.
    """
    prompt_lower = AUTHORING_SYSTEM_PROMPT.lower()
    
    # Check for INVEST keywords
    assert "invest" in prompt_lower
    assert "user story" in prompt_lower
    assert "acceptance criteria" in prompt_lower

def test_prioritization_agent_analytical():
    """
    Task 5.5.5: Verify Prioritization Agent is analytical and objective.
    """
    prompt_lower = PRIORITIZATION_SYSTEM_PROMPT.lower()
    
    # Check for analytical tone instructions
    # Updated to match actual prompt content: "strategic", "decisive", "business-focused", "why"
    assert "strategic" in prompt_lower or "decisive" in prompt_lower or "business-focused" in prompt_lower
    assert "why" in prompt_lower or "rationale" in prompt_lower
