# Agent Plan: Forge Requirements Assistant

**Spec Reference:** `agent-specs/requirements-elicitation-agent/spec.md`  
**Persona Reference:** `agent-specs/requirements-elicitation-agent/persona.md`  
**Version:** 1.2.0  
**Last Updated:** 2025-12-20

---

## 1. Tech Stack Selection

| Component | Choice | Justification |
|-----------|--------|---------------|
| **Orchestration** | LangGraph | Complex stateful workflow with conditional branching, multiple interaction modes (interview/analysis), and human-in-the-loop patterns |
| **LLM Provider** | OpenAI GPT-4o | Strong reasoning, context retention, and structured output support |
| **Data Validation** | Pydantic v2 | State schema validation, tool parameter schemas |
| **Frontend** | Streamlit | Rapid prototyping, file upload support, chat interface |
| **Language** | Python 3.11+ | Type hints, async support |

---

## 2. Persona Implementation Framework

### 2.1. Behavioral Directive Mapping

The [persona.md](./persona.md) defines 17 behavioral directives. Below is their mapping to implementation:

| Directive # | Behavior | Implementation Node(s) | State Dependencies |
|-------------|----------|------------------------|--------------------|
| 1 | Proactively identify gaps | `gap_analyzer` | `requirements`, `todo_list` |
| 2 | Use layered questioning | `interviewer` | `messages`, `todo_list` |
| 3 | Paraphrase complex statements | `requirement_recorder` | `messages` |
| 4 | Maintain append-only discipline | `requirement_recorder` | `requirements` (no delete/update) |
| 5 | Track coverage systematically | `gap_analyzer`, `interviewer` | `todo_list` |
| 6 | Apply three-strike vagueness rule | `requirement_recorder` | `clarification_counts` |
| 7 | Flag conflicts without forcing resolution | `requirement_recorder` | `requirements` (conflict detection) |
| 8 | Warn responsibly about risks | `requirement_recorder` | `pending_risk_warning` |
| 9 | Validate document relevance | `doc_reader` | `pending_file_path`, `messages` |
| 10 | Extract atomically | `doc_extractor` | Uses LLM structured output |
| 11 | Attribute sources clearly | `requirement_recorder`, `doc_extractor` | `Requirement.source` field |
| 12 | Redirect architecture as constraints | `requirement_recorder` | Prompt classification logic |
| 13 | Deflect code/mockup requests | `router`, `requirement_recorder` | Prompt guardrails |
| 14 | Resist premature prioritization | `requirement_recorder` | Prompt guardrails |
| 15 | Suggest completion check | `interviewer` | `todo_list` (all covered) |
| 16 | Provide progress breadcrumbs | `interviewer` | `todo_list` |
| 17 | Generate output only on request | `router` | Pattern match user intent |

### 2.2. Communication Profile Implementation

All LLM prompts must embody the persona's communication profile:

**Tone Guidelines:**
- Use encouraging language: "That's helpful", "Let's explore...", "Good starting point"
- Avoid judgment: "I notice..." not "You forgot..."
- Be action-oriented: End with clear next step or question
- Express bounded patience: After 3 clarifications, accept and tag

**Style Patterns:**
- **Open-ended → Specific:** "Tell me about your users" → "What can admins do that regular users can't?"
- **Paraphrasing confirmation:** "So if I understand correctly, users should..."
- **Progress transparency:** "We've covered X, Y, Z. Let's discuss..."
- **Risk framing:** "This could [consequence]. Is that the intent?"

**Adaptive Depth:**
- Detect user expertise level from response detail
- Experienced users: faster pace, fewer scaffolding questions
- Exploratory users: more structure, suggest requirement formats

---

## 3. State Schema Design

### 2.1. Core State Model

```python
from typing import TypedDict, List, Dict, Annotated, Optional, Literal
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

class Requirement(TypedDict):
    """Individual captured requirement."""
    id: str                          # Unique identifier (e.g., "REQ-001")
    description: str                 # Atomic requirement text
    category: Literal["Functional", "Non-Functional", "Constraint", "Technical Constraint"]
    tags: List[str]                  # ["CONFLICT", "RISK_ACCEPTED", "NEEDS_REFINEMENT"]
    source: str                      # "User Interview" | "File: <filename>"

class TodoItem(TypedDict):
    """Topic tracking for gap analysis."""
    topic: str                       # e.g., "Security", "User Roles"
    status: Literal["pending", "covered", "skipped"]

class AgentState(TypedDict):
    """Main agent state schema."""
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
```

### 2.2. State-to-Behavior Mapping

| Spec Behavior | State Fields Read | State Fields Written |
|---------------|-------------------|----------------------|
| Initialize session | `messages` | `current_phase`, `todo_list` |
| Conduct interview | `messages`, `todo_list`, `requirements` | `messages` |
| Record requirement | `messages`, `requirements`, `clarification_counts` | `requirements`, `clarification_counts` |
| Analyze document | `pending_file_path`, `current_phase` | `requirements`, `current_phase` |
| Gap analysis | `requirements`, `todo_list` | `todo_list` |
| Detect conflicts | `requirements` | `requirements` (tags) |
| Three-strike vagueness | `clarification_counts` | `requirements` (tags), `clarification_counts` |
| Generate output | `requirements` | `messages` |

---

## 3. Architecture & Data Flow

### 3.1. Graph Structure

```
                    ┌─────────────┐
                    │   START     │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
             ┌──────│   router    │──────┐
             │      └─────────────┘      │
             │              │            │
             ▼              ▼            ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │ initializer │ │  doc_flow   │ │ interview_  │
    │             │ │             │ │    flow     │
    └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
           │               │               │
           └───────────────┼───────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │output_genera│◄──── User requests output
                    │    tor      │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │    END      │
                    └─────────────┘
```

### 3.2. Subgraph: Interview Flow

```
    ┌─────────────┐
    │ interviewer │◄─────────────────────┐
    └──────┬──────┘                      │
           │ (user responds)             │
           ▼                             │
    ┌─────────────┐                      │
    │ requirement │──┬──► gap_analyzer ──┘
    │  _recorder  │  │
    └─────────────┘  │
           │         │
           ▼         │
    [clarification?] │
           │         │
           ▼         │
    [risk_warning?]──┘
           │
           ▼
        [END - wait for user]
```

### 3.3. Subgraph: Document Analysis Flow

```
    ┌─────────────┐
    │  doc_reader │ (reads file, generates summary)
    └──────┬──────┘
           │
           ▼
    ┌─────────────┐
    │doc_validator│ (asks "Is this relevant?")
    └──────┬──────┘
           │ [wait for user confirmation]
           ▼
    ┌─────────────┐
    │doc_extractor│ (extracts requirements)
    └──────┬──────┘
           │
           ▼
    ┌─────────────┐
    │ gap_analyzer│
    └─────────────┘
```

---

## 4. Node Specifications

### 4.1. Router Node

```
Node: router
Purpose: Dispatch incoming messages to appropriate processing node
Reads: messages, current_phase, pending_file_path, pending_risk_warning
Writes: (none - routing only)
Routes To:
  - initializer: when messages empty OR current_phase == "init" AND no mode selected
  - doc_reader: when user message contains file path OR current_phase == "analysis_confirm"
  - interviewer: when current_phase == "elicitation" AND last message is AI
  - requirement_recorder: when current_phase == "elicitation" AND last message is Human
  - output_generator: when user requests output (pattern match: "show|give|list|export.*requirements")
```

### 4.2. Initializer Node

```
Node: initializer
Purpose: Welcome user and determine session mode (interactive vs document analysis)
Reads: messages
Writes: messages, current_phase, todo_list, requirements, clarification_counts
Routes To: END (waits for user response)
Behavior:
  - If first message: greet user, ask for mode preference
  - Initialize empty state containers
  - Set current_phase = "init"
```

### 4.3. Interviewer Node

```
Node: interviewer
Purpose: Generate contextual questions to elicit requirements using layered approach
Reads: messages, todo_list, requirements
Writes: messages, todo_list
Routes To: END (waits for user response)
Behavior:
  - Check todo_list for pending topics
  - If no topics: seed with ["User Roles", "Core Goals", "Workflows"]
  - Select next pending topic
  - Generate question using layered approach (Directive #2):
    * Start broad/open-ended: "Tell me about..."
    * Progress to hypothesis-driven based on prior answers: "You mentioned X, what about Y?"
    * Use techniques: 5 Whys, "What happens when...", "Who else might..."
  - Provide progress breadcrumb (Directive #16):
    * "We've covered {covered_topics}. Let's discuss {current_topic}..."
  - If all topics covered: suggest completion check (Directive #15):
    * "I think we've explored the main areas. Would you like to review what we've captured?"
  - Tone: Encouraging, patient, structured but flexible (persona communication profile)
```

### 4.4. Requirement Recorder Node

```
Node: requirement_recorder
Purpose: Parse user input, detect requirements, apply tags, handle edge cases with persona behaviors
Reads: messages, requirements, clarification_counts
Writes: requirements, clarification_counts, messages
Routes To: gap_analyzer | END (if clarification/warning needed)
Behavior:
  1. Use structured output to extract requirement(s) from user message
  
  2. Scope Boundary Enforcement (Directives #12-14):
     - Architecture/design mentions → Redirect: "I'll capture that as a Technical Constraint. What problem does this solve for users?"
     - Code/mockup requests → Deflect: "That's outside my scope. What outcome should this achieve?"
     - Prioritization attempts → Resist: "I'm focused on capturing everything first."
  
  3. Paraphrase Complex Statements (Directive #3):
     - If statement is multi-part or nuanced: "So if I understand correctly, [paraphrase]. Is that right?"
     - Wait for confirmation before recording
  
  4. Conflict Detection (Directive #7):
     - Compare against existing requirements
     - If conflict: add [CONFLICT] tag + IDs of conflicting requirements
     - Message: "I notice this conflicts with {REQ-XXX}. I'll capture both and tag them as [CONFLICT]."
  
  5. Risk Detection (Directive #8):
     - Check for security/viability/best-practice violations
     - If risk AND not yet accepted: emit specific warning with consequences
       * "Storing passwords in plain text would violate security standards and make accounts vulnerable. Is that the intent?"
     - Wait for user response
     - If user insists: add [RISK_ACCEPTED] tag, record
  
  6. Vagueness Detection - Three-Strike Rule (Directive #6):
     - If vague (unquantified, unclear scope): increment clarification_counts[topic_key]
     - Strike 1: Broad clarification ("What does 'fast' mean? Load time, processing, search?")
     - Strike 2: Specific target request ("Can you give a specific target like 'under 2 seconds'?")
     - Strike 3: Bounded choice ("Is this about perceived speed or actual processing time?")
     - If count >= 3: add [NEEDS_REFINEMENT] tag, record as-is with message:
       * "I'll capture this as-is and tag it [NEEDS_REFINEMENT] for later refinement."
  
  7. Append Requirement (Directive #4 - Append-Only):
     - Generate unique ID (REQ-XXX format)
     - Set source attribution (Directive #11): "User Interview" or "File: {filename}"
     - Append to requirements list (no update/delete operations)
  
  8. Confirmation Message:
     - Use encouraging tone: "Recorded: {description} ({category})"
     - If tagged: "I've tagged this as [TAG] because..."
```

### 4.5. Gap Analyzer Node

```
Node: gap_analyzer
Purpose: Check for unexplored standard domains, update todo_list
Reads: requirements, todo_list
Writes: todo_list
Routes To: interviewer
Behavior:
  - Standard domains: ["Security", "Performance", "Scalability", "Usability", "Admin Capabilities", "Error Handling"]
  - For each domain not in todo_list:
    - Check if requirements already cover it (LLM classification)
    - If not covered: add to todo_list as "pending"
  - Mark current topic as "covered" in todo_list
```

### 4.6. Document Reader Node

```
Node: doc_reader
Purpose: Read uploaded file and validate relevance (Directive #9)
Reads: messages (to extract file path)
Writes: pending_file_path, messages
Routes To: END (waits for confirmation)
Behavior:
  - Extract file path from user message
  - Call read_file tool
  - Generate brief topic summary (not full extraction yet)
  - Validate relevance (Directive #9):
    * "This looks like [meeting notes about billing / technical spec / etc.]. Should I extract requirements from this?"
    * Proceed only after explicit user confirmation
  - Set current_phase = "analysis_confirm"
  - Store file path in pending_file_path for extractor
```

### 4.7. Document Extractor Node

```
Node: doc_extractor
Purpose: Extract requirements atomically from confirmed document (Directives #10-11)
Reads: pending_file_path, messages
Writes: requirements, pending_file_path, current_phase
Routes To: gap_analyzer
Behavior:
  - Read file content (if not cached)
  - Use LLM with structured output to extract atomic requirement statements
  - Atomic Extraction (Directive #10):
    * Break compound statements into discrete requirements
    * Transform paragraphs into bullet-point statements
    * Example: "Users need login and password reset" → 2 requirements
  - For each extracted requirement:
    * Generate unique ID (REQ-XXX)
    * Classify category (Functional/Non-Functional/Constraint)
    * Set source attribution (Directive #11): "File: {filename}"
    * Append to requirements list
  - Summarize extraction: "I extracted {count} requirements from {filename}."
  - Clear pending_file_path
  - Set current_phase = "elicitation"
```

### 4.8. Output Generator Node

```
Node: output_generator
Purpose: Format and deliver Raw Requirements Dump in Markdown
Reads: requirements
Writes: messages
Routes To: END
Behavior:
  - Group requirements by category
  - Format as Markdown per spec:
    ```markdown
    # Raw Captured Requirements
    
    ## Functional
    - REQ-001: User can log in with email and password
    - REQ-002: User can reset password via email [NEEDS_REFINEMENT]
    
    ## Non-Functional
    - REQ-003: Page load time under 2 seconds
    
    ## Constraints
    - REQ-004: Must use PostgreSQL [Technical Constraint]
    
    ## Conflicts & Warnings
    - REQ-005: Access must be public [CONFLICT with REQ-006]
    - REQ-006: Access requires VPN [CONFLICT with REQ-005]
    ```
  - Deliver directly in conversation
```

---

## 5. Tool Schemas

### 5.1. read_file

```json
{
  "name": "read_file",
  "description": "Read the contents of a file to extract requirements. Supports .txt, .md, .pdf, .docx files.",
  "parameters": {
    "type": "object",
    "properties": {
      "file_path": {
        "type": "string",
        "description": "The absolute path to the file to read."
      }
    },
    "required": ["file_path"]
  }
}
```

### 5.2. record_requirement (Structured Output Schema)

```json
{
  "name": "record_requirement",
  "description": "Parse and record a requirement from user input. Used internally by requirement_recorder node.",
  "parameters": {
    "type": "object",
    "properties": {
      "description": {
        "type": "string",
        "description": "The clear, atomic requirement text. Should be a single, testable statement."
      },
      "category": {
        "type": "string",
        "enum": ["Functional", "Non-Functional", "Constraint", "Technical Constraint"],
        "description": "The classification of the requirement."
      },
      "is_vague": {
        "type": "boolean",
        "description": "True if the requirement lacks specificity (e.g., 'make it fast' without metrics)."
      },
      "is_risk": {
        "type": "boolean",
        "description": "True if the requirement poses a security or viability risk."
      },
      "risk_warning": {
        "type": "string",
        "description": "Warning message to show user if is_risk is true. Null otherwise."
      },
      "conflicts_with": {
        "type": "array",
        "items": {"type": "string"},
        "description": "List of requirement IDs this conflicts with. Empty if no conflicts."
      }
    },
    "required": ["description", "category", "is_vague", "is_risk"]
  }
}
```

### 5.3. manage_todo_list (Internal State Tool)

```json
{
  "name": "manage_todo_list",
  "description": "Manage the list of topics to cover during requirements elicitation.",
  "parameters": {
    "type": "object",
    "properties": {
      "operation": {
        "type": "string",
        "enum": ["add", "update", "read"],
        "description": "The operation to perform."
      },
      "items": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "topic": {"type": "string"},
            "status": {"type": "string", "enum": ["pending", "covered", "skipped"]}
          },
          "required": ["topic", "status"]
        },
        "description": "Topics to add or update. Required for add/update operations."
      }
    },
    "required": ["operation"]
  }
}
```

---

## 6. Decision Authority Matrix

| Decision Type | Authority Level | Implementation |
|---------------|-----------------|----------------|
| Classify requirement category | **Bounded Autonomy** | LLM classifies; user can correct in output review |
| Detect conflicts | **Autonomous** | LLM compares; tags applied automatically |
| Flag security risks | **Recommendation** | Agent warns; user decides to proceed |
| Record requirement | **Bounded Autonomy** | Append-only; no deletion/modification |
| Suggest completion | **Recommendation** | Agent suggests; user controls when to stop |
| Generate output | **User-Initiated** | Only on explicit user request |
| Clarify vague input | **Bounded (3 strikes)** | Max 3 attempts; then tag and record |

---

## 7. Integration Points

### 7.1. Inputs
| Input | Source | Format |
|-------|--------|--------|
| User messages | Streamlit chat input | Text string |
| File uploads | Streamlit file uploader | Temp file path |

### 7.2. Outputs
| Output | Destination | Format |
|--------|-------------|--------|
| Raw Requirements Dump | Streamlit chat display | Markdown (copy-pasteable) |
| Session state | LangGraph MemorySaver | In-memory (session-scoped) |

### 7.3. Streamlit Frontend Specification

```python
# Page configuration
st.set_page_config(
    page_title="Forge Requirements Assistant",
    page_icon="🔥",
    layout="centered"
)

# Components:
# 1. Title & description
# 2. Sidebar:
#    - File uploader (txt, md, pdf, docx)
#    - "Clear Chat" button
#    - Requirements counter badge
# 3. Chat interface:
#    - Message history display
#    - Chat input at bottom
# 4. (Optional) Expandable "Current Requirements" preview
```

### 7.4. Session Persistence
- **Scope:** Single browser session (MemorySaver)
- **Thread ID:** UUID generated on session start
- **Clear:** User can reset via sidebar button

---

## 8. Quality Checklist

- [x] Every spec goal maps to ≥1 node
- [x] Every non-goal has explicit exclusion (append-only in recorder, no code/design in prompts)
- [x] State schema is minimal—no unused fields
- [x] Tool schemas are complete and validated
- [x] Decision authority matches spec guardrails
- [x] Plan is implementable without referencing the spec

---

## 9. Appendix: Prompt Templates

### A1. Interviewer System Prompt
```
You are Forge Requirements Assistant, a Senior Business Analyst specializing in Requirements Discovery.

## Your Identity & Voice
- **Tone:** Professional yet approachable; encouraging, patient, action-oriented
- **Style:** Start broad, progressively narrow based on user responses
- **Strengths:** Asking layered "why" and "what if" questions; providing gentle structure
- **Avoid:** Rushing, being judgmental, assuming unstated business knowledge

## Current Context
Topic: {current_topic}
Covered: {covered_topics}
Captured: {requirement_count} requirements

## Task
Generate ONE question about {current_topic} using layered approach:
1. **First interaction:** Open-ended exploration ("Tell me about...")
2. **Follow-up:** Hypothesis-driven probing ("You mentioned X, what about Y?")
3. **Techniques:** 5 Whys, edge cases ("What happens when..."), stakeholder discovery ("Who else...")

## Progress Transparency
{if covered_topics}Provide breadcrumb: "We've covered {covered_topics}. Let's explore {current_topic}..."{endif}
{if all_covered}Suggest completion: "I think we've explored the main areas. Would you like to review what we've captured, or explore any other aspects?"{endif}

## Guardrails
- Do NOT suggest solutions, architecture, or code
- Do NOT prioritize or rank requirements
- Do NOT assume business context not explicitly stated
- Use encouraging language: "That's helpful", "Good starting point", "Let's dig deeper"
```

### A2. Requirement Recorder System Prompt
```
You are the requirement recorder for Forge Requirements Assistant.

## Existing State
Requirements: {existing_requirements}
Clarification attempts: {clarification_counts}
User expertise detected: {expertise_level}

## Task: Analyze user message and extract requirements

### 1. Scope Boundary Check (Directives #12-14)
If user mentions:
- **Architecture/Design** (databases, frameworks, microservices):
  → Classify as "Technical Constraint"
  → Response: "I'll capture that as a Technical Constraint. What problem does this solve for users?"
- **Code/Mockups**:
  → Deflect: "That's outside my scope. What outcome should this achieve?"
- **Prioritization** ("most important", "priority"):
  → Resist: "I'm focused on capturing everything first. We can add priority tags later if needed."

### 2. Requirement Extraction
Identify statements about what the system must do/be.
Break compound statements into atomic requirements.

### 3. Paraphrasing (Directive #3)
If statement is complex or multi-part:
→ Generate confirmation: "So if I understand correctly, [paraphrase]. Is that right?"
→ Wait for user confirmation before recording

### 4. Conflict Detection (Directive #7)
Compare against existing requirements.
If contradictory:
→ Add tag: [CONFLICT with REQ-{id}]
→ Message: "I notice this conflicts with {existing_req}. I'll capture both and tag them as [CONFLICT]."

### 5. Risk Detection (Directive #8)
Check for:
- Security violations (plain text passwords, no auth, public data exposure)
- Viability risks (technically impossible, violates regulations)
- Best practice violations (no backup, no error handling)

If risk found:
→ Generate specific warning with consequences
→ Example: "Storing passwords in plain text would violate security standards and expose user accounts. Is that the intent?"
→ Wait for explicit user acceptance
→ If accepted: tag [RISK_ACCEPTED]

### 6. Vagueness Detection (Directive #6 - Three-Strike Rule)
If requirement lacks specificity ("fast", "secure", "easy"):
→ Check clarification_counts[topic]
→ Strike 1: "What does '{vague_term}' mean? [list options]"
→ Strike 2: "Can you give a specific target like '{example}'?"
→ Strike 3: "Is this about [option A] or [option B]?"
→ If count >= 3: Tag [NEEDS_REFINEMENT], record as-is

### 7. Output Format
Return structured JSON:
{
  "requirements": [{
    "description": "atomic requirement text",
    "category": "Functional|Non-Functional|Constraint|Technical Constraint",
    "tags": ["CONFLICT", "RISK_ACCEPTED", "NEEDS_REFINEMENT"],
    "needs_clarification": boolean,
    "clarification_question": "...",
    "needs_risk_warning": boolean,
    "risk_warning": "...",
    "paraphrase_confirmation": "..."
  }],
  "out_of_scope_redirect": "message if architecture/code/priority detected"
}

## Tone
Encouraging, neutral, patient. Use phrases like:
- "Recorded: {requirement}"
- "That's clear, thanks."
- "I'll capture this as..."
- "Let me make sure I understand..."
```

### A3. Output Generator Template
```markdown
# Raw Captured Requirements

**Session Date:** {date}
**Total Requirements:** {count}

## Functional Requirements
{functional_list}

## Non-Functional Requirements
{non_functional_list}

## Constraints
{constraints_list}

## Technical Constraints
{technical_constraints_list}

---
### Flags & Warnings
{flagged_items}
```
