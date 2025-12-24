# Implementation Guide: Forge Requirements Builder

**Target:** Python + LangGraph + Streamlit  
**Status:** Pre-Implementation  
**Last Updated:** December 21, 2025

---

## Quick Start

This guide translates the specification into implementation steps.

---

## 1. State Schema (LangGraph)

Create a TypedDict for shared state across all agents:

```python
from typing import TypedDict, Optional, List
from dataclasses import dataclass, field

class RequirementObject(TypedDict):
    id: str
    title: str
    description: str
    type: str  # Functional | Non-Functional | Constraint
    effort_estimate: str  # XS | S | M | L | XL
    risks: str
    category: Optional[str]

class UserStoryObject(TypedDict):
    id: str
    title: str
    story_statement: str
    acceptance_criteria: List[str]
    edge_cases: List[str]
    definition_of_done: List[str]
    effort_estimate: str
    story_points: int
    related_stories: List[str]

class QualityIssueObject(TypedDict):
    id: str
    location: str  # Story/Requirement ID
    type: str  # Ambiguity | Incompleteness | Inconsistency | Untestable
    severity: str  # High | Medium | Low
    issue: str
    proposed_fix: str
    status: str  # Resolved | Deferred | Disputed

class PrioritizedRequirementObject(TypedDict):
    rank: int
    requirement_id: str
    title: str
    priority_level: str
    framework_score: Optional[float]
    phase: str
    dependencies: List[str]
    enables: List[str]
    rationale: str

class ForgeRequirementsState(TypedDict):
    # Project metadata
    project_id: str
    project_name: str
    user_context: str
    
    # Discovery phase
    discovery_complete: bool
    requirements_raw: List[RequirementObject]
    gaps_identified: List[str]
    assumptions_documented: List[str]
    
    # Authoring phase
    user_stories: List[UserStoryObject]
    
    # Quality phase
    quality_issues: List[QualityIssueObject]
    quality_issues_resolved: bool
    requirements_formal: str  # Markdown formatted
    
    # Prioritization phase
    prioritized_backlog: List[PrioritizedRequirementObject]
    prioritization_framework: str  # MoSCoW | RICE | Kano | Value-Effort
    
    # Overall workflow
    workflow_phase: str  # discovery | authoring | quality | prioritization | complete
    conversation_history: List[dict]
    user_preferences: dict
    
    # Final output
    final_deliverable: str  # Complete markdown requirements document
```

---

## 2. LangGraph Node Structure

Create nodes for each agent and routing:

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint import MemorySaver

def create_graph():
    graph = StateGraph(ForgeRequirementsState)
    
    # Add nodes
    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("discovery", discovery_node)
    graph.add_node("authoring", authoring_node)
    graph.add_node("quality", quality_node)
    graph.add_node("prioritization", prioritization_node)
    graph.add_node("synthesize", synthesize_final_deliverable)
    
    # Set entry point
    graph.set_entry_point("orchestrator")
    
    # Add conditional routing
    graph.add_conditional_edges(
        "orchestrator",
        route_next_agent,
        {
            "discovery": "discovery",
            "authoring": "authoring",
            "quality": "quality",
            "prioritization": "prioritization",
            "synthesize": "synthesize",
            "end": END,
        }
    )
    
    # Linear edges for agent completion
    graph.add_edge("discovery", "orchestrator")
    graph.add_edge("authoring", "orchestrator")
    graph.add_edge("quality", "orchestrator")
    graph.add_edge("prioritization", "orchestrator")
    graph.add_edge("synthesize", END)
    
    # Compile with memory
    return graph.compile(checkpointer=MemorySaver())
```

---

## 3. Orchestrator Node Implementation

```python
def orchestrator_node(state: ForgeRequirementsState) -> ForgeRequirementsState:
    """
    Orchestrator logic:
    1. Interpret user intent
    2. Check current state
    3. Decide next agent
    4. Prepare context for next agent
    """
    
    user_message = state["conversation_history"][-1]["content"]
    
    # Detect user intent
    if "start" in user_message.lower():
        next_phase = "discovery"
    elif "story" in user_message.lower() or (
        state["discovery_complete"] and not state["user_stories"]
    ):
        next_phase = "authoring"
    elif "quality" in user_message.lower() or (
        len(state["user_stories"]) > 0 and not state["quality_issues_resolved"]
    ):
        next_phase = "quality"
    elif "prioritize" in user_message.lower():
        next_phase = "prioritization"
    elif state["workflow_phase"] == "prioritization" and state["prioritized_backlog"]:
        next_phase = "synthesize"
    else:
        next_phase = "ask_clarification"
    
    state["workflow_phase"] = next_phase
    
    # Log progress
    state["conversation_history"].append({
        "role": "system",
        "content": f"Moving to {next_phase} phase..."
    })
    
    return state
```

---

## 4. Discovery Agent Node

```python
async def discovery_node(state: ForgeRequirementsState) -> ForgeRequirementsState:
    """
    Discovery agent:
    - Conducts interactive discovery
    - Extracts requirements from documents
    - Identifies gaps
    - Returns structured requirements
    """
    
    discovery_agent = DiscoveryAgent(model="gpt-4o")
    
    result = await discovery_agent.discover(
        user_context=state["user_context"],
        conversation_history=state["conversation_history"],
    )
    
    state["requirements_raw"] = result["requirements_raw"]
    state["gaps_identified"] = result["gaps_identified"]
    state["discovery_complete"] = True
    
    state["conversation_history"].append({
        "role": "assistant",
        "content": result["discovery_document"],
    })
    
    return state
```

---

## 5. User Story Authoring Node

```python
async def authoring_node(state: ForgeRequirementsState) -> ForgeRequirementsState:
    """
    User Story Authoring agent:
    - Transforms requirements into user stories
    - Adds acceptance criteria
    - Documents edge cases
    - Estimates effort
    """
    
    authoring_agent = AuthoringAgent(model="gpt-4o")
    
    result = await authoring_agent.author(
        requirements=state["requirements_raw"],
        user_preferences=state["user_preferences"],
        conversation_history=state["conversation_history"],
    )
    
    state["user_stories"] = result["user_stories"]
    
    state["conversation_history"].append({
        "role": "assistant",
        "content": result["stories_document"],
    })
    
    return state
```

---

## 6. Quality Agent Node

```python
async def quality_node(state: ForgeRequirementsState) -> ForgeRequirementsState:
    """
    Quality agent:
    - Analyzes for ambiguity, completeness, consistency, testability
    - Identifies issues
    - Proposes and applies fixes
    - Generates quality report
    """
    
    quality_agent = QualityAgent(model="gpt-4o")
    
    result = await quality_agent.validate(
        requirements=state["user_stories"],
        check_level="comprehensive",
        auto_fix=state["user_preferences"].get("auto_fix_quality", False),
        user_approvals=extract_recent_approvals(state["conversation_history"]),
    )
    
    state["quality_issues"] = result["quality_issues"]
    state["quality_issues_resolved"] = result["quality_issues_resolved"]
    state["requirements_formal"] = result["requirements_formal"]
    
    state["conversation_history"].append({
        "role": "assistant",
        "content": result["quality_report"],
    })
    
    return state
```

---

## 7. Prioritization Agent Node

```python
async def prioritization_node(state: ForgeRequirementsState) -> ForgeRequirementsState:
    """
    Prioritization agent:
    - Presents prioritization frameworks
    - Scores requirements
    - Identifies dependencies
    - Produces ranked backlog
    """
    
    prioritization_agent = PrioritizationAgent(model="gpt-4o")
    
    result = await prioritization_agent.prioritize(
        requirements=state["requirements_formal"],
        framework=state["user_preferences"].get("framework", "RICE"),
        business_context=extract_business_context(state["conversation_history"]),
        user_overrides=extract_prioritization_overrides(state["conversation_history"]),
    )
    
    state["prioritized_backlog"] = result["prioritized_backlog"]
    state["prioritization_framework"] = result["framework_used"]
    
    state["conversation_history"].append({
        "role": "assistant",
        "content": result["prioritization_report"],
    })
    
    return state
```

---

## 8. Synthesis Node

```python
def synthesize_final_deliverable(state: ForgeRequirementsState) -> ForgeRequirementsState:
    """
    Combine all agent outputs into final requirements document:
    - Project overview
    - User scenarios
    - Requirements list
    - User stories
    - Functional requirements
    - Non-functional requirements
    - Data model
    - Testing strategy
    - Success criteria
    - Appendices
    """
    
    synthesizer = DeliverableSynthesizer()
    
    final_doc = synthesizer.create(
        project_name=state["project_name"],
        user_context=state["user_context"],
        requirements_raw=state["requirements_raw"],
        user_stories=state["user_stories"],
        quality_report=state.get("quality_report", ""),
        prioritized_backlog=state["prioritized_backlog"],
        prioritization_framework=state["prioritization_framework"],
        assumptions=state["assumptions_documented"],
        gaps=state["gaps_identified"],
    )
    
    state["final_deliverable"] = final_doc
    
    state["conversation_history"].append({
        "role": "assistant",
        "content": f"✓ Your requirements are complete!\n\n{final_doc[:500]}...\n\nFull document is ready to download or share."
    })
    
    return state
```

---

## 9. Streamlit UI Structure

```python
import streamlit as st
from langgraph import create_graph

# Initialize session state
if "graph" not in st.session_state:
    st.session_state.graph = create_graph()

if "state" not in st.session_state:
    st.session_state.state = init_empty_state()

# UI Layout
st.set_page_config(page_title="Forge Requirements Builder", layout="wide")

st.title("📋 Forge Requirements Builder")

# Left sidebar: Project info & progress
with st.sidebar:
    st.subheader("Project")
    project_name = st.text_input("Project Name", state["project_name"])
    
    st.subheader("Progress")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Phase", state["workflow_phase"])
    with col2:
        st.metric("Requirements", len(state["requirements_raw"]))
    
    st.progress(
        calculate_progress(state),
        text=f"{calculate_progress(state):.0%} Complete"
    )

# Main area: Conversation
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Requirements Assistant")
    
    # Display conversation history
    for msg in state["conversation_history"]:
        if msg["role"] == "user":
            st.write(f"**You:** {msg['content']}")
        else:
            st.write(f"**Assistant:** {msg['content']}")
    
    # Input for next message
    user_input = st.text_input("You:", key="user_input", placeholder="Tell me about your project...")
    
    if user_input:
        # Add to history
        state["conversation_history"].append({
            "role": "user",
            "content": user_input
        })
        
        # Run graph
        result_state = st.session_state.graph.invoke(state)
        st.session_state.state = result_state
        st.rerun()

with col2:
    st.subheader("Current State")
    st.json({
        "phase": state["workflow_phase"],
        "discovery_complete": state["discovery_complete"],
        "stories_count": len(state["user_stories"]),
        "quality_resolved": state["quality_issues_resolved"],
        "has_backlog": bool(state["prioritized_backlog"]),
    })
    
    if state["final_deliverable"]:
        st.download_button(
            label="📥 Download Requirements",
            data=state["final_deliverable"],
            file_name=f"{state['project_name']}_requirements.md",
            mime="text/markdown"
        )
```

---

## 10. Deployment

### Option A: Streamlit App
```bash
streamlit run src/forge_requirements_builder/app.py
```

### Option B: MCP Server
```python
# mcp_server.py
from mcp.server import Server

server = Server("forge-requirements-builder")

@server.tool()
def create_requirements_project(project_name: str, context: str) -> dict:
    """Start a new requirements project"""
    graph = create_graph()
    return graph.invoke({"project_name": project_name, "user_context": context})

@server.tool()
def continue_requirements_conversation(project_id: str, message: str) -> dict:
    """Continue conversation in a project"""
    # Load project state from storage
    # Run graph with new message
    # Save state back
    pass

if __name__ == "__main__":
    server.start()
```

---

## 11. Testing Strategy

### Unit Tests
- Test each agent node in isolation
- Verify state transitions
- Test schema validation

### Integration Tests
- Test end-to-end workflows
- Verify agent handoffs
- Validate state preservation

### Gold Dataset Tests
- Happy path scenario (discovery → authoring → quality → prioritization)
- User interruption scenario (skip to prioritization)
- Error scenario (conflicting requirements)
- Incomplete scope scenario (gaps identified and filled)

---

## 12. Development Checklist

### Foundation (Week 1-2)
- [ ] Create LangGraph state schema
- [ ] Implement Orchestrator routing logic
- [ ] Set up Streamlit UI shell
- [ ] Create mock agents for testing

### Discovery Agent (Week 2)
- [ ] Implement discovery conversation logic
- [ ] Add document parsing capability
- [ ] Generate discovery document output
- [ ] Test with sample projects

### Authoring Agent (Week 2-3)
- [ ] Implement story generation from requirements
- [ ] Add acceptance criteria generation
- [ ] Add edge case identification
- [ ] Implement effort estimation
- [ ] Test with sample requirements

### Quality Agent (Week 3-4)
- [ ] Implement ambiguity detection
- [ ] Implement completeness checking
- [ ] Implement consistency detection
- [ ] Implement testability validation
- [ ] Add issue fixing workflow
- [ ] Generate quality report

### Prioritization Agent (Week 4-5)
- [ ] Implement RICE framework
- [ ] Implement MoSCoW framework
- [ ] Add dependency detection
- [ ] Generate phased backlog
- [ ] Test prioritization accuracy

### Integration & Polish (Week 5-6)
- [ ] End-to-end testing
- [ ] Performance optimization
- [ ] State persistence (save/resume)
- [ ] Final deliverable synthesis
- [ ] UI polish and UX refinement

---

## 13. Error Handling Strategy

| Error | Recovery |
|-------|----------|
| Agent timeout | Retry once; if fails, offer skip/escalate |
| Invalid user input | Ask clarification; don't assume |
| Quality issue unresolved | Escalate to user; don't force |
| State corruption | Log error; offer to start new project |
| LLM API failure | Retry with exponential backoff; escalate |

---

## 14. Performance Considerations

- Cache agent prompts to reduce API calls
- Stream long outputs to Streamlit to improve perceived speed
- Batch quality checks rather than checking one-by-one
- Use function calling for structured outputs (not parsing)
- Implement request caching for identical queries

---

## 15. Security & Privacy

- No PII in state logs
- Optionally encrypt project state at rest
- Rate limit API to prevent abuse
- Validate user input (no injection attacks)
- Audit trail for all quality fixes and prioritization decisions

---

**Ready for implementation!**

Questions? Refer to specific agent specs for detailed operational instructions.
