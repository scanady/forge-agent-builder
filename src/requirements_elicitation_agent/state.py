"""
State schema definitions for the Forge Requirements Assistant.

Implements the state models defined in plan.md Section 3 (formerly Section 2).
"""

from typing import TypedDict, List, Dict, Annotated, Optional, Literal
from langgraph.graph.message import add_messages


class Requirement(TypedDict):
    """Individual captured requirement.
    
    Attributes:
        id: Unique identifier (e.g., "REQ-001")
        description: Atomic requirement text
        category: Classification of the requirement
        tags: List of tags like ["CONFLICT", "RISK_ACCEPTED", "NEEDS_REFINEMENT"]
        source: Origin of the requirement (e.g., "User Interview" or "File: doc.pdf")
    """
    id: str
    description: str
    category: Literal["Functional", "Non-Functional", "Constraint", "Technical Constraint"]
    tags: List[str]
    source: str


class TodoItem(TypedDict):
    """Topic tracking for gap analysis.
    
    Attributes:
        topic: The requirement domain (e.g., "Security", "User Roles")
        status: Current coverage status of this topic
    """
    topic: str
    status: Literal["pending", "covered", "skipped"]


class AgentState(TypedDict):
    """Main agent state schema.
    
    Manages conversation flow, domain data, and control state for the
    requirements elicitation process.
    
    Attributes:
        messages: Conversation history with add_messages reducer
        current_phase: Current stage of the elicitation process
        requirements: List of all captured requirements (append-only)
        todo_list: Topics to cover during gap analysis
        clarification_counts: Tracks clarification attempts per topic (max 3)
        pending_file_path: File awaiting user confirmation for analysis
        pending_risk_warning: Risk warning awaiting user response
        user_expertise: Detected user expertise level for adaptive communication
    """
    # Conversation state
    messages: Annotated[List[dict], add_messages]
    current_phase: Literal["init", "elicitation", "analysis_confirm", "gap_analysis", "output"]
    
    # Domain state (append-only per spec)
    requirements: List[Requirement]
    
    # Control state
    todo_list: List[TodoItem]
    clarification_counts: Dict[str, int]  # topic_key -> attempt count (max 3)
    
    # Pending state
    pending_file_path: Optional[str]      # File awaiting confirmation
    pending_risk_warning: Optional[str]   # Risk warning awaiting user response
    pending_paraphrase: Optional[dict]    # Paraphrased requirement awaiting confirmation
    
    # Adaptive communication state
    user_expertise: Optional[Literal["experienced", "exploratory"]]  # Task 3.12
