"""State Schema for Forge Requirements Builder

Defines all Pydantic models and TypedDict for shared state management across agents.
"""

from datetime import datetime
from typing import TypedDict, Optional, List
from pydantic import BaseModel, Field


# ============================================================================
# Domain Models (Pydantic BaseModel)
# ============================================================================

class RequirementRaw(BaseModel):
    """Raw requirement captured during discovery phase."""
    
    id: str = Field(..., description="Unique requirement identifier (e.g., REQ-001)")
    title: str = Field(..., description="Concise requirement title")
    description: str = Field(..., description="Full requirement description from user")
    type: str = Field(..., description="Functional | Non-Functional | Constraint | Assumption | Risk")
    source: str = Field(..., description="Where this came from (discovery session, document, etc.)")
    tagged: Optional[List[str]] = Field(default=None, description="User-applied tags")
    needs_refinement: bool = Field(default=False, description="Marked [NEEDS_REFINEMENT] during clarification")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "REQ-001",
                "title": "User authentication",
                "description": "System must support secure user login with email and password",
                "type": "Functional",
                "source": "discovery_session",
                "tagged": ["security", "auth"],
                "needs_refinement": False
            }
        }


class UserStory(BaseModel):
    """User story with acceptance criteria and definition of done."""
    
    id: str = Field(..., description="Story ID (e.g., STORY-001)")
    requirement_id: str = Field(..., description="Related requirement ID")
    title: str = Field(..., description="Story title")
    story_statement: str = Field(..., description="As a [role], I want [feature] so that [benefit]")
    acceptance_criteria: List[str] = Field(default_factory=list, description="Testable acceptance criteria")
    edge_cases: List[str] = Field(default_factory=list, description="Edge cases and error scenarios")
    definition_of_done: List[str] = Field(default_factory=list, description="DoD checklist items")
    effort_estimate: str = Field(..., description="XS | S | M | L | XL")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "STORY-001",
                "requirement_id": "REQ-001",
                "title": "User Login",
                "story_statement": "As a user, I want to log in with email and password so that I can access my account",
                "acceptance_criteria": [
                    "User can enter email and password",
                    "System validates credentials",
                    "User is redirected to dashboard on success"
                ],
                "edge_cases": [
                    "Invalid credentials show error message",
                    "Account locked after 3 failed attempts"
                ],
                "definition_of_done": [
                    "Unit tests pass",
                    "Code reviewed",
                    "Security audit completed"
                ],
                "effort_estimate": "M"
            }
        }


class QualityIssue(BaseModel):
    """Quality issue identified during validation."""
    
    id: str = Field(..., description="Issue ID (e.g., QA-001)")
    location: str = Field(..., description="Requirement/Story ID this affects")
    category: str = Field(..., description="Ambiguity | Incompleteness | Inconsistency | Untestable")
    severity: str = Field(..., description="Critical | High | Medium | Low")
    description: str = Field(..., description="What the issue is")
    recommended_fix: str = Field(..., description="How to fix it")
    status: str = Field(..., description="Identified | Proposed | Resolved | Acknowledged | Deferred")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "QA-001",
                "location": "REQ-001",
                "category": "Ambiguity",
                "severity": "High",
                "description": "Term 'secure' is not defined - what security standard?",
                "recommended_fix": "Specify OAuth 2.0 or define security requirements explicitly",
                "status": "Identified"
            }
        }


class AcknowledgedRisk(BaseModel):
    """Risk that user acknowledged but chose not to fix."""
    
    id: str = Field(..., description="Risk ID (e.g., RISK-001)")
    issue_id: str = Field(..., description="Original QualityIssue ID")
    title: str = Field(..., description="Risk title")
    description: str = Field(..., description="What the risk is and why user accepted it")
    mitigation: Optional[str] = Field(default=None, description="How to mitigate if needed")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "RISK-001",
                "issue_id": "QA-001",
                "title": "Vague security requirement",
                "description": "User acknowledges 'secure' is ambiguous but will clarify in implementation phase",
                "mitigation": "Document security standards in technical design document"
            }
        }


class PrioritizedRequirement(BaseModel):
    """Requirement with prioritization metadata."""
    
    rank: int = Field(..., description="Overall priority rank (1 = highest)")
    requirement_id: str = Field(..., description="Requirement ID")
    title: str = Field(..., description="Requirement title")
    priority_level: str = Field(..., description="Must Have | Should Have | Could Have | Won't Have")
    framework_score: Optional[float] = Field(default=None, description="RICE, MoSCoW, Kano score")
    phase: str = Field(..., description="Phase 1 | Phase 2 | Backlog | Future")
    dependencies: List[str] = Field(default_factory=list, description="Prerequisites (requirement IDs)")
    enables: List[str] = Field(default_factory=list, description="Unlocks (other requirement IDs)")
    rationale: str = Field(..., description="Why ranked here")

    class Config:
        json_schema_extra = {
            "example": {
                "rank": 1,
                "requirement_id": "REQ-001",
                "title": "User authentication",
                "priority_level": "Must Have",
                "framework_score": 85.5,
                "phase": "Phase 1",
                "dependencies": [],
                "enables": ["REQ-002", "REQ-003"],
                "rationale": "Foundation for all user-specific features; high reach and impact"
            }
        }


# ============================================================================
# Shared State (TypedDict for LangGraph)
# ============================================================================

class ForgeRequirementsState(TypedDict):
    """Shared state maintained across all agents in the workflow."""
    
    # Project metadata
    project_id: str
    project_name: str
    user_context: str
    created_at: datetime
    last_updated: datetime
    
    # Discovery phase state
    discovery_complete: bool
    discovery_gap_topics: List[str]  # Topics explored during discovery
    requirements_raw: List[RequirementRaw]
    
    # Authoring phase state
    authoring_complete: bool
    user_stories: List[UserStory]
    
    # Quality phase state
    quality_complete: bool
    quality_issues: List[QualityIssue]
    quality_issues_resolved: bool
    acknowledged_risks: List[AcknowledgedRisk]
    requirements_formal: str  # Markdown formatted after quality validation
    
    # Prioritization phase state
    prioritization_complete: bool
    prioritization_framework: str  # MoSCoW | RICE | Kano | Value-Effort
    prioritized_backlog: List[PrioritizedRequirement]
    
    # Orchestration state
    workflow_phase: str  # discovery | authoring | quality | prioritization | synthesis | complete
    current_agent: Optional[str]  # Which agent is currently executing
    conversation_history: List[dict]  # All messages for context
    user_preferences: dict  # Prioritization framework choice, output format, etc.
    
    # Final deliverable
    final_deliverable: str  # Complete 10-section markdown requirements document
    synthesis_complete: bool


# ============================================================================
# State Management Functions
# ============================================================================

def create_project_state(
    project_name: str,
    user_context: str,
    project_id: Optional[str] = None
) -> ForgeRequirementsState:
    """Initialize a new project state with default values.
    
    Args:
        project_name: Name of the requirements project
        user_context: Initial project description/context from user
        project_id: Optional custom project ID (auto-generated if not provided)
        
    Returns:
        Initialized ForgeRequirementsState with all fields
    """
    import uuid
    
    if project_id is None:
        project_id = f"PRJ-{uuid.uuid4().hex[:8].upper()}"
    
    return ForgeRequirementsState(
        # Project metadata
        project_id=project_id,
        project_name=project_name,
        user_context=user_context,
        created_at=datetime.now(),
        last_updated=datetime.now(),
        
        # Discovery phase
        discovery_complete=False,
        discovery_gap_topics=[],
        requirements_raw=[],
        
        # Authoring phase
        authoring_complete=False,
        user_stories=[],
        
        # Quality phase
        quality_complete=False,
        quality_issues=[],
        quality_issues_resolved=False,
        acknowledged_risks=[],
        requirements_formal="",
        
        # Prioritization phase
        prioritization_complete=False,
        prioritization_framework="",
        prioritized_backlog=[],
        
        # Orchestration
        workflow_phase="discovery",
        current_agent="orchestrator",
        conversation_history=[],
        user_preferences={},
        
        # Final deliverable
        final_deliverable="",
        synthesis_complete=False,
    )


def serialize_state(state: ForgeRequirementsState) -> dict:
    """Serialize state to JSON-compatible dict for persistence.
    
    Args:
        state: Current ForgeRequirementsState
        
    Returns:
        JSON-serializable dict
    """
    import json
    
    def convert_value(val):
        """Convert Pydantic models and datetime objects to serializable format."""
        if isinstance(val, BaseModel):
            return val.model_dump()
        elif isinstance(val, datetime):
            return val.isoformat()
        elif isinstance(val, list):
            return [convert_value(item) for item in val]
        elif isinstance(val, dict):
            return {k: convert_value(v) for k, v in val.items()}
        return val
    
    return {key: convert_value(value) for key, value in state.items()}


def deserialize_state(data: dict) -> ForgeRequirementsState:
    """Deserialize JSON dict back to ForgeRequirementsState.
    
    Args:
        data: JSON-compatible dict from serialize_state
        
    Returns:
        Reconstructed ForgeRequirementsState
    """
    from datetime import datetime
    
    # Convert string datetime back to datetime object
    if isinstance(data.get("created_at"), str):
        data["created_at"] = datetime.fromisoformat(data["created_at"])
    
    if isinstance(data.get("last_updated"), str):
        data["last_updated"] = datetime.fromisoformat(data["last_updated"])
    elif "last_updated" not in data:
        # Backwards compatibility: use created_at if last_updated doesn't exist
        data["last_updated"] = data.get("created_at", datetime.now())
    
    # Convert lists of dicts back to Pydantic models
    if "requirements_raw" in data:
        data["requirements_raw"] = [
            RequirementRaw(**req) if isinstance(req, dict) else req
            for req in data["requirements_raw"]
        ]
    
    if "user_stories" in data:
        data["user_stories"] = [
            UserStory(**story) if isinstance(story, dict) else story
            for story in data["user_stories"]
        ]
    
    if "quality_issues" in data:
        data["quality_issues"] = [
            QualityIssue(**issue) if isinstance(issue, dict) else issue
            for issue in data["quality_issues"]
        ]
    
    if "acknowledged_risks" in data:
        data["acknowledged_risks"] = [
            AcknowledgedRisk(**risk) if isinstance(risk, dict) else risk
            for risk in data["acknowledged_risks"]
        ]
    
    if "prioritized_backlog" in data:
        data["prioritized_backlog"] = [
            PrioritizedRequirement(**req) if isinstance(req, dict) else req
            for req in data["prioritized_backlog"]
        ]
    
    return ForgeRequirementsState(**data)
