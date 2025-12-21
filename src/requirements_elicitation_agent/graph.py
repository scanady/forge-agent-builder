"""
Graph orchestration and routing for the Forge Requirements Assistant.

Implements the graph structure defined in plan.md Section 4.
"""

import re
from typing import Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage

from .state import AgentState
from .nodes import (
    initializer,
    interviewer,
    requirement_recorder,
    gap_analyzer,
    doc_reader,
    doc_extractor,
    output_generator
)


def router(state: AgentState) -> Literal["initializer", "doc_reader", "doc_extractor", "interviewer", "requirement_recorder", "output_generator"]:
    """Route incoming messages to appropriate processing node.
    
    Ref: Plan Section 4.1, Persona Directive #17
    Task: 4.1
    
    Routes based on state and message patterns.
    """
    messages = state.get("messages", [])
    current_phase = state.get("current_phase")
    pending_file_path = state.get("pending_file_path")
    
    # Route to initializer if no phase set (first interaction) or no messages
    if not current_phase or not messages:
        return "initializer"
    
    last_message = messages[-1]
    
    # Check for output generation request (Directive #17)
    if isinstance(last_message, HumanMessage):
        content_lower = last_message.content.lower()
        output_patterns = [
            r'^show\s+(me\s+)?(the\s+)?requirements?',  # "show requirements", "show me the requirements"
            r'^give\s+(me\s+)?(the\s+)?requirements?',  # "give me the requirements"
            r'^list\s+(all\s+)?(the\s+)?requirements?', # "list requirements"
            r'^export\s+(the\s+)?requirements?',        # "export requirements"
            r'^generate\s+(the\s+)?requirements?',      # "generate requirements"
            r"what('ve|\s+have)?\s+(you\s+)?(we\s+)?captured",  # "what have we captured"
            r'^review\s+(the\s+)?captured\s+requirements?',     # "review captured requirements"
            r'^show\s+summary',                         # "show summary"
            r'^requirements\s+dump',                    # "requirements dump"
        ]
        if any(re.search(pattern, content_lower) for pattern in output_patterns):
            return "output_generator"
    
    # Route based on current phase
    if current_phase == "init":
        if not messages or len(messages) <= 1:
            return "initializer"
        # User has responded, start elicitation
        if isinstance(last_message, HumanMessage):
            # Check if user uploaded file
            if "uploaded a file:" in last_message.content.lower() or re.search(r'\.(txt|md|pdf|docx)', last_message.content):
                return "doc_reader"
            return "interviewer"
    
    elif current_phase == "analysis_confirm":
        if isinstance(last_message, HumanMessage):
            content_lower = last_message.content.lower()
            if any(word in content_lower for word in ['yes', 'confirm', 'proceed', 'ok', 'sure']):
                return "doc_extractor"
            else:
                # User declined, return to elicitation
                return "interviewer"
    
    elif current_phase == "elicitation":
        if isinstance(last_message, HumanMessage):
            # Check for file upload
            if "uploaded a file:" in last_message.content.lower() or re.search(r'\.(txt|md|pdf|docx)', last_message.content):
                return "doc_reader"
            # User responding to question
            return "requirement_recorder"
        else:  # Last message is AI
            # AI asked question, wait for user response
            return "interviewer"
    
    # Default: continue interview
    return "interviewer"


def recorder_router(state: AgentState) -> Literal["gap_analyzer", END]:
    """Route from recorder to gap analyzer or END.
    
    Ref: Plan Section 3.2 (Interview Flow)
    Task: 4.2
    
    Stops flow if clarification or risk warning emitted.
    """
    messages = state.get("messages", [])
    pending_risk_warning = state.get("pending_risk_warning")
    
    if not messages:
        return END
    
    last_message = messages[-1]
    
    # Check if waiting for clarification or risk response
    if isinstance(last_message, AIMessage):
        content_lower = last_message.content.lower()
        
        # Waiting for clarification
        if any(phrase in content_lower for phrase in [
            "could you be more specific",
            "can you give me a specific",
            "let me try once more"
        ]):
            return END
        
        # Waiting for risk acceptance
        if "is that the intent?" in content_lower or pending_risk_warning:
            return END
        
        # Waiting for paraphrase confirmation
        if "is that right?" in content_lower:
            return END
    
    # Continue to gap analysis
    return "gap_analyzer"


def create_graph() -> StateGraph:
    """Create and compile the main agent graph.
    
    Ref: Plan Sections 3.1, 4.3, 4.4
    Tasks: 4.3, 4.4, 4.5
    
    Returns:
        Compiled StateGraph with MemorySaver checkpointer
    """
    # Create graph
    workflow = StateGraph(AgentState)
    
    # Add nodes (Task 4.3)
    workflow.add_node("initializer", initializer)
    workflow.add_node("interviewer", interviewer)
    workflow.add_node("requirement_recorder", requirement_recorder)
    workflow.add_node("gap_analyzer", gap_analyzer)
    workflow.add_node("doc_reader", doc_reader)
    workflow.add_node("doc_extractor", doc_extractor)
    workflow.add_node("output_generator", output_generator)
    
    # Set conditional entry point
    workflow.set_conditional_entry_point(router)
    
    # Wire up edges (Task 4.4)
    workflow.add_edge("initializer", END)
    workflow.add_edge("interviewer", END)
    workflow.add_conditional_edges(
        "requirement_recorder",
        recorder_router,
        {
            "gap_analyzer": "gap_analyzer",
            END: END
        }
    )
    workflow.add_edge("gap_analyzer", "interviewer")
    workflow.add_edge("doc_reader", END)
    workflow.add_edge("doc_extractor", "gap_analyzer")
    workflow.add_edge("output_generator", END)
    
    # Compile with checkpointer (Task 4.5)
    checkpointer = MemorySaver()
    app = workflow.compile(checkpointer=checkpointer)
    
    return app
