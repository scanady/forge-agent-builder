# Implementation Plan: Forge Requirements Builder

**Version:** 1.0.0  
**Status:** Ready for Development  
**Date:** December 21, 2025  
**Target Technology:** Python 3.10+ | LangGraph | Pydantic | OpenAI | Streamlit  

---

## Executive Summary

The Forge Requirements Builder is a **5-agent orchestrated network** that guides users through the complete requirements lifecycle (Discovery → Authoring → Quality → Prioritization → Synthesis). This plan translates the specification into implementable components with specific code patterns, state management, and deployment guidance.

**Implementation Complexity:** Moderate to High  
**Recommended Framework:** LangGraph (stateful workflows, conditional routing, human-in-the-loop)  
**Estimated Development:** 6-8 weeks for MVP, 10-12 weeks for full feature parity  

---

## 1. Tech Stack Selection & Justification

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Orchestration** | LangGraph | Complex stateful workflow with 5 agents, conditional routing, human interruption points |
| **LLM Provider** | OpenAI (GPT-4o) | Strong reasoning for requirements analysis, structured output support, context retention |
| **Language** | Python 3.10+ | Type hints, async support, LangGraph native support, modern features |
| **State Validation** | Pydantic v2 | TypedDict-based state schema, tool parameter validation, structured outputs |
| **Frontend** | Streamlit | Rapid prototyping, file uploads (docs for extraction), real-time chat interface |
| **Backend** | FastAPI (optional) | REST API for programmatic access, deployment flexibility |
| **Testing** | Pytest | Unit tests, integration tests, async test support |
| **MCP Integration** | Model Context Protocol | Expose agents as reusable tools for other applications |
| **Configuration** | python-dotenv | Environment variables for API keys, model selection, deployment mode |

### Why LangGraph for This Project?

✅ **Stateful Workflows** — Maintains shared state across 5 agents with explicit field mutations  
✅ **Conditional Routing** — Orchestrator makes routing decisions based on detected state  
✅ **Human-in-the-Loop** — Users can interrupt, request refinements, approve phase transitions  
✅ **Error Recovery** — Explicit error handling with retry/fallback patterns  
✅ **Testability** — Clear node boundaries enable unit and integration testing  

### Alternative Considered: PydanticAI

PydanticAI would work for simpler sequential workflows but lacks:
- Explicit state mutation tracking (harder to debug handoffs)
- Built-in human interruption points
- Native visualization and monitoring

---

## 2. State Schema Design

### 2.1 Core State Structure (Pydantic TypedDict)

```python
from typing import TypedDict, Optional, List
from datetime import datetime
from pydantic import Field, BaseModel

# Core domain objects

class RequirementRaw(BaseModel):
    id: str = Field(..., description="Unique requirement identifier (e.g., REQ-001)")
    title: str = Field(..., description="Concise requirement title")
    description: str = Field(..., description="Full requirement description from user")
    type: str = Field(..., description="Functional | Non-Functional | Constraint | Assumption | Risk")
    source: str = Field(..., description="Where this came from (discovery session, document, etc.)")
    tagged: Optional[List[str]] = Field(default=None, description="User-applied tags")
    needs_refinement: bool = Field(default=False, description="Marked [NEEDS_REFINEMENT] during clarification")

class UserStory(BaseModel):
    id: str = Field(..., description="Story ID (e.g., STORY-001)")
    requirement_id: str = Field(..., description="Related requirement ID")
    title: str = Field(..., description="Story title")
    story_statement: str = Field(..., description="As a [role], I want [feature] so that [benefit]")
    acceptance_criteria: List[str] = Field(default_factory=list, description="Testable acceptance criteria")
    edge_cases: List[str] = Field(default_factory=list, description="Edge cases and error scenarios")
    definition_of_done: List[str] = Field(default_factory=list, description="DoD checklist items")
    effort_estimate: str = Field(..., description="XS | S | M | L | XL")

class QualityIssue(BaseModel):
    id: str = Field(..., description="Issue ID (e.g., QA-001)")
    location: str = Field(..., description="Requirement/Story ID this affects")
    category: str = Field(..., description="Ambiguity | Incompleteness | Inconsistency | Untestable")
    severity: str = Field(..., description="Critical | High | Medium | Low")
    description: str = Field(..., description="What the issue is")
    recommended_fix: str = Field(..., description="How to fix it")
    status: str = Field(..., description="Identified | Proposed | Resolved | Acknowledged | Deferred")

class AcknowledgedRisk(BaseModel):
    id: str = Field(..., description="Risk ID (e.g., RISK-001)")
    issue_id: str = Field(..., description="Original QualityIssue ID")
    title: str = Field(..., description="Risk title")
    description: str = Field(..., description="What the risk is and why user accepted it")
    mitigation: Optional[str] = Field(default=None, description="How to mitigate if needed")

class PrioritizedRequirement(BaseModel):
    rank: int = Field(..., description="Overall priority rank (1 = highest)")
    requirement_id: str = Field(..., description="Requirement ID")
    title: str = Field(..., description="Requirement title")
    priority_level: str = Field(..., description="Must Have | Should Have | Could Have | Won't Have")
    framework_score: Optional[float] = Field(default=None, description="RICE, MoSCoW, Kano score")
    phase: str = Field(..., description="Phase 1 | Phase 2 | Backlog | Future")
    dependencies: List[str] = Field(default_factory=list, description="Prerequisites (requirement IDs)")
    enables: List[str] = Field(default_factory=list, description="Unlocks (other requirement IDs)")
    rationale: str = Field(..., description="Why ranked here")

# Shared workflow state

class ForgeRequirementsState(TypedDict):
    # Project metadata
    project_id: str
    project_name: str
    user_context: str
    created_at: datetime
    
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
```

### 2.2 State Mutation Rules

**Orchestrator can mutate:**
- `workflow_phase`, `current_agent`, `user_preferences`, `conversation_history`
- Initialize all empty lists/dicts

**Discovery Agent can mutate:**
- `requirements_raw` (append only)
- `discovery_gap_topics` (track what was explored)
- `discovery_complete` (set to True when done)

**Authoring Agent can mutate:**
- `user_stories` (append, user manages deletion externally)
- `authoring_complete`

**Quality Agent can mutate:**
- `quality_issues` (append)
- `quality_issues_resolved` (when user approves/acknowledges all)
- `acknowledged_risks` (track user-accepted issues)
- `requirements_formal` (formatted version after validation)
- `quality_complete`

**Prioritization Agent can mutate:**
- `prioritized_backlog` (set complete ranked list)
- `prioritization_framework` (record which was used)
- `prioritization_complete`

**Synthesis Node can mutate:**
- `final_deliverable` (assembled 10-section markdown)
- `synthesis_complete`

---

## 3. Architecture & Data Flow

### 3.1 LangGraph Network Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                     FORGE REQUIREMENTS BUILDER                  │
│                         LangGraph Network                        │
└─────────────────────────────────────────────────────────────────┘

    START
      │
      ├──→ [Orchestrator] (Smart Phase Detection)
      │    ├─ Detect content type (raw ideas / requirements / stories)
      │    ├─ Suggest starting phase
      │    └─ Initialize shared state
      │
      ├─→ IF raw_ideas: [Discovery Agent] ──────────┐
      │   ├─ Elicit requirements via Q&A            │
      │   ├─ Analyze uploaded documents             │
      │   └─ Return: requirements_raw               │
      │                                              │
      ├─→ [User Checkpoint 1] ←──────────────────────┤
      │   "Ready to move to User Story Authoring?"   │
      │                                              │
      ├─→ [Authoring Agent] ─────────────────────────┤
      │   ├─ Transform requirements → user stories   │
      │   ├─ Add acceptance criteria & edge cases    │
      │   └─ Return: user_stories                   │
      │                                              │
      ├─→ [User Checkpoint 2] ←──────────────────────┤
      │   "Review stories. Ready for Quality Check?" │
      │                                              │
      ├─→ [Quality Agent] ────────────────────────────┤
      │   ├─ Validate 4 dimensions (ambiguity, etc)  │
      │   ├─ Surface issues & allow risk acknowledgment
      │   ├─ Return: quality_issues, acknowledged_risks
      │   └─ Pragmatic gate: user decides "good enough"
      │                                              │
      ├─→ [User Checkpoint 3] ←──────────────────────┤
      │   "Ready to prioritize?" [or request refinements]
      │                                              │
      ├─→ [Prioritization Agent] ─────────────────────┤
      │   ├─ Recommend prioritization framework      │
      │   ├─ Score all requirements                  │
      │   ├─ Identify dependencies & phases          │
      │   └─ Return: prioritized_backlog             │
      │                                              │
      ├─→ [User Checkpoint 4] ←──────────────────────┤
      │   "Ready to synthesize final deliverable?"   │
      │                                              │
      └─→ [Synthesis Node] ────────────────────────────┤
          ├─ Aggregate all phase outputs              │
          ├─ Assemble 10-section markdown document    │
          ├─ Cross-reference stories → requirements   │
          └─ Return: final_deliverable                │
                                                      │
                                          END ←───────┘
```

### 3.2 Routing Decision Logic

```python
def route_orchestrator(state: ForgeRequirementsState) -> str:
    """Orchestrator routing: which agent or checkpoint next?"""
    
    user_request = state["conversation_history"][-1]["content"]
    current_phase = state["workflow_phase"]
    
    # Smart detection for first invocation
    if current_phase == "init":
        content_type = detect_content_type(user_request)
        if content_type == "user_stories":
            return "quality"  # Skip to quality
        elif content_type == "requirements":
            return "authoring"  # Skip to authoring
        else:
            return "discovery"  # Default to discovery
    
    # Explicit user requests
    if "skip" in user_request.lower():
        target = extract_phase(user_request)
        return request_confirmation(target)
    
    # Phase completion routing
    if current_phase == "discovery" and state["discovery_complete"]:
        return "checkpoint_1"
    elif current_phase == "authoring" and state["authoring_complete"]:
        return "checkpoint_2"
    elif current_phase == "quality" and state["quality_complete"]:
        return "checkpoint_3"
    elif current_phase == "prioritization" and state["prioritization_complete"]:
        return "checkpoint_4"
    elif current_phase == "synthesis" and state["synthesis_complete"]:
        return "end"
    
    # Fallback
    return "ask_clarification"
```

---

## 4. Node Specifications

### 4.1 Orchestrator Node

**Role:** Project Manager & Workflow Router

**Inputs:**
- `user_request` (latest message)
- `workflow_phase` (current state)
- `requirements_raw`, `user_stories`, `quality_issues`, `prioritized_backlog` (phase outputs)

**Logic:**
1. Parse user intent (explicit request or inferred from state)
2. Detect content type (if first invocation)
3. Decide next routing (which agent or checkpoint)
4. Maintain conversation history and project context
5. Format progress updates for user

**Output:**
- Updated `workflow_phase`
- Updated `conversation_history`
- Routing decision to next agent/checkpoint

**Example System Prompt:**
```
You are the Requirements Project Manager. Your role is to guide the user 
through requirements discovery, authoring, validation, and prioritization.

Current project state:
- Phase: {workflow_phase}
- Requirements captured: {len(requirements_raw)}
- Stories authored: {len(user_stories)}
- Quality issues: {len(quality_issues)}

Based on the user's request and current state, decide the next action:
1. Proceed to next phase with confirmation
2. Refine current phase
3. Skip phases if user approves
4. Synthesize final deliverable

Always provide explicit progress updates: "✓ Discovery complete. 47 requirements 
captured. Ready to move to User Story Authoring?"

Use role-based identity: "As your project manager..." (never name-based)
```

---

### 4.2 Discovery Agent Node

**Role:** Requirements Analyst & Interviewer

**Inputs:**
- `user_context` (initial project description)
- `requirements_raw` (existing requirements if appending)
- `discovery_gap_topics` (what's been explored)

**Logic:**
1. Ask open-ended questions to elicit requirements
2. Proactively surface overlooked areas (security, performance, edge cases, integrations)
3. Capture ambiguities and conflicts
4. Classify requirements by type
5. Ask for confirmation of understanding

**Output:**
- Append to `requirements_raw`
- Update `discovery_gap_topics`
- Set `discovery_complete` = True when ready

**Example System Prompt:**
```
You are an Expert Requirements Analyst conducting interactive discovery.

Your goal is to elicit comprehensive requirements through conversation. Start broad 
("Tell me about your business problem..."), then drill into specifics.

Key behaviors:
- Proactively surface overlooked areas (security, performance, compliance, edge cases)
- Ask "why" and "what if" to uncover hidden needs
- Validate understanding: "So if I'm hearing correctly..."
- Summarize frequently to confirm accuracy
- Use layered questioning: broad → specific
- Tag requirements by type (Functional, Non-Functional, Constraint, Assumption, Risk)
- For conflicts: "I'm hearing both X and Y. Which is more important?"
- For ambiguity: Ask up to 3 times to clarify; if still vague, mark [NEEDS_REFINEMENT]

Tone: Warm, curious, respectful. Use role-based identity: "As your analyst..."
```

---

### 4.3 Authoring Agent Node

**Role:** Technical Writer & Story Strategist

**Inputs:**
- `requirements_raw` (raw requirements to structure)
- `user_stories` (existing stories if appending)

**Logic:**
1. Transform each requirement into "As a [role], I want [feature] so that [benefit]"
2. Develop 3-5 acceptance criteria per story (Given-When-Then format)
3. Identify and document edge cases (2+ per story)
4. Define Definition of Done
5. Estimate effort (XS-XL sizing)
6. Map stories back to source requirements

**Output:**
- Append to `user_stories`
- Set `authoring_complete` = True

**Example System Prompt:**
```
You are a Technical Writer specializing in user story authoring.

For each requirement provided, you will:
1. Create a user story: "As a [role], I want [feature] so that [benefit]"
2. Write 3-5 specific, testable acceptance criteria
3. Brainstorm edge cases and error scenarios
4. Define Definition of Done (code, tests, docs, review, etc.)
5. Estimate effort using t-shirt sizing (XS/S/M/L/XL)

Format:
**Story:** [title]
**Statement:** As a [role], I want [feature] so that [benefit]
**Acceptance Criteria:**
- Given [context], when [action], then [result]
**Edge Cases:**
- [edge case 1]: How to handle?
- [edge case 2]: How to handle?
**Definition of Done:**
- [ ] Code complete
- [ ] Tests written and passing
- [ ] PR reviewed and approved
**Effort:** [XS/S/M/L/XL]

Questions to ask users:
- Who is the user for this feature?
- What's the business value?
- What could go wrong?
- What's the success condition?

Tone: Methodical, collaborative. Use role-based identity.
```

---

### 4.4 Quality Agent Node

**Role:** Quality Engineer & Issue Resolution Partner

**Inputs:**
- `user_stories` (stories to validate)
- `requirements_formal` (formal requirements if previously validated)

**Logic:**
1. Validate 4 dimensions:
   - **Ambiguity:** Are statements clear and unambiguous?
   - **Completeness:** Are all major areas covered?
   - **Consistency:** Do requirements conflict?
   - **Testability:** Can each requirement be objectively verified?
2. Surface issues diplomatically
3. Offer resolution options
4. Allow user to acknowledge risks (pragmatic approach)
5. Track acknowledged risks separately

**Output:**
- Append to `quality_issues`
- Append to `acknowledged_risks` (for user-accepted issues)
- Set `requirements_formal` (validated, formatted markdown)
- Set `quality_complete` = True

**Example System Prompt:**
```
You are a Quality Engineer validating requirements across 4 dimensions:
1. Ambiguity: Are statements clear?
2. Completeness: Are major areas covered?
3. Consistency: Do requirements contradict?
4. Testability: Can each be objectively verified?

For each issue found:
- Describe the problem diplomatically ("I'm noticing an opportunity to clarify...")
- Explain the risk if not addressed
- Offer 2-3 resolution options
- Allow user to choose: resolve now, defer, or acknowledge risk

Format issues as:
**Category:** [Ambiguity | Completeness | Inconsistency | Untestability]
**Severity:** [Critical | High | Medium | Low]
**Issue:** [What's wrong]
**Risk:** [Impact if not fixed]
**Options:**
1. [Resolution option 1]
2. [Resolution option 2]

Mark risk-accepted issues with [RISK_ACCEPTED] tag in final deliverable.

Pragmatic quality approach: User declares "good enough" and proceeds. You track 
risks separately for visibility.

Tone: Constructive, not judgmental. Use role-based identity.
```

---

### 4.5 Prioritization Agent Node

**Role:** Product Strategist & Ranking Analyst

**Inputs:**
- `requirements_formal` (validated requirements)
- `user_preferences` (prioritization framework preference)

**Logic:**
1. Recommend prioritization framework based on project context:
   - **RICE** (Reach, Impact, Confidence, Effort) for product roadmaps
   - **MoSCoW** (Must, Should, Could, Won't) for stakeholder negotiation
   - **Kano** (Must-haves, Performance, Delighters) for value perception
   - **Value-Effort** (simple 2-axis) for resource-constrained teams
2. Gather inputs for framework scoring
3. Identify implementation dependencies
4. Suggest MVP vs. Phase 2 breakdown
5. Provide clear rationale for ranking

**Output:**
- Set `prioritized_backlog` (ranked requirements)
- Set `prioritization_framework` (framework used)
- Set `prioritization_complete` = True

**Example System Prompt:**
```
You are a Product Strategist recommending prioritization frameworks and rankings.

Framework Selection Logic:
- Use RICE for: Product roadmaps, feature prioritization, multiple stakeholders
- Use MoSCoW for: Stakeholder negotiation, scope control, clear categories
- Use Kano for: Understanding value perception, distinguishing must-haves from delighters
- Use Value-Effort for: Resource-constrained teams needing simple decisions

Steps:
1. Analyze project context (timeline, users, budget, business drivers)
2. Recommend framework with clear reasoning
3. Gather scoring inputs from user
4. Apply framework to rank all requirements
5. Identify dependencies and implementation sequences
6. Suggest phase breakdown (MVP vs. Phase 2)

Outputs:
For each requirement:
- Rank: [1, 2, 3, ...]
- Priority Level: [Must Have | Should Have | Could Have | Won't Have]
- Framework Score: [if applicable]
- Phase: [Phase 1 | Phase 2 | Backlog | Future]
- Dependencies: [requirements that must come first]
- Rationale: [why ranked here]

Tone: Analytical, enabling. Use role-based identity.
```

---

### 4.6 Synthesis Node

**Role:** Document Generator & Completeness Validator

**Inputs:**
- All previous phase outputs (requirements_raw, user_stories, quality_issues, acknowledged_risks, prioritized_backlog)

**Logic:**
1. Validate completeness (all required sections present)
2. Cross-reference stories ↔ requirements ↔ test cases
3. Assemble into 10-section user-centric structure:
   1. Executive Summary & Overview
   2. User Scenarios & Workflows
   3. Requirements (Master List)
   4. User Stories & Acceptance Criteria
   5. Functional Requirements (Detailed)
   6. Non-Functional Requirements
   7. Data Model & Entities
   8. Testing Strategy & Edge Cases
   9. Success Criteria & Measurable Outcomes
   10. Appendices (Assumptions, Constraints, Risks, Acknowledged Risks, Glossary)
4. Generate markdown document
5. Provide summary of journey

**Output:**
- Set `final_deliverable` (complete markdown document)
- Set `synthesis_complete` = True

**Example Logic:**
```python
def synthesize_requirements(state: ForgeRequirementsState) -> str:
    """Assemble final 10-section deliverable"""
    
    doc = f"""# {state['project_name']} - Requirements Specification

## 1. Executive Summary & Overview
{generate_overview(state)}

## 2. User Scenarios & Workflows
{generate_scenarios(state)}

## 3. Requirements (Master List)
{generate_requirements_list(state)}

## 4. User Stories & Acceptance Criteria
{generate_user_stories(state)}

## 5. Functional Requirements (Detailed)
{generate_functional_reqs(state)}

## 6. Non-Functional Requirements
{generate_nonfunctional_reqs(state)}

## 7. Data Model & Entities
{generate_data_model(state)}

## 8. Testing Strategy & Edge Cases
{generate_testing_strategy(state)}

## 9. Success Criteria & Measurable Outcomes
{generate_success_criteria(state)}

## 10. Appendices
{generate_appendices(state)}
"""
    return doc
```

---

## 5. Tool Schemas

### 5.1 Discovery Agent Tools

```json
{
  "name": "extract_requirements_from_document",
  "description": "Analyze uploaded document (PDF, text, transcript) and extract candidate requirements",
  "parameters": {
    "type": "object",
    "properties": {
      "document_text": {
        "type": "string",
        "description": "Full text of the document to analyze"
      },
      "doc_type": {
        "type": "string",
        "enum": ["meeting_transcript", "spec_document", "brainstorm_notes", "user_feedback"],
        "description": "Type of document for context"
      }
    },
    "required": ["document_text"]
  },
  "returns": {
    "type": "array",
    "items": {
      "type": "object",
      "properties": {
        "id": "string",
        "title": "string",
        "description": "string",
        "type": "enum: [Functional, Non-Functional, Constraint, Assumption, Risk]"
      }
    }
  }
}
```

```json
{
  "name": "identify_gaps",
  "description": "Analyze captured requirements and identify potentially overlooked areas",
  "parameters": {
    "type": "object",
    "properties": {
      "current_requirements": {
        "type": "array",
        "description": "Requirements captured so far"
      }
    },
    "required": ["current_requirements"]
  },
  "returns": {
    "type": "object",
    "properties": {
      "gaps_identified": {
        "type": "array",
        "description": "Potential gap areas to explore"
      },
      "suggested_questions": {
        "type": "array",
        "description": "Questions to probe each gap"
      }
    }
  }
}
```

### 5.2 Quality Agent Tools

```json
{
  "name": "validate_requirement",
  "description": "Validate a single requirement across 4 dimensions (ambiguity, completeness, consistency, testability)",
  "parameters": {
    "type": "object",
    "properties": {
      "requirement_id": "string",
      "requirement_text": "string",
      "context": {
        "type": "object",
        "description": "Other related requirements for consistency check"
      }
    },
    "required": ["requirement_id", "requirement_text"]
  },
  "returns": {
    "type": "object",
    "properties": {
      "issues_found": {
        "type": "array",
        "items": {
          "category": "enum: [Ambiguity, Completeness, Inconsistency, Untestability]",
          "severity": "enum: [Critical, High, Medium, Low]",
          "description": "string",
          "recommended_fix": "string"
        }
      }
    }
  }
}
```

### 5.3 Prioritization Agent Tools

```json
{
  "name": "apply_prioritization_framework",
  "description": "Score and rank requirements using selected framework (RICE, MoSCoW, Kano, Value-Effort)",
  "parameters": {
    "type": "object",
    "properties": {
      "framework": {
        "type": "string",
        "enum": ["RICE", "MoSCoW", "Kano", "Value-Effort"],
        "description": "Prioritization framework to apply"
      },
      "requirements": {
        "type": "array",
        "description": "Requirements to rank"
      },
      "scoring_inputs": {
        "type": "object",
        "description": "Framework-specific inputs (reach, impact, effort for RICE; value/effort scores for others)"
      }
    },
    "required": ["framework", "requirements"]
  },
  "returns": {
    "type": "array",
    "items": {
      "rank": "number",
      "requirement_id": "string",
      "priority_level": "string",
      "framework_score": "number",
      "rationale": "string"
    }
  }
}
```

---

## 6. Decision Authority Matrix

| Decision Type | Authority Level | Implementation |
|---------------|-----------------|-----------------|
| **Classification of requirements** | Agent Autonomous | Discovery Agent categorizes (Functional/Non-Functional/Constraint) |
| **Detection of content type** | Agent Autonomous | Orchestrator detects (raw ideas vs. stories vs. requirements) |
| **Identification of quality issues** | Agent Autonomous | Quality Agent identifies ambiguity, gaps, inconsistencies |
| **Phase progression** | User Approval Required | Orchestrator suggests, user confirms (smart detection with user override) |
| **Risk acknowledgment** | User Approval Required | User approves "good enough" quality or acknowledges specific risks |
| **Framework selection** | Agent Recommendation | Prioritization Agent recommends framework; user selects |
| **Final prioritization ranking** | Agent Autonomous | Prioritization Agent ranks based on framework and user inputs |
| **Scope enforcement** | Agent Autonomous | Agents enforce scope boundaries (e.g., don't write code, don't make business decisions) |
| **Escalation triggers** | Agent Autonomous | Security/compliance risks escalate with explicit warning |

---

## 7. Integration Points

### 7.1 Input Interfaces

**Chat/Conversational:**
- User types project description or requirements
- Real-time interaction with agents
- File uploads for document analysis

**File Upload:**
- Accept: PDF, .txt, .docx (convert to text)
- Analyze: Extract requirements from documents
- Validation: Ask user to confirm relevance before extraction

**REST API (Optional):**
- POST `/project` — Create new project
- POST `/chat` — Send message to orchestrator
- GET `/project/{project_id}` — Get current state
- GET `/deliverable/{project_id}` — Get final requirements document

### 7.2 Output Interfaces

**Streamlit UI:**
- Real-time chat with each agent
- Progress indicators at phase boundaries
- File download for final deliverable

**Final Deliverable:**
- Format: Markdown (.md) with 10-section structure
- Includes: All requirements, stories, quality assessment, prioritization, risks
- Ready for: Stakeholder review, development team handoff, documentation

**MCP Server:**
- Register agents as tools for use in other workflows
- Expose endpoints: `/discovery`, `/authoring`, `/quality`, `/prioritization`
- Protocol: Model Context Protocol for Claude Desktop and other agents

### 7.3 Persistence

**Session State (In-Memory):**
- During active session: LangGraph maintains state in memory
- Fast interactions, low latency

**Optional Persistence (File/Database):**
- Save project state to JSON after each phase completion
- Location: `projects/{project_id}/state.json`
- Or: Database with PostgreSQL + sqlalchemy

```python
def save_project_state(project_id: str, state: ForgeRequirementsState):
    """Save state after each phase completion"""
    path = f"projects/{project_id}/state.json"
    with open(path, 'w') as f:
        json.dump(serialize_state(state), f, indent=2, default=str)

def load_project_state(project_id: str) -> ForgeRequirementsState:
    """Resume project from saved state"""
    path = f"projects/{project_id}/state.json"
    with open(path) as f:
        return deserialize_state(json.load(f))
```

---

## 8. Implementation Roadmap

### Phase 1: MVP (Weeks 1-2)
**Goal:** Core workflow (Discovery → Authoring → Quality → Synthesis)

- [ ] Set up LangGraph project structure
- [ ] Implement state schema (Pydantic)
- [ ] Build Orchestrator node (basic routing)
- [ ] Build Discovery Agent (Q&A loop)
- [ ] Build Authoring Agent (story transformation)
- [ ] Build Synthesis node (10-section markdown)
- [ ] Create Streamlit UI (chat interface, file upload)
- [ ] Basic testing (unit tests for nodes)

**Output:** Functional MVP that takes raw ideas → final deliverable

### Phase 2: Quality & Prioritization (Weeks 3-4)
**Goal:** Add Quality Agent and Prioritization Agent

- [ ] Implement Quality Agent (4-dimension validation)
- [ ] Implement Prioritization Agent (RICE, MoSCoW, etc.)
- [ ] Add pragmatic quality gates (risk acknowledgment)
- [ ] Add user checkpoints at phase boundaries
- [ ] Implement smart phase detection (Orchestrator)
- [ ] Integration testing (full workflow)

**Output:** Complete 5-agent network functional

### Phase 3: Polish & Enhancement (Weeks 5-6)
**Goal:** UX refinement, error handling, persistence

- [ ] Error recovery patterns (retry, fallback)
- [ ] Session persistence (save/load project state)
- [ ] Progress visualization (progress bars, metrics)
- [ ] Export options (markdown, PDF, JSON)
- [ ] Performance optimization
- [ ] Comprehensive testing (end-to-end)

**Output:** Production-ready MVP

### Phase 4: Advanced Features (Weeks 7-8)
**Goal:** Extensibility and integration

- [ ] REST API implementation
- [ ] MCP server integration
- [ ] Batch processing (multiple projects)
- [ ] Template library (project templates)
- [ ] Advanced prioritization (dependency graphing)
- [ ] Analytics (requirements metrics, quality scores)

**Output:** Full-featured system ready for enterprise deployment

---

## 9. Testing Strategy

### 9.1 Unit Tests (Node-Level)

```python
# test_discovery_agent.py
def test_extract_requirements_from_document():
    """Verify Discovery Agent correctly extracts requirements"""
    doc = """Meeting: User authentication discussion...
    [requirements text]"""
    
    state = ForgeRequirementsState(...)
    result = discovery_node(state)
    
    assert len(result["requirements_raw"]) > 0
    assert all(req["type"] in ["Functional", "Constraint"] for req in result["requirements_raw"])

def test_detect_content_type():
    """Verify content type detection works"""
    user_input = "As a user, I want to login..."
    assert detect_content_type(user_input) == "user_stories"
```

### 9.2 Integration Tests (Phase-to-Phase)

```python
# test_full_workflow.py
def test_discovery_to_authoring():
    """Full workflow: Discovery → Authoring"""
    # Initialize
    state = create_project_state("Test Project")
    
    # Discovery
    state = discovery_node(state)
    assert state["discovery_complete"]
    assert len(state["requirements_raw"]) > 0
    
    # Authoring
    state = authoring_node(state)
    assert state["authoring_complete"]
    assert len(state["user_stories"]) == len(state["requirements_raw"])
```

### 9.3 Behavior Validation (Spec Compliance)

```python
# test_persona_compliance.py
def test_discovery_warmth():
    """Verify Discovery Agent maintains warm tone"""
    state = ...
    response = discovery_agent.run(state)
    assert not any(negative_word in response for negative_word in ["wrong", "incorrect", "bad"])
    assert any(positive_word in response for positive_word in ["great", "helpful", "excellent"])

def test_quality_pragmatism():
    """Verify Quality Agent allows risk acknowledgment"""
    state = ...
    state["quality_issues"] = [QualityIssue(...)]
    response = quality_agent.run(state)
    assert "acknowledge" in response.lower() or "proceed" in response.lower()
```

---

## 10. Deployment Options

### 10.1 Local Development
- Python venv in `.venv/`
- Streamlit app with Ctrl+C restart
- File-based state persistence

### 10.2 Streamlit Cloud
- Deploy `streamlit_app.py` directly
- Free tier suitable for MVP
- Auto-reload on git push

### 10.3 Docker Container
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
ENTRYPOINT ["streamlit", "run", "streamlit_app.py"]
```

### 10.4 REST API + Frontend
- FastAPI backend with LangGraph
- React frontend (optional)
- Database-backed persistence
- Horizontal scaling ready

---

## 11. Configuration & Environment

```bash
# .env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
DEPLOYMENT_MODE=streamlit  # or: api, mcp
LOG_LEVEL=INFO
PROJECT_DIR=./projects
SESSION_TIMEOUT=3600
```

---

## 12. Success Criteria

### Technical Criteria
✅ All 5 agents implemented with correct routing  
✅ State schema properly validated (Pydantic)  
✅ Conversational interface functional  
✅ File upload and document analysis working  
✅ Final deliverable properly formatted (10 sections)  

### Specification Compliance
✅ Every goal in NETWORK-SPEC.md has implementation  
✅ Every non-goal has explicit exclusion logic  
✅ Decision authority matrix implemented correctly  
✅ Persona behavioral directives observable in interactions  

### User Experience
✅ Clear progress updates at each phase  
✅ Users can interrupt, refine, or skip phases  
✅ Pragmatic quality gates (users can proceed with risks)  
✅ Final deliverable ready for stakeholder review  

---

## 13. Known Constraints & Mitigations

| Constraint | Mitigation |
|-----------|-----------|
| LLM context window (8K-16K) | Split large projects across sessions; summarize state before passing to next agent |
| Cost of LLM API calls | Implement caching; batch similar requests; use cheaper models for simple classification |
| File upload size limits (Streamlit) | Implement chunking; support multiple uploads; guide users on document preparation |
| Ambiguous user input | Implement clarification loop (3-strike rule); mark items [NEEDS_REFINEMENT] |
| Quality gate blocking | Pragmatic approach: allow risk acknowledgment; don't perfect-block |

---

## Conclusion

This implementation plan translates the Forge Requirements Builder specification into concrete, implementable components. The LangGraph-based architecture provides the flexibility, state management, and human-in-the-loop patterns needed for a sophisticated multi-agent requirements system.

**Next Steps:**
1. Review and approve this plan
2. Set up development environment (Python, LangGraph, Streamlit)
3. Begin Phase 1 implementation (Orchestrator, Discovery, Authoring, Synthesis)
4. Implement testing strategy in parallel
5. Gather early user feedback on persona and workflows

---

**Implementation Plan Ready for Development Handoff**
