# Tasks: Forge Requirements Builder

**Spec Reference:** [NETWORK-SPEC.md](./NETWORK-SPEC.md)  
**Plan Reference:** [plan.md](./plan.md)  
**Status:** Ready for Implementation  
**Date:** December 21, 2025

---

## Phase 1: Foundation & Project Setup

### 1.1 Environment & Dependencies

- [x] **Task 1.1.1:** Set up Python virtual environment with Python 3.10+
  - *Ref:* Plan Section 1 (Tech Stack Selection)
  - *Verify:* Run `python --version` in venv, confirm ≥3.10

- [x] **Task 1.1.2:** Install core dependencies (LangGraph, Pydantic v2, OpenAI SDK)
  - *Ref:* Plan Section 1 (Tech Stack Table)
  - *Verify:* Run `pip freeze | grep -E "langgraph|pydantic|openai"`, confirm all present

- [x] **Task 1.1.3:** Install UI/API dependencies (Streamlit, FastAPI, python-dotenv)
  - *Ref:* Plan Section 1 (Tech Stack Table)
  - *Verify:* Run `streamlit --version`, confirm successful execution

- [x] **Task 1.1.4:** Install testing dependencies (pytest, pytest-asyncio)
  - *Ref:* Plan Section 9 (Testing Strategy)
  - *Verify:* Run `pytest --version`, confirm installation

- [x] **Task 1.1.5:** Create project directory structure
  - *Ref:* Plan Section 8 (Implementation Roadmap)
  - *Verify:* Directories exist: `src/`, `tests/`, `projects/`, `config/`

- [x] **Task 1.1.6:** Configure environment variables (.env file with OPENAI_API_KEY)
  - *Ref:* Plan Section 11 (Configuration & Environment)
  - *Verify:* Load .env and access `OPENAI_API_KEY` without error

### 1.2 State Schema Implementation

- [x] **Task 1.2.1:** Create Pydantic models for domain objects (RequirementRaw, UserStory, QualityIssue)
  - *Ref:* Plan Section 2.1 (Core State Structure)
  - *Verify:* Instantiate each model with valid data, confirm Field constraints enforced

- [x] **Task 1.2.2:** Create Pydantic models for AcknowledgedRisk and PrioritizedRequirement
  - *Ref:* Plan Section 2.1 (Core State Structure)
  - *Verify:* Validate all fields match plan specification

- [x] **Task 1.2.3:** Implement ForgeRequirementsState TypedDict with all 18 fields
  - *Ref:* Plan Section 2.1 (Shared workflow state)
  - *Verify:* TypedDict includes all fields: project_id, project_name, user_context, created_at, discovery_complete, requirements_raw, user_stories, quality_issues, quality_issues_resolved, acknowledged_risks, prioritized_backlog, workflow_phase, current_agent, conversation_history, user_preferences, final_deliverable, synthesis_complete, requirements_formal

- [x] **Task 1.2.4:** Implement state initialization function (create_project_state)
  - *Ref:* Plan Section 2.2 (State Mutation Rules)
  - *Verify:* Call with project_name and context, confirm all fields properly initialized

- [x] **Task 1.2.5:** Implement state serialization/deserialization (for persistence)
  - *Ref:* Plan Section 7.3 (Persistence)
  - *Verify:* Serialize state to JSON, deserialize back, confirm equality

### 1.3 Shared Utilities

- [x] **Task 1.3.1:** Implement content type detection function (detect_content_type)
  - *Ref:* Plan Section 4.1 (Orchestrator Node) - Smart phase detection
  - *Verify:* Test with user stories, requirements, raw ideas; confirm correct classification

- [x] **Task 1.3.2:** Implement conversation history manager (add_message, get_context)
  - *Ref:* Plan Section 2.1 (conversation_history field)
  - *Verify:* Add messages, retrieve last N messages, confirm chronological order

- [x] **Task 1.3.3:** Create logging configuration (structured logging with project_id context)
  - *Ref:* Plan Section 11 (LOG_LEVEL configuration)
  - *Verify:* Log messages include project_id, timestamp, log level

- [x] **Task 1.3.4:** Implement error handling utilities (retry decorator, fallback patterns)
  - *Ref:* Plan Section 13 (Known Constraints & Mitigations)
  - *Verify:* Test retry on transient failure, confirm exponential backoff

---

## Phase 2: Tools Implementation

### 2.1 Discovery Agent Tools

- [x] **Task 2.1.1:** Implement extract_from_document tool function
  - *Ref:* Plan Section 5.1 (Discovery Agent Tools JSON schema)
  - *Verify:* Parse sample document (PDF/TXT/DOCX), extract requirements list with metadata

- [x] **Task 2.1.2:** Create document parser for PDF files (pypdf or pdfplumber)
  - *Ref:* Plan Section 7.1 (Accept: PDF, .txt, .docx)
  - *Verify:* Extract text from multi-page PDF, confirm formatting preserved

- [x] **Task 2.1.3:** Create document parser for DOCX files (python-docx)
  - *Ref:* Plan Section 7.1 (Accept: PDF, .txt, .docx)
  - *Verify:* Extract text from .docx with headers and lists, confirm structure retained

- [x] **Task 2.1.4:** Implement validate_requirement_capture tool function
  - *Ref:* Plan Section 5.1 (Discovery Agent Tools JSON schema)
  - *Verify:* Pass incomplete requirement → returns validation_passed=False + missing_fields list

### 2.2 Authoring Agent Tools

- [x] **Task 2.2.1:** Implement validate_user_story tool function
  - *Ref:* Plan Section 5.2 (Authoring Agent Tools JSON schema)
  - *Verify:* Pass malformed user story → returns is_valid=False + improvement_suggestions

- [x] **Task 2.2.2:** Create user story template formatter
  - *Ref:* Plan Section 4.3 (Authoring Node - "As a [role], I want [feature]...")
  - *Verify:* Format story with role/feature/benefit, confirm proper structure

- [x] **Task 2.2.3:** Implement acceptance criteria validator
  - *Ref:* Plan Section 2.1 (UserStory.acceptance_criteria)
  - *Verify:* Check criteria are testable (contains verbs like "can", "should", "displays")

### 2.3 Quality Agent Tools

- [x] **Task 2.3.1:** Implement validate_requirements_quality tool function
  - *Ref:* Plan Section 5.2 (Quality Agent Tools JSON schema)
  - *Verify:* Pass ambiguous requirement → returns issues_found with category=Ambiguity

- [x] **Task 2.3.2:** Create ambiguity detection logic
  - *Ref:* Plan Section 4.4 (Quality Node - 4-dimension validation)
  - *Verify:* Detect vague terms ("user-friendly", "fast"), return ambiguity issues

- [x] **Task 2.3.3:** Create completeness checker
  - *Ref:* Plan Section 4.4 (Quality Node - 4-dimension validation)
  - *Verify:* Identify missing fields (no acceptance criteria, no description)

- [x] **Task 2.3.4:** Create consistency validator (cross-reference requirements)
  - *Ref:* Plan Section 4.4 (Quality Node - 4-dimension validation)
  - *Verify:* Detect conflicting requirements, return inconsistency issues

- [x] **Task 2.3.5:** Create testability checker
  - *Ref:* Plan Section 4.4 (Quality Node - 4-dimension validation)
  - *Verify:* Flag untestable requirements (no measurable criteria)

### 2.4 Prioritization Agent Tools

- [x] **Task 2.4.1:** Implement apply_prioritization_framework tool function
  - *Ref:* Plan Section 5.3 (Prioritization Agent Tools JSON schema)
  - *Verify:* Apply MoSCoW framework, return ranked requirements with rationale

- [x] **Task 2.4.2:** Implement RICE scoring calculator
  - *Ref:* Plan Section 4.5 (Prioritization Node - RICE framework)
  - *Verify:* Calculate RICE score = (Reach × Impact × Confidence) / Effort

- [x] **Task 2.4.3:** Implement MoSCoW categorization logic
  - *Ref:* Plan Section 4.5 (Prioritization Node - MoSCoW framework)
  - *Verify:* Categorize requirements into Must/Should/Could/Won't

- [x] **Task 2.4.4:** Implement Kano model classifier
  - *Ref:* Plan Section 4.5 (Prioritization Node - Kano framework)
  - *Verify:* Classify requirements as Must-haves/Performance/Delighters

- [x] **Task 2.4.5:** Implement Value-Effort matrix scorer
  - *Ref:* Plan Section 4.5 (Prioritization Node - Value-Effort framework)
  - *Verify:* Score requirements on 2-axis grid, recommend high-value/low-effort first

- [x] **Task 2.4.6:** Implement dependency graph analyzer
  - *Ref:* Plan Section 2.1 (PrioritizedRequirement.dependencies)
  - *Verify:* Detect circular dependencies, return topologically sorted order

---

## Phase 3: Nodes Implementation

### 3.1 Orchestrator Node

- [x] **Task 3.1.1:** Implement orchestrator_node function skeleton
  - *Ref:* Plan Section 4.1 (Orchestrator Node specification)
  - *Verify:* Accept ForgeRequirementsState, return updated state with routing decision

- [x] **Task 3.1.2:** Implement smart phase detection logic
  - *Ref:* Plan Section 4.1 (Smart Phase Detection with content-type detection)
  - *Verify:* Upload user stories → suggests "Quality", upload requirements → suggests "Authoring"

- [x] **Task 3.1.3:** Implement phase progression approval workflow
  - *Ref:* Plan Section 6 (Decision Authority Matrix - Phase progression: User Approval Required)
  - *Verify:* Orchestrator suggests phase, waits for user confirmation before proceeding

- [x] **Task 3.1.4:** Implement user interruption handling
  - *Ref:* NETWORK-SPEC Section 2.2 (Orchestrator - Dynamic Routing)
  - *Verify:* User says "stop, refine current phase" → pauses workflow, returns to current agent

- [x] **Task 3.1.5:** Implement explicit phase skip logic
  - *Ref:* Plan Section 4.1 (User can request "Skip to Prioritization")
  - *Verify:* User requests skip → validates prerequisites, moves to requested phase

- [x] **Task 3.1.6:** Create orchestrator system prompt (project-oriented, progress-focused)
  - *Ref:* NETWORK-SPEC Section 2.4 (Supervisor Persona & Voice)
  - *Verify:* Prompt includes progress metrics, avoids agent jargon, emphasizes outcomes

- [x] **Task 3.1.7:** Implement agent failure fallback logic
  - *Ref:* Plan Section 4.1 (Error handling with retry/fallback)
  - *Verify:* Agent times out → retry once → escalate to user with options

### 3.2 Discovery Agent Node

- [x] **Task 3.2.1:** Implement discovery_node function skeleton
  - *Ref:* Plan Section 4.2 (Discovery Node specification)
  - *Verify:* Accept state, return state with requirements_raw populated

- [x] **Task 3.2.2:** Create discovery agent system prompt (warm, curious interviewer)
  - *Ref:* NETWORK-SPEC Section 3.1 (Discovery Agent Persona - Curious and probing)
  - *Verify:* Prompt asks "why?" questions, probes for implicit requirements, uses plain language

- [x] **Task 3.2.3:** Implement interactive Q&A loop for requirement elicitation
  - *Ref:* Plan Section 4.2 (Discovery Node - Logic step 2: Ask questions)
  - *Verify:* Agent asks follow-up questions until user says "done" or coverage complete

- [x] **Task 3.2.4:** Implement gap identification logic
  - *Ref:* NETWORK-SPEC Section 3.1 (Discovery Agent - Goal: Probe for implicit requirements)
  - *Verify:* Agent detects missing areas (e.g., no security requirements mentioned), asks targeted questions

- [x] **Task 3.2.5:** Implement requirement capture and metadata tagging
  - *Ref:* Plan Section 4.2 (Discovery Node - Output: requirements_raw with type, source)
  - *Verify:* Each captured requirement has id, title, description, type, source fields

- [x] **Task 3.2.6:** Implement discovery completion criteria
  - *Ref:* Plan Section 4.2 (Discovery Node - Set discovery_complete = True)
  - *Verify:* User confirms "done" OR 3 consecutive clarifications without new requirements → mark complete

### 3.3 Authoring Agent Node

- [x] **Task 3.3.1:** Implement authoring_node function skeleton
  - *Ref:* Plan Section 4.3 (Authoring Node specification)
  - *Verify:* Accept state with requirements_raw, return state with user_stories populated

- [x] **Task 3.3.2:** Create authoring agent system prompt (story craftsperson, INVEST-aware)
  - *Ref:* Plan Section 4.3 (Authoring Node - System Prompt example)
  - *Verify:* Prompt emphasizes Independent, Negotiable, Valuable, Estimable, Small, Testable principles

- [x] **Task 3.3.3:** Implement requirement-to-story transformation logic
  - *Ref:* Plan Section 4.3 (Authoring Node - Logic step 1: Create user story)
  - *Verify:* Transform requirement into "As a [role], I want [feature] so that [benefit]" format

- [x] **Task 3.3.4:** Implement acceptance criteria generation
  - *Ref:* Plan Section 4.3 (Authoring Node - Logic step 2: Define acceptance criteria)
  - *Verify:* Generate 3-5 testable criteria per story with Given/When/Then structure

- [x] **Task 3.3.5:** Implement edge case identification
  - *Ref:* Plan Section 4.3 (Authoring Node - Logic step 3: Add edge cases)
  - *Verify:* Identify error scenarios, boundary conditions, negative cases per story

- [x] **Task 3.3.6:** Implement definition of done checklist generation
  - *Ref:* Plan Section 4.3 (Authoring Node - Logic step 4: Suggest DoD items)
  - *Verify:* Generate DoD with code review, tests, documentation items

- [x] **Task 3.3.7:** Implement effort estimation (XS/S/M/L/XL sizing)
  - *Ref:* Plan Section 4.3 (Authoring Node - Logic step 5: Estimate effort)
  - *Verify:* Assign size based on complexity, scope, unknowns

### 3.4 Quality Agent Node

- [x] **Task 3.4.1:** Implement quality_node function skeleton
  - *Ref:* Plan Section 4.4 (Quality Node specification)
  - *Verify:* Accept state, return state with quality_issues populated

- [x] **Task 3.4.2:** Create quality agent system prompt (objective validator, pragmatic)
  - *Ref:* Plan Section 4.4 (Quality Node - System Prompt example)
  - *Verify:* Prompt emphasizes pragmatic validation, allows risk acknowledgment

- [x] **Task 3.4.3:** Implement 4-dimension validation (ambiguity, completeness, consistency, testability)
  - *Ref:* Plan Section 4.4 (Quality Node - Logic step 1: Run 4-dimension check)
  - *Verify:* All dimensions checked, issues categorized correctly

- [x] **Task 3.4.4:** Implement issue severity classification (Critical/High/Medium/Low)
  - *Ref:* Plan Section 2.1 (QualityIssue.severity)
  - *Verify:* Critical = blocks development, High = significant risk, Medium/Low appropriately classified

- [x] **Task 3.4.5:** Implement recommended fix generation for each issue
  - *Ref:* Plan Section 2.1 (QualityIssue.recommended_fix)
  - *Verify:* Each issue has actionable fix suggestion

- [x] **Task 3.4.6:** Implement pragmatic quality gate (allow risk acknowledgment)
  - *Ref:* Plan Section 4.4 (Quality Node - Logic step 2: Present findings with user choice)
  - *Verify:* User can choose "acknowledge risks and proceed", issues moved to acknowledged_risks

- [x] **Task 3.4.7:** Implement quality completion criteria
  - *Ref:* Plan Section 4.4 (Quality Node - Set quality_issues_resolved = True)
  - *Verify:* All issues resolved OR acknowledged → mark complete

### 3.5 Prioritization Agent Node

- [x] **Task 3.5.1:** Implement prioritization_node function skeleton
  - *Ref:* Plan Section 4.5 (Prioritization Node specification)
  - *Verify:* Accept state, return state with prioritized_backlog populated

- [x] **Task 3.5.2:** Create prioritization agent system prompt (analytical strategist)
  - *Ref:* Plan Section 4.5 (Prioritization Node - System Prompt example)
  - *Verify:* Prompt includes framework selection logic and analytical tone

- [x] **Task 3.5.3:** Implement framework recommendation logic
  - *Ref:* Plan Section 4.5 (Prioritization Node - Framework Selection Logic)
  - *Verify:* Recommend RICE for roadmaps, MoSCoW for negotiation, Kano for value, Value-Effort for constraints

- [x] **Task 3.5.4:** Implement scoring input gathering workflow
  - *Ref:* Plan Section 4.5 (Prioritization Node - Step 3: Gather scoring inputs)
  - *Verify:* Agent asks for framework-specific inputs (reach, impact, confidence, effort for RICE)

- [x] **Task 3.5.5:** Implement ranking algorithm based on framework scores
  - *Ref:* Plan Section 4.5 (Prioritization Node - Step 4: Apply framework to rank)
  - *Verify:* Requirements ranked 1-N with clear ordering

- [x] **Task 3.5.6:** Implement dependency analysis and sequencing
  - *Ref:* Plan Section 4.5 (Prioritization Node - Step 5: Identify dependencies)
  - *Verify:* Prerequisites listed, implementation order respects dependencies

- [x] **Task 3.5.7:** Implement MVP vs. Phase 2 breakdown
  - *Ref:* Plan Section 4.5 (Prioritization Node - Step 6: Suggest phase breakdown)
  - *Verify:* Requirements categorized into Phase 1 (MVP) / Phase 2 / Backlog / Future

- [x] **Task 3.5.8:** Implement rationale generation for each ranking decision
  - *Ref:* Plan Section 2.1 (PrioritizedRequirement.rationale)
  - *Verify:* Each requirement has clear explanation for its rank

### 3.6 Synthesis Node

- [x] **Task 3.6.1:** Implement synthesis_node function skeleton
  - *Ref:* Plan Section 4.6 (Synthesis Node specification)
  - *Verify:* Accept state, return state with final_deliverable populated

- [x] **Task 3.6.2:** Implement completeness validator
  - *Ref:* Plan Section 4.6 (Synthesis Node - Logic step 1: Validate completeness)
  - *Verify:* Check all phases complete, all required sections have content

- [x] **Task 3.6.3:** Implement cross-reference validator (stories ↔ requirements ↔ tests)
  - *Ref:* Plan Section 4.6 (Synthesis Node - Logic step 2: Cross-reference)
  - *Verify:* Every requirement has story, every story has acceptance criteria

- [x] **Task 3.6.4:** Implement Section 1 generator (Executive Summary & Overview)
  - *Ref:* Plan Section 4.6 (10-section structure - Section 1)
  - *Verify:* Section includes project context, goals, stakeholders summary

- [x] **Task 3.6.5:** Implement Section 2 generator (User Scenarios & Workflows)
  - *Ref:* Plan Section 4.6 (10-section structure - Section 2)
  - *Verify:* Section includes key user journeys and workflow diagrams

- [x] **Task 3.6.6:** Implement Section 3 generator (Requirements Master List)
  - *Ref:* Plan Section 4.6 (10-section structure - Section 3)
  - *Verify:* Section lists all requirements with IDs, titles, types

- [x] **Task 3.6.7:** Implement Section 4 generator (User Stories & Acceptance Criteria)
  - *Ref:* Plan Section 4.6 (10-section structure - Section 4)
  - *Verify:* Section includes all stories with acceptance criteria and DoD

- [x] **Task 3.6.8:** Implement Section 5 generator (Functional Requirements Detailed)
  - *Ref:* Plan Section 4.6 (10-section structure - Section 5)
  - *Verify:* Section expands on functional requirements with detailed descriptions

- [x] **Task 3.6.9:** Implement Section 6 generator (Non-Functional Requirements)
  - *Ref:* Plan Section 4.6 (10-section structure - Section 6)
  - *Verify:* Section includes performance, security, scalability, usability requirements

- [x] **Task 3.6.10:** Implement Section 7 generator (Data Model & Entities)
  - *Ref:* Plan Section 4.6 (10-section structure - Section 7)
  - *Verify:* Section documents key entities, relationships, attributes

- [x] **Task 3.6.11:** Implement Section 8 generator (Testing Strategy & Edge Cases)
  - *Ref:* Plan Section 4.6 (10-section structure - Section 8)
  - *Verify:* Section includes test approach, edge cases from authoring phase

- [x] **Task 3.6.12:** Implement Section 9 generator (Success Criteria & Measurable Outcomes)
  - *Ref:* Plan Section 4.6 (10-section structure - Section 9)
  - *Verify:* Section lists KPIs, success metrics, acceptance thresholds

- [x] **Task 3.6.13:** Implement Section 10 generator (Appendices with Acknowledged Risks)
  - *Ref:* Plan Section 4.6 (10-section structure - Section 10)
  - *Verify:* Section includes assumptions, constraints, risks, acknowledged risks, glossary

- [x] **Task 3.6.14:** Implement markdown document assembly
  - *Ref:* Plan Section 4.6 (Synthesis Node - Logic step 3: Assemble into 10-section structure)
  - *Verify:* All sections combined into properly formatted markdown with table of contents

- [x] **Task 3.6.15:** Implement journey summary generator
  - *Ref:* Plan Section 4.6 (Synthesis Node - Logic step 4: Provide summary of journey)
  - *Verify:* Summary includes phases completed, total requirements, stories, issues resolved

---

## Phase 4: Graph Assembly & Routing

### 4.1 LangGraph Configuration

- [x] **Task 4.1.1:** Initialize LangGraph StateGraph with ForgeRequirementsState schema
  - *Ref:* Plan Section 3 (LangGraph Architecture)
  - *Verify:* Create StateGraph instance, verify state schema accepted

- [x] **Task 4.1.2:** Add all 6 nodes to the graph (orchestrator, discovery, authoring, quality, prioritization, synthesis)
  - *Ref:* Plan Section 4 (Node Specifications)
  - *Verify:* Call graph.add_node() for each, verify no duplicate names

- [x] **Task 4.1.3:** Set entry point to orchestrator_node
  - *Ref:* Plan Section 3 (Architecture - Orchestrator as entry point)
  - *Verify:* graph.set_entry_point("orchestrator"), verify routing starts there

### 4.2 Edge Definitions

- [x] **Task 4.2.1:** Add conditional edge from orchestrator to all specialized agents
  - *Ref:* Plan Section 3 (Routing Logic - Orchestrator routes to appropriate agent)
  - *Verify:* Conditional edge routes to discovery/authoring/quality/prioritization/synthesis based on state

- [x] **Task 4.2.2:** Add edge from discovery back to orchestrator
  - *Ref:* Plan Section 3 (Architecture - Agents return to Orchestrator)
  - *Verify:* After discovery_complete, control returns to orchestrator

- [x] **Task 4.2.3:** Add edge from authoring back to orchestrator
  - *Ref:* Plan Section 3 (Architecture - Agents return to Orchestrator)
  - *Verify:* After authoring_complete, control returns to orchestrator

- [x] **Task 4.2.4:** Add edge from quality back to orchestrator
  - *Ref:* Plan Section 3 (Architecture - Agents return to Orchestrator)
  - *Verify:* After quality_issues_resolved, control returns to orchestrator

- [x] **Task 4.2.5:** Add edge from prioritization back to orchestrator
  - *Ref:* Plan Section 3 (Architecture - Agents return to Orchestrator)
  - *Verify:* After prioritization_complete, control returns to orchestrator

- [x] **Task 4.2.6:** Add edge from synthesis to END
  - *Ref:* Plan Section 3 (Architecture - Synthesis produces final deliverable, workflow complete)
  - *Verify:* After synthesis_complete, graph terminates

### 4.3 Routing Logic Implementation

- [x] **Task 4.3.1:** Implement route_next function for conditional routing
  - *Ref:* Plan Section 3 (Routing Logic based on workflow_phase)
  - *Verify:* Returns correct next node name based on state conditions

- [x] **Task 4.3.2:** Implement discovery routing condition
  - *Ref:* Plan Section 3 (Route to discovery when: new project OR user requests discovery)
  - *Verify:* State with discovery_complete=False → routes to discovery

- [x] **Task 4.3.3:** Implement authoring routing condition
  - *Ref:* Plan Section 3 (Route to authoring when: discovery complete AND user stories empty)
  - *Verify:* State with discovery_complete=True, user_stories=[] → routes to authoring

- [x] **Task 4.3.4:** Implement quality routing condition
  - *Ref:* Plan Section 3 (Route to quality when: authoring complete OR user requests quality check)
  - *Verify:* State with authoring_complete=True → routes to quality

- [x] **Task 4.3.5:** Implement prioritization routing condition
  - *Ref:* Plan Section 3 (Route to prioritization when: quality complete)
  - *Verify:* State with quality_issues_resolved=True → routes to prioritization

- [x] **Task 4.3.6:** Implement synthesis routing condition
  - *Ref:* Plan Section 3 (Route to synthesis when: prioritization complete)
  - *Verify:* State with prioritization_complete=True → routes to synthesis

- [x] **Task 4.3.7:** Implement user interrupt routing
  - *Ref:* Plan Section 4.1 (Orchestrator handles user interruptions)
  - *Verify:* User sends "stop" or "refine" → pause workflow, stay in current phase

### 4.4 Graph Compilation

- [x] **Task 4.4.1:** Compile LangGraph with interrupt_before for checkpoints
  - *Ref:* Plan Section 3 (Human-in-the-loop at phase boundaries)
  - *Verify:* Compile with interrupt_before=["authoring", "quality", "prioritization", "synthesis"]

- [x] **Task 4.4.2:** Test graph compilation and validate no circular dependencies
  - *Ref:* Plan Section 4 (Ensure proper routing)
  - *Verify:* Compile succeeds, visualize graph, confirm no cycles

- [x] **Task 4.4.3:** Create graph visualization utility
  - *Ref:* Plan Section 3 (LangGraph native visualization)
  - *Verify:* Generate graph diagram showing all nodes and edges

---

## Phase 5: Testing & Validation

### 5.1 Unit Tests - State & Utilities

- [x] **Task 5.1.1:** Write unit test for state initialization
  - *Ref:* Plan Section 9.1 (Unit Tests)
  - *Verify:* Test create_project_state() with various inputs

- [x] **Task 5.1.2:** Write unit test for content type detection
  - *Ref:* Plan Section 9.1 (test_detect_content_type example)
  - *Verify:* Test with user stories, requirements, raw ideas; assert correct classification

- [x] **Task 5.1.3:** Write unit test for state serialization/deserialization
  - *Ref:* Plan Section 7.3 (Persistence functions)
  - *Verify:* Serialize → deserialize → assert equality

- [x] **Task 5.1.4:** Write unit test for conversation history manager
  - *Ref:* Plan Section 2.1 (conversation_history field)
  - *Verify:* Add messages, retrieve context, assert correct order

### 5.2 Unit Tests - Tools

- [x] **Task 5.2.1:** Write unit test for extract_from_document tool
  - *Ref:* Plan Section 9.1 (test_extract_requirements_from_document example)
  - *Verify:* Pass sample document, assert requirements extracted with correct types

- [x] **Task 5.2.2:** Write unit test for validate_user_story tool
  - *Ref:* Plan Section 5.2 (Authoring Agent Tools)
  - *Verify:* Pass malformed story, assert validation fails with suggestions

- [x] **Task 5.2.3:** Write unit test for validate_requirements_quality tool
  - *Ref:* Plan Section 5.2 (Quality Agent Tools)
  - *Verify:* Pass ambiguous requirement, assert ambiguity issue detected

- [x] **Task 5.2.4:** Write unit test for apply_prioritization_framework tool (RICE)
  - *Ref:* Plan Section 5.3 (Prioritization Agent Tools)
  - *Verify:* Calculate RICE scores, assert correct ranking

- [x] **Task 5.2.5:** Write unit test for apply_prioritization_framework tool (MoSCoW)
  - *Ref:* Plan Section 5.3 (Prioritization Agent Tools)
  - *Verify:* Categorize requirements, assert Must/Should/Could/Won't assignments

### 5.3 Unit Tests - Nodes

- [x] **Task 5.3.1:** Write unit test for discovery_node (basic requirement capture)
  - *Ref:* Plan Section 9.1 (Unit Tests - Node Level)
  - *Verify:* Run with user input, assert requirements_raw populated, discovery_complete=True

- [x] **Task 5.3.2:** Write unit test for authoring_node (story generation)
  - *Ref:* Plan Section 9.2 (Integration Tests)
  - *Verify:* Run with requirements_raw, assert user_stories generated with acceptance criteria

- [x] **Task 5.3.3:** Write unit test for quality_node (issue detection)
  - *Ref:* Plan Section 4.4 (Quality Node)
  - *Verify:* Run with flawed requirements, assert quality_issues populated with correct categories

- [x] **Task 5.3.4:** Write unit test for prioritization_node (ranking)
  - *Ref:* Plan Section 4.5 (Prioritization Node)
  - *Verify:* Run with requirements and framework, assert prioritized_backlog ranked correctly

- [x] **Task 5.3.5:** Write unit test for synthesis_node (document generation)
  - *Ref:* Plan Section 4.6 (Synthesis Node)
  - *Verify:* Run with complete state, assert final_deliverable contains all 10 sections

- [x] **Task 5.3.6:** Write unit test for orchestrator_node (routing decisions)
  - *Ref:* Plan Section 4.1 (Orchestrator Node)
  - *Verify:* Test various state conditions, assert correct routing decisions

### 5.4 Integration Tests - Phase-to-Phase

- [x] **Task 5.4.1:** Write integration test for Discovery → Authoring transition
  - *Ref:* Plan Section 9.2 (test_discovery_to_authoring example)
  - *Verify:* Run discovery, then authoring; assert state properly handed off

- [x] **Task 5.4.2:** Write integration test for Authoring → Quality transition
  - *Ref:* Plan Section 9.2 (Integration Tests - Phase-to-Phase)
  - *Verify:* Run authoring, then quality; assert quality checks all stories

- [x] **Task 5.4.3:** Write integration test for Quality → Prioritization transition
  - *Ref:* Plan Section 9.2 (Integration Tests - Phase-to-Phase)
  - *Verify:* Resolve quality issues, then prioritize; assert clean handoff

- [x] **Task 5.4.4:** Write integration test for Prioritization → Synthesis transition
  - *Ref:* Plan Section 9.2 (Integration Tests - Phase-to-Phase)
  - *Verify:* Complete prioritization, then synthesize; assert final deliverable generated

- [x] **Task 5.4.5:** Write end-to-end integration test (full workflow)
  - *Ref:* Plan Section 9.2 (Integration Tests)
  - *Verify:* Run complete workflow from raw input to final deliverable

### 5.5 Behavioral Tests - Persona Compliance

- [x] **Task 5.5.1:** Write behavioral test for Discovery Agent warmth
  - *Ref:* Plan Section 9.3 (test_discovery_warmth example)
  - *Verify:* Check agent responses avoid negative words, use encouraging language

- [x] **Task 5.5.2:** Write behavioral test for Quality Agent pragmatism
  - *Ref:* Plan Section 9.3 (test_quality_pragmatism example)
  - *Verify:* Verify agent allows risk acknowledgment, doesn't block on minor issues

- [x] **Task 5.5.3:** Write behavioral test for Orchestrator transparency
  - *Ref:* NETWORK-SPEC Section 2.4 (Supervisor Persona - Transparent)
  - *Verify:* Check orchestrator explicitly names which agent is invoked and why

- [x] **Task 5.5.4:** Write behavioral test for Authoring Agent INVEST principles
  - *Ref:* Plan Section 4.3 (Authoring Node - INVEST-aware)
  - *Verify:* Verify generated stories are Independent, Valuable, Estimable, Small, Testable

- [x] **Task 5.5.5:** Write behavioral test for Prioritization Agent analytical tone
  - *Ref:* Plan Section 4.5 (Prioritization Node - Tone: Analytical, enabling)
  - *Verify:* Check agent provides clear rationale, avoids prescriptive language

### 5.6 Validation Tests - Spec Compliance

- [x] **Task 5.6.1:** Write validation test for all NETWORK-SPEC goals implemented
  - *Ref:* NETWORK-SPEC Section 3 (All agent goals)
  - *Verify:* Checklist of all goals → confirm implementation exists for each

- [x] **Task 5.6.2:** Write validation test for all non-goals enforced
  - *Ref:* NETWORK-SPEC Section 3 (All agent non-goals)
  - *Verify:* Verify agents don't perform prohibited actions (e.g., Discovery doesn't write code)

- [x] **Task 5.6.3:** Write validation test for decision authority matrix compliance
  - *Ref:* Plan Section 6 (Decision Authority Matrix)
  - *Verify:* Test autonomous decisions execute without user approval, recommendations wait for approval

- [x] **Task 5.6.4:** Write validation test for smart phase detection
  - *Ref:* Plan Section 4.1 (Smart Phase Detection)
  - *Verify:* Upload different content types, assert correct phase suggestions

- [x] **Task 5.6.5:** Write validation test for pragmatic quality gates
  - *Ref:* Plan Section 4.4 (Quality Node - Pragmatic approach)
  - *Verify:* User can acknowledge risks and proceed, issues moved to acknowledged_risks

---

## Phase 6: User Interface & Deployment

### 6.1 Streamlit UI

- [x] **Task 6.1.1:** Create main Streamlit app file (streamlit_app.py)
  - *Ref:* Plan Section 10.1 (Deployment - Streamlit app)
  - *Verify:* Run `streamlit run streamlit_app.py`, app launches

- [x] **Task 6.1.2:** Implement chat interface with conversation history
  - *Ref:* Plan Section 7.1 (Chat/Conversational interface)
  - *Verify:* User can type messages, see agent responses in chat format

- [x] **Task 6.1.3:** Implement file upload widget for document analysis
  - *Ref:* Plan Section 7.1 (File Upload - Accept: PDF, .txt, .docx)
  - *Verify:* User uploads file, agent extracts requirements, displays results

- [x] **Task 6.1.4:** Implement progress indicators for phase transitions
  - *Ref:* NETWORK-SPEC Section 1 (User Interaction - Visibility at each handoff)
  - *Verify:* Display "✓ Discovery complete. 47 requirements captured." messages

- [x] **Task 6.1.5:** Implement user checkpoint prompts (approve/refine/skip)
  - *Ref:* Plan Section 4.1 (Phase progression approval workflow)
  - *Verify:* Display buttons: "Proceed to next phase", "Refine current phase", "Skip to phase..."

- [x] **Task 6.1.6:** Implement final deliverable download (markdown, PDF, JSON)
  - *Ref:* Plan Section 7.2 (Output - File download for final deliverable)
  - *Verify:* User clicks download, receives properly formatted file

- [x] **Task 6.1.7:** Add session state management for multi-turn conversations
  - *Ref:* Plan Section 7.3 (Session State - In-Memory)
  - *Verify:* Refresh page, conversation history persists within session

### 6.2 REST API (Optional)

- [ ] **Task 6.2.1:** Create FastAPI application (main.py)
  - *Ref:* Plan Section 7.1 (REST API - Optional)
  - *Verify:* Run API server, health check endpoint returns 200

- [ ] **Task 6.2.2:** Implement POST /project endpoint (create new project)
  - *Ref:* Plan Section 7.1 (REST API - POST `/project`)
  - *Verify:* POST with project_name → returns project_id

- [ ] **Task 6.2.3:** Implement POST /chat endpoint (send message to orchestrator)
  - *Ref:* Plan Section 7.1 (REST API - POST `/chat`)
  - *Verify:* POST message → returns agent response and updated state

- [ ] **Task 6.2.4:** Implement GET /project/{project_id} endpoint (get current state)
  - *Ref:* Plan Section 7.1 (REST API - GET `/project/{project_id}`)
  - *Verify:* GET project_id → returns ForgeRequirementsState JSON

- [ ] **Task 6.2.5:** Implement GET /deliverable/{project_id} endpoint (get final document)
  - *Ref:* Plan Section 7.1 (REST API - GET `/deliverable/{project_id}`)
  - *Verify:* GET project_id → returns final_deliverable markdown

### 6.3 MCP Server Integration (Optional)

- [x] **Task 6.3.1:** Create MCP server wrapper (mcp_server.py)
  - *Ref:* Plan Section 7.2 (MCP Server - Register agents as tools)
  - *Verify:* MCP server starts, exposes endpoints

- [x] **Task 6.3.2:** Register discovery agent as MCP tool
  - *Ref:* Plan Section 7.2 (MCP Server - Expose endpoints: `/discovery`)
  - *Verify:* Call discovery tool via MCP protocol, returns requirements_raw

- [x] **Task 6.3.3:** Register authoring agent as MCP tool
  - *Ref:* Plan Section 7.2 (MCP Server - Expose endpoints: `/authoring`)
  - *Verify:* Call authoring tool via MCP protocol, returns user_stories

- [x] **Task 6.3.4:** Register quality agent as MCP tool
  - *Ref:* Plan Section 7.2 (MCP Server - Expose endpoints: `/quality`)
  - *Verify:* Call quality tool via MCP protocol, returns quality_issues

- [x] **Task 6.3.5:** Register prioritization agent as MCP tool
  - *Ref:* Plan Section 7.2 (MCP Server - Expose endpoints: `/prioritization`)
  - *Verify:* Call prioritization tool via MCP protocol, returns prioritized_backlog

### 6.4 Deployment Configuration

- [x] **Task 6.4.1:** Create Dockerfile for containerized deployment
  - *Ref:* Plan Section 10.3 (Docker Container example)
  - *Verify:* Build image, run container, access Streamlit app

- [ ] **Task 6.4.2:** Configure environment variables for production
  - *Ref:* Plan Section 11 (Configuration - .env file)
  - *Verify:* Set DEPLOYMENT_MODE, confirm app uses production settings

- [x] **Task 6.4.3:** Implement file-based persistence option
  - *Ref:* Plan Section 7.3 (Optional Persistence - save_project_state function)
  - *Verify:* Save state to projects/{project_id}/state.json, reload successfully

- [ ] **Task 6.4.4:** Implement database persistence option (PostgreSQL)
  - *Ref:* Plan Section 7.3 (Optional Persistence - Database with PostgreSQL)
  - *Verify:* Save state to database, query and restore state

- [x] **Task 6.4.5:** Create deployment documentation (README with setup instructions)
  - *Ref:* Plan Section 10 (Deployment Options)
  - *Verify:* Follow README, successfully deploy to each environment

---

## Phase 7: Documentation & Polish

### 7.1 Code Documentation

- [ ] **Task 7.1.1:** Add docstrings to all Pydantic models
  - *Ref:* Plan Section 2.1 (State Schema)
  - *Verify:* Each model has class docstring and field descriptions

- [ ] **Task 7.1.2:** Add docstrings to all node functions
  - *Ref:* Plan Section 4 (Node Specifications)
  - *Verify:* Each node function documents inputs, outputs, behavior

- [ ] **Task 7.1.3:** Add docstrings to all tool functions
  - *Ref:* Plan Section 5 (Tool Schemas)
  - *Verify:* Each tool documents parameters, return values, examples

- [ ] **Task 7.1.4:** Create architecture documentation (architecture.md)
  - *Ref:* Plan Section 3 (LangGraph Architecture)
  - *Verify:* Document includes graph diagram, routing logic, state flow

### 7.2 User Documentation

- [ ] **Task 7.2.1:** Create user guide (USER-GUIDE.md with quickstart)
  - *Ref:* Plan Section 1 (Executive Summary)
  - *Verify:* User can follow guide and complete first workflow

- [ ] **Task 7.2.2:** Create example workflows (examples/ directory with sample projects)
  - *Ref:* NETWORK-SPEC Section 1 (User Interaction Model)
  - *Verify:* Examples cover: new project, skip phases, upload documents

- [ ] **Task 7.2.3:** Create troubleshooting guide (TROUBLESHOOTING.md)
  - *Ref:* Plan Section 13 (Known Constraints & Mitigations)
  - *Verify:* Document common issues and solutions

### 7.3 Developer Documentation

- [ ] **Task 7.3.1:** Create development setup guide (DEVELOPMENT.md)
  - *Ref:* Plan Section 8 (Implementation Roadmap - Phase 1)
  - *Verify:* Developer can set up environment following guide

- [ ] **Task 7.3.2:** Create contribution guidelines (CONTRIBUTING.md)
  - *Ref:* Plan Section 9 (Testing Strategy)
  - *Verify:* Guidelines cover code style, testing requirements, PR process

- [ ] **Task 7.3.3:** Create API documentation (API.md for REST endpoints)
  - *Ref:* Plan Section 7.1 (REST API - Optional)
  - *Verify:* All endpoints documented with examples

---

## Coverage Verification Checklist

### State Fields
- [x] All 18 state fields defined in plan.md implemented
- [x] project_id, project_name, user_context, created_at (metadata)
- [x] discovery_complete, requirements_raw (discovery phase)
- [x] authoring_complete, user_stories (authoring phase)
- [x] quality_complete, quality_issues, quality_issues_resolved, acknowledged_risks, requirements_formal (quality phase)
- [x] prioritization_complete, prioritization_framework, prioritized_backlog (prioritization phase)
- [x] workflow_phase, current_agent, conversation_history, user_preferences (orchestration)
- [x] final_deliverable, synthesis_complete (synthesis phase)

### Tools
- [x] extract_from_document (Discovery Agent)
- [x] validate_requirement_capture (Discovery Agent)
- [x] validate_user_story (Authoring Agent)
- [x] validate_requirements_quality (Quality Agent)
- [x] apply_prioritization_framework (Prioritization Agent)

### Nodes
- [x] Orchestrator node with smart phase detection and routing
- [x] Discovery Agent node with Q&A loop and gap identification
- [x] Authoring Agent node with story transformation and INVEST principles
- [x] Quality Agent node with 4-dimension validation and pragmatic gates
- [x] Prioritization Agent node with framework selection and ranking
- [x] Synthesis node with 10-section document generation

### Edges & Routing
- [x] Conditional routing from Orchestrator to all agents
- [x] Return edges from all agents to Orchestrator
- [x] Synthesis → END edge
- [x] User interruption handling
- [x] Phase skip logic

### Spec Goals (NETWORK-SPEC.md)
- [x] Discovery Agent: Conduct interactive discovery, capture requirements, probe for gaps
- [x] Authoring Agent: Transform requirements into user stories with acceptance criteria
- [x] Quality Agent: Validate requirements on 4 dimensions, allow risk acknowledgment
- [x] Prioritization Agent: Recommend framework, rank requirements, suggest phase breakdown
- [x] Orchestrator: Route tasks, monitor progress, synthesize final deliverable

### Non-Goals Enforcement
- [x] Discovery doesn't organize into stories (Authoring's job)
- [x] Discovery doesn't judge/critique (Quality's job)
- [x] Discovery doesn't assign priorities (Prioritization's job)
- [x] Quality doesn't perfect-block (pragmatic approach)
- [x] No agent writes code or makes business decisions

### Guardrails & Safety
- [x] Pragmatic quality gates implemented (allow risk acknowledgment)
- [x] User checkpoints at phase boundaries
- [x] Smart phase detection with user confirmation
- [x] Explicit escalation for security/compliance risks
- [x] User autonomy respected (can skip, refine, override)

### Testing Coverage
- [x] Unit tests for state management and utilities
- [x] Unit tests for all tools
- [x] Unit tests for all nodes
- [x] Integration tests for phase-to-phase transitions
- [x] End-to-end workflow test
- [x] Behavioral tests for persona compliance
- [x] Validation tests for spec compliance

---

## Implementation Priority Matrix

### Critical Path (Must Complete First)
1. Phase 1: Foundation (state schema, utilities)
2. Phase 2: Tools (all agent tools)
3. Phase 3: Nodes (all 6 nodes)
4. Phase 4: Graph Assembly (routing and edges)
5. Phase 5.1-5.3: Core testing (state, tools, nodes)

### High Priority (Core Functionality)
6. Phase 5.4: Integration testing (phase transitions)
7. Phase 6.1: Streamlit UI (user interface)
8. Phase 7.2: User documentation

### Medium Priority (Enhancement)
9. Phase 5.5-5.6: Behavioral and validation testing
10. Phase 6.3: MCP Server integration
11. Phase 7.1: Code documentation

### Low Priority (Optional/Future)
12. Phase 6.2: REST API
13. Phase 6.4: Database persistence
14. Phase 7.3: Developer documentation

---

**Tasks Document Ready for Development Tracking**  
**Total Tasks:** 200+  
**Estimated Timeline:** 8 weeks (per plan.md roadmap)  
**Next Action:** Begin Phase 1, Task 1.1.1 (Set up Python virtual environment)
