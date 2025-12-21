# Tasks: Forge Requirements Assistant

**Spec Reference:** `agent-specs/requirements-elicitation-agent/spec.md`  
**Plan Reference:** `agent-specs/requirements-elicitation-agent/plan.md`  
**Persona Reference:** `agent-specs/requirements-elicitation-agent/persona.md`  
**Version:** 1.3.0  
**Last Updated:** 2025-12-20

---

## Phase 1: Foundation & State Models

- [x] **Task 1.1:** Set up project structure with required dependencies
  - *Ref:* Plan Section 1 (Tech Stack)
  - *Details:* Ensure `pyproject.toml` or `requirements.txt` includes: `langgraph`, `langchain-openai`, `langchain-core`, `pydantic>=2.0`, `streamlit`, `python-dotenv`
  - *Verify:* `pip install -e .` succeeds; imports resolve without error

- [x] **Task 1.2:** Define `Requirement` TypedDict model
  - *Ref:* Plan Section 2.1
  - *Details:* Fields: `id` (str), `description` (str), `category` (Literal), `tags` (List[str]), `source` (str)
  - *Verify:* Type checker accepts model; test instantiation with sample data

- [x] **Task 1.3:** Define `TodoItem` TypedDict model
  - *Ref:* Plan Section 2.1
  - *Details:* Fields: `topic` (str), `status` (Literal["pending", "covered", "skipped"])
  - *Verify:* Type checker accepts model

- [x] **Task 1.4:** Define `AgentState` TypedDict with all required fields
  - *Ref:* Plan Section 2.1
  - *Details:* Fields: `messages` (with `add_messages` reducer), `current_phase`, `requirements`, `todo_list`, `clarification_counts`, `pending_file_path`, `pending_risk_warning`
  - *Verify:* LangGraph accepts state schema in `StateGraph(AgentState)`

---

## Phase 2: Tool Implementations

- [x] **Task 2.1:** Implement `read_file` tool with Pydantic schema
  - *Ref:* Plan Section 5.1
  - *Details:* Accept `file_path` string, read file contents, handle errors gracefully. Support `.txt`, `.md` files (PDF/DOCX as stretch goal)
  - *Verify:* Tool reads sample file; returns error message for invalid path

- [x] **Task 2.2:** Implement `manage_todo_list` tool with Pydantic schema
  - *Ref:* Plan Section 5.3
  - *Details:* Operations: `add`, `update`, `read`. Accept list of `TodoItem` objects for add/update
  - *Verify:* Unit test for each operation type

- [x] **Task 2.3:** Define `RecordRequirement` Pydantic model for structured output
  - *Ref:* Plan Section 5.2
  - *Details:* Fields: `description`, `category`, `is_vague`, `is_risk`, `risk_warning` (Optional), `conflicts_with` (List[str])
  - *Verify:* LLM `with_structured_output(RecordRequirement)` returns valid objects

---

## Phase 3: Core Node Implementations

- [x] **Task 3.1:** Implement `initializer` node
  - *Ref:* Plan Section 4.2
  - *Details:* 
    - If no messages: emit greeting with mode selection prompt
    - Initialize state: `current_phase="init"`, empty `requirements`, `todo_list`, `clarification_counts`
  - *Verify:* First invocation returns greeting; state fields initialized correctly

- [x] **Task 3.2:** Implement `interviewer` node
  - *Ref:* Plan Section 4.3, Persona Directive #2, #5, #15, #16
  - *Details:*
    - Read `todo_list` for pending topics
    - If empty: seed with ["User Roles", "Core Goals", "Workflows"]
    - Generate contextual question using LLM with persona-aligned interviewer system prompt
    - Implement layered questioning: start broad, narrow based on prior responses
    - Add progress breadcrumbs: "We've covered {topics}. Let's discuss {current}..."
    - If all topics covered: suggest completion check per Directive #15
  - *Verify:* Generates relevant layered question; provides progress context; suggests review when complete

- [x] **Task 3.3:** Implement `requirement_recorder` node - basic recording with persona behaviors
  - *Ref:* Plan Section 4.4, Persona Directives #3, #4, #11
  - *Details:*
    - Use `llm.with_structured_output(RecordRequirement)` to parse user message
    - If requirement found: append to `requirements` list with generated ID (append-only per Directive #4)
    - Set source attribution: "User Interview" (Directive #11)
    - Implement paraphrasing for complex statements (Directive #3): "So if I understand correctly..."
    - Emit confirmation with encouraging tone: "Recorded: {description} ({category})"
  - *Verify:* User statement parsed and recorded; paraphrasing triggered for complex inputs; confirmation uses persona voice

- [x] **Task 3.4:** Implement `requirement_recorder` - conflict detection
  - *Ref:* Plan Section 4.4, Persona Directive #7, Spec Clarification (Record & Flag)
  - *Details:*
    - Compare new requirement against existing requirements using LLM
    - If conflict detected: add `[CONFLICT with REQ-XXX]` tag to new requirement
    - Record both conflicting requirements (append-only, Directive #4)
    - Message per Directive #7: "I notice this conflicts with {existing}. I'll capture both and tag them as [CONFLICT]."
    - Do NOT force immediate resolution
  - *Verify:* Contradictory statements both recorded with CONFLICT tags; neutral framing message

- [x] **Task 3.5:** Implement `requirement_recorder` - risk detection
  - *Ref:* Plan Section 4.4, Persona Directive #8, Spec Section 6 (Safety)
  - *Details:*
    - If `is_risk=True` and not previously accepted: emit specific warning with consequences (Directive #8)
    - Example: "Storing passwords in plain text would violate security standards and expose accounts. Is that the intent?"
    - Wait for explicit user response, return END
    - If user confirms acceptance: add `[RISK_ACCEPTED]` tag, record with neutral acknowledgment
  - *Verify:* Security risk triggers detailed warning; acceptance records with tag; maintains neutral tone

- [x] **Task 3.6:** Implement `requirement_recorder` - Three-Strike Rule
  - *Ref:* Plan Section 4.4, Persona Directive #6, Spec Clarification (Three-Strike Rule)
  - *Details:*
    - If `is_vague=True`: increment `clarification_counts[topic_key]`
    - Progressive clarification per Directive #6:
      * Strike 1: Broad clarification ("What does 'fast' mean? Load time, processing, search?")
      * Strike 2: Specific target request ("Can you give a specific target like 'under 2 seconds'?")
      * Strike 3: Bounded choice ("Is this about perceived speed or actual processing time?")
    - If count < 3: ask appropriate clarification, return END
    - If count >= 3: add `[NEEDS_REFINEMENT]` tag, record as-is with message: "I'll capture this as-is and tag it [NEEDS_REFINEMENT] for later refinement."
  - *Verify:* Progressive clarification questions; 3rd attempt → record with tag and patient message

- [x] **Task 3.7:** Implement `gap_analyzer` node
  - *Ref:* Plan Section 4.5, Persona Directive #1, #5
  - *Details:*
    - Standard domains: ["Security", "Performance", "Scalability", "Usability", "Admin Capabilities", "Error Handling"]
    - Check if each domain is in `todo_list` or covered by existing requirements
    - Proactively add missing domains to `todo_list` as "pending" (Directive #1)
    - Mark current topic as "covered" (Directive #5)
    - Use neutral framing: "Let me check if there's anything about {domain} we should discuss..."
  - *Verify:* Missing domains added to todo_list; current topic marked covered; helpful framing used

- [x] **Task 3.8:** Implement `doc_reader` node
  - *Ref:* Plan Section 4.6, Persona Directive #9
  - *Details:*
    - Extract file path from user message
    - Call `read_file` tool
    - Generate brief topic summary using LLM (not full extraction)
    - Validate relevance per Directive #9: "This looks like [meeting notes about billing / technical spec]. Should I extract requirements from this?"
    - Set `current_phase = "analysis_confirm"`, store `pending_file_path`
    - Wait for explicit user confirmation
  - *Verify:* File read; concise summary generated; relevance confirmation requested; no extraction until confirmed

- [x] **Task 3.9:** Implement `doc_extractor` node
  - *Ref:* Plan Section 4.7, Persona Directives #10, #11
  - *Details:*
    - Read cached file content
    - Use LLM with structured output to extract atomic requirement statements (Directive #10)
    - Atomic extraction: break compound statements into discrete requirements
      * Example: "Users need login and password reset" → 2 separate requirements
    - Create `Requirement` objects with clear source attribution (Directive #11): `source = "File: {filename}"`
    - Append to requirements list
    - Summarize: "I extracted {count} requirements from {filename}."
    - Clear `pending_file_path`, set `current_phase = "elicitation"`
  - *Verify:* Requirements extracted atomically; source field set correctly; summary provided

- [x] **Task 3.10:** Implement `output_generator` node
  - *Ref:* Plan Section 4.8, Appendix A3, Spec Step 6
  - *Details:*
    - Group requirements by category
    - Format as Markdown with headers, bullet points, inline tags
    - Include Flags & Warnings section for tagged items
    - Emit as AI message
  - *Verify:* Output matches spec format; all tags displayed correctly

---

## Phase 3.5: Persona Behavioral Logic

- [x] **Task 3.11:** Implement scope boundary enforcement logic
  - *Ref:* Plan Section 4.4, Persona Directives #12-14
  - *Details:*
    - Detect architecture/design mentions in user messages (databases, frameworks, microservices)
    - Redirect: "I'll capture that as a Technical Constraint. What problem does this solve for users?"
    - Detect code/mockup requests
    - Deflect: "That's outside my scope. What outcome should this achieve?"
    - Detect prioritization attempts ("most important", "priority")
    - Resist: "I'm focused on capturing everything first. We can add priority tags later if needed."
  - *Verify:* Out-of-scope requests redirected with helpful framing; requirement captured as appropriate category

- [x] **Task 3.12:** Implement adaptive communication depth detection
  - *Ref:* Plan Section 2.2 (Adaptive Depth)
  - *Details:*
    - Analyze user response detail/length to infer expertise level
    - Track response patterns (brief vs. detailed, technical vs. non-technical language)
    - Adjust question complexity and scaffolding accordingly
    - Experienced users: faster pace, fewer examples, assume domain vocabulary
    - Exploratory users: more structure, suggest requirement formats, model good statements
  - *Verify:* Questioning style adapts based on user response patterns

- [x] **Task 3.13:** Enhance all LLM prompts with persona tone guidelines
  - *Ref:* Plan Sections 2.2, A1, A2
  - *Details:*
    - Add persona identity block to all system prompts
    - Incorporate tone patterns: encouraging ("That's helpful"), neutral ("I notice..."), action-oriented
    - Add behavioral guardrails: no rushing, no judgment, no assumptions
    - Include example phrases for each prompt type
    - Verify consistency across initializer, interviewer, recorder prompts
  - *Verify:* All prompts use consistent persona voice; tone guidelines visible in responses

---

## Phase 4: Graph Orchestration & Routing

- [x] **Task 4.1:** Implement `router` conditional logic
  - *Ref:* Plan Section 4.1, Persona Directive #17
  - *Details:*
    - Route to `initializer`: messages empty OR `current_phase == "init"` with no mode selected
    - Route to `doc_reader`: user message contains file path
    - Route to `doc_extractor`: `current_phase == "analysis_confirm"` and user confirmed
    - Route to `interviewer`: `current_phase == "elicitation"` and last message is AI
    - Route to `requirement_recorder`: `current_phase == "elicitation"` and last message is Human
    - Route to `output_generator`: user explicitly requests output (Directive #17)
      * Pattern match: "show|give|list|export|generate.*requirements|summary|dump"
  - *Verify:* Each routing condition tested with mock state; output only generated on explicit request

- [x] **Task 4.2:** Implement `recorder_router` conditional logic
  - *Ref:* Plan Section 3.2 (Interview Flow)
  - *Details:*
    - If clarification requested or risk warning emitted: return END
    - Otherwise: route to `gap_analyzer`
  - *Verify:* Clarification stops flow; confirmation continues to gap_analyzer

- [x] **Task 4.3:** Construct main StateGraph with all nodes
  - *Ref:* Plan Section 3.1
  - *Details:*
    - Add nodes: `initializer`, `interviewer`, `requirement_recorder`, `gap_analyzer`, `doc_reader`, `doc_extractor`, `output_generator`
    - Set conditional entry point using `router`
  - *Verify:* Graph compiles without error

- [x] **Task 4.4:** Wire up graph edges
  - *Ref:* Plan Sections 3.1, 3.2, 3.3
  - *Details:*
    - `initializer` → END
    - `interviewer` → END
    - `requirement_recorder` → (conditional) → `gap_analyzer` | END
    - `gap_analyzer` → `interviewer`
    - `doc_reader` → END
    - `doc_extractor` → `gap_analyzer`
    - `output_generator` → END
  - *Verify:* Graph visualization matches plan diagrams

- [x] **Task 4.5:** Compile graph with MemorySaver checkpointer
  - *Ref:* Plan Section 7.4
  - *Details:*
    - Use `MemorySaver()` for session persistence
    - Thread ID passed via config
  - *Verify:* State persists across multiple invocations with same thread_id

---

## Phase 5: Streamlit Frontend

- [x] **Task 5.1:** Create Streamlit app skeleton
  - *Ref:* Plan Section 7.3
  - *Details:*
    - Page config: title="Forge Requirements Assistant", icon="🔥"
    - Title and description header
    - Initialize session state for `thread_id`, `messages`, `processed_files`
  - *Verify:* App loads; session state initialized

- [x] **Task 5.2:** Implement sidebar with file uploader
  - *Ref:* Plan Section 7.3
  - *Details:*
    - File uploader: accept `.txt`, `.md`, `.pdf`, `.docx`
    - "Clear Chat" button to reset session
    - (Optional) Requirements counter badge
  - *Verify:* File upload triggers agent; clear button resets state

- [x] **Task 5.3:** Implement chat interface
  - *Ref:* Plan Section 7.3
  - *Details:*
    - Display message history from session state
    - Chat input at bottom
    - Process input through LangGraph agent
    - Display AI responses in real-time
  - *Verify:* Full conversation flow works end-to-end

- [x] **Task 5.4:** Handle file upload flow
  - *Ref:* Plan Section 7.1
  - *Details:*
    - Save uploaded file to temp location
    - Pass file path to agent as user message
    - Track processed files to avoid re-processing on rerun
  - *Verify:* Uploaded file triggers document analysis flow

- [x] **Task 5.5:** Add requirements preview expander (optional enhancement)
  - *Ref:* Plan Section 7.3
  - *Details:*
    - Expandable section showing current requirements list
    - Updates after each requirement recorded
  - *Verify:* Preview shows captured requirements; updates dynamically

---

## Phase 6: Testing & Validation

- [x] **Task 6.1:** Unit test: Three-Strike Rule logic
  - *Ref:* Plan Section 4.4, Persona Directive #6, Spec Clarification
  - *Details:*
    - Simulate 3 consecutive vague inputs for same topic
    - Assert: Strike 1 → broad clarification; Strike 2 → specific target request; Strike 3 → bounded choice
    - Assert: After 3rd attempt → record with NEEDS_REFINEMENT tag
    - Assert: Clarification questions use progressive refinement pattern
  - *Verify:* Test passes; clarification_counts incremented correctly; persona voice maintained

- [x] **Task 6.7:** Persona behavior test: Scope boundary enforcement
  - *Ref:* Persona Directives #12-14, Task 3.11
  - *Details:*
    - Input: "Use PostgreSQL as the database"
    - Assert: Captured as Technical Constraint; redirect message includes "What problem does this solve?"
    - Input: "Show me the wireframe"
    - Assert: Deflected; response asks about outcome
    - Input: "This is the most important feature"
    - Assert: Resisted; response focuses on capture-first approach
  - *Verify:* All scope boundaries enforced with helpful, non-judgmental framing

- [x] **Task 6.8:** Persona behavior test: Layered questioning progression
  - *Ref:* Persona Directive #2, Task 3.2
  - *Details:*
    - Start topic: "User Roles"
    - Assert: First question is broad/open-ended ("Tell me about...")
    - Provide detailed answer
    - Assert: Follow-up is hypothesis-driven ("You mentioned X, what about Y?")
    - Provide brief answer
    - Assert: Next question provides scaffolding/examples
  - *Verify:* Question complexity adapts to user response patterns

- [x] **Task 6.9:** Persona behavior test: Progress transparency
  - *Ref:* Persona Directives #16, #15
  - *Details:*
    - Cover multiple topics
    - Assert: Periodic breadcrumbs appear ("We've covered X, Y. Let's discuss Z...")
    - Cover all standard domains
    - Assert: Completion suggestion appears with clear choices
  - *Verify:* User always has visibility into session progress and next steps

- [x] **Task 6.10:** Persona tone consistency test
  - *Ref:* Plan Section 2.2, Persona Section 3
  - *Details:*
    - Run full session with varied interactions
    - Assert: No judgmental language ("You forgot", "That's wrong")
    - Assert: Encouraging phrases present ("That's helpful", "Good starting point")
    - Assert: Neutral conflict framing ("I notice..." not "This contradicts...")
    - Assert: Action-oriented closings on all AI messages
  - *Verify:* Consistent persona voice maintained across all interaction types

---

## Phase 7: Polish & Documentation

- [x] **Task 6.1:** Unit test: Three-Strike Rule logic
  - *Ref:* Plan Section 4.4, Spec Clarification
  - *Details:*
    - Simulate 3 consecutive vague inputs for same topic
    - Assert: First 2 → clarification request; 3rd → record with NEEDS_REFINEMENT
  - *Verify:* Test passes; clarification_counts incremented correctly

- [x] **Task 6.2:** Unit test: Conflict detection logic
  - *Ref:* Plan Section 4.4, Spec Clarification
  - *Details:*
    - Input: "Access must be public" then "Access requires VPN"
    - Assert: Both recorded with CONFLICT tag
  - *Verify:* Test passes; both requirements present with tags

- [x] **Task 6.3:** Unit test: Risk warning flow
  - *Ref:* Plan Section 4.4, Spec Section 6
  - *Details:*
    - Input: "No password hashing"
    - Assert: Warning emitted; not recorded until user confirms
    - Input: "Proceed anyway"
    - Assert: Recorded with RISK_ACCEPTED tag
  - *Verify:* Test passes; risk flow works correctly

- [x] **Task 6.4:** Integration test: Document analysis flow
  - *Ref:* Spec Goal 2, Plan Section 3.3
  - *Details:*
    - Upload sample document
    - Confirm relevance
    - Assert: Requirements extracted; source field set correctly
  - *Verify:* End-to-end document flow works

- [x] **Task 6.5:** Integration test: Full interview flow
  - *Ref:* Spec Section 4, Plan Section 3.2
  - *Details:*
    - Start session → Select interactive mode → Answer questions → Request output
    - Assert: Requirements captured; gap analysis adds domains; output formatted correctly
  - *Verify:* Full interview cycle completes successfully

- [x] **Task 6.6:** Integration test: Output generation format
  - *Ref:* Spec Step 6, Plan Section 4.8
  - *Details:*
    - Capture mix of requirements with various tags
    - Request output
    - Assert: Markdown format matches spec; all categories and tags present
  - *Verify:* Output is valid Markdown; copy-pasteable

---

## Phase 7: Polish & Documentation

- [x] **Task 7.1:** Add error handling for LLM failures
  - *Ref:* Spec Section 6 (Fallback Strategy)
  - *Details:*
    - Wrap LLM calls in try/except
    - Graceful fallback messages
  - *Verify:* Agent doesn't crash on API errors

- [x] **Task 7.2:** Update agent greeting to use "Forge Requirements Assistant" name
  - *Ref:* Spec Section 1 (Agent Name)
  - *Details:*
    - Verify initializer uses correct name
    - Verify Streamlit title matches
  - *Verify:* Consistent branding throughout

- [x] **Task 7.3:** Create README for agent usage
  - *Ref:* N/A
  - *Details:*
    - Setup instructions
    - Environment variables (OPENAI_API_KEY)
    - Running the Streamlit app
    - Example conversation
  - *Verify:* New user can run agent following README

---

## Coverage Checklist

### Persona Behavioral Directives Mapped to Tasks
| Directive # | Behavior | Implementing Tasks |
|-------------|----------|-----------------|
| 1 | Proactively identify gaps | 3.7, 6.9 |
| 2 | Use layered questioning | 3.2, 6.8 |
| 3 | Paraphrase complex statements | 3.3 |
| 4 | Maintain append-only discipline | 3.3, 3.4 |
| 5 | Track coverage systematically | 3.7, 6.9 |
| 6 | Apply three-strike vagueness rule | 3.6, 6.1 |
| 7 | Flag conflicts without forcing resolution | 3.4, 6.2 |
| 8 | Warn responsibly about risks | 3.5, 6.3 |
| 9 | Validate document relevance | 3.8 |
| 10 | Extract atomically | 3.9 |
| 11 | Attribute sources clearly | 3.3, 3.9 |
| 12-14 | Redirect/deflect/resist out-of-scope | 3.11, 6.7 |
| 15 | Suggest completion check | 3.2, 6.9 |
| 16 | Provide progress breadcrumbs | 3.2, 6.9 |
| 17 | Generate output only on request | 4.1 |

### Spec Goals Mapped to Tasks
| Spec Goal | Implementing Tasks |
|-----------|-------------------|
| Conduct interactive Q&A sessions | 3.1, 3.2, 3.3, 4.1-4.5, 6.5 |
| Analyze uploaded documents | 2.1, 3.8, 3.9, 5.4, 6.4 |
| Identify unexplored areas | 3.7, 6.5 |
| Classify requirements | 2.3, 3.3 |
| Capture technical constraints | 3.3 |
| Produce Raw Requirements Dump | 3.10, 6.6 |

### Spec Non-Goals Enforced
| Non-Goal | Enforcement |
|----------|-------------|
| No system architecture design | Prompt templates exclude architecture |
| No code writing | Prompt templates exclude code |
| No UI mockups | Not implemented |
| No PRD structure | Output is "raw" format only |
| No requirement deletion | Append-only in Task 3.3 |

### Guardrails Mapped to Tasks
| Guardrail | Implementing Tasks |
|-----------|-------------------|
| Three-Strike Rule | 3.6, 6.1 |
| Conflict detection | 3.4, 6.2 |
| Risk warnings | 3.5, 6.3 |
| Append-only | 3.3 (state mutation pattern) |
| User-requested output | 4.1 (router pattern match) |
