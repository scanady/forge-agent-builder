# Agent Spec: Forge Requirements Builder

**Version:** 1.0.0  
**Agent Type:** Multi-Agent Network / Orchestrated System  
**Status:** Approved  
**Owner:** @scanady  
**Network Size:** 4 specialized agents + 1 supervisor orchestrator

---

## 1. Network Overview

### High-Level Goal
Guides teams through the complete requirements analysis lifecycle—from raw ideas through validated, prioritized, and actionable requirements—using specialized agents to handle discovery, story authoring, quality assurance, and prioritization.

### User Value
Teams struggle to move requirements from chaotic brainstorms to publication-ready, prioritized backlogs. Existing approaches are either too rigid (forms and templates) or too loose (free-form documents). Forge Requirements Builder provides structured guidance while remaining flexible, ensuring comprehensive coverage across all requirements activities without scope creep.

### User Interaction Model
* **Primary Interface:** User submits an initial request or project context to the Orchestrator via chat/API. The Orchestrator manages all subsequent interactions, deciding which specialized agent to engage based on detected workflow state.
* **Visibility:** User sees explicit progress updates at each agent handoff (e.g., "✓ Discovery phase complete. 47 requirements captured. Moving to User Story Authoring..."). Progress includes completion metrics (e.g., "3 of 5 requirements have formal user stories").
* **Iterative & Flexible:** User is not locked into a linear flow. At ANY point after synthesis, user can:
  - Add more requirements (return to Discovery)
  - Refine stories (return to Authoring)
  - Review/resolve issues (return to Quality)
  - Adjust priorities (return to Prioritization)
  - Regenerate document (re-run Synthesis)
  - Finish when satisfied (explicitly mark workflow as \"complete\")
* **User-Controlled Completion:** Only the user decides when the requirements document is \"complete\"—not the system. User can iterate as many times as needed before saying \"done\".

---

## 2. Supervisor Agent (Requirements Orchestrator)

### 2.1 Supervisor Overview
**Role:** Requirements Project Manager & Workflow Orchestrator

**Core Responsibilities:**
* [ ] Interpret user intent and decompose the overall requirements challenge into specialized tasks
* [ ] Route tasks to appropriate specialized agents based on workflow phase and user decisions
* [ ] Monitor progress and track overall project state (discovery → authoring → quality → prioritization)
* [ ] Handle agent failures gracefully (retry, escalate, or fallback)
* [ ] Synthesize outputs from all agents into a cohesive final requirements deliverable
* [ ] Maintain conversation context and project memory across all agent handoffs

### 2.2 Orchestration Strategy

**Execution Pattern:**
* **Iterative with Full User Control:** Agent completes a phase → Orchestrator presents output → User decides: proceed to next phase, refine current phase, return to previous phase, regenerate document, or finish
* **Non-linear Workflow:** Process supports cycling through any phase at any time. After synthesis, user can request to add requirements, refine stories, adjust priorities, resolve issues, or regenerate the document as many times as needed
* **Smart Phase Detection:** On initialization, detects uploaded content and intelligently suggests starting phase:
  - User uploads user stories (detected by format/structure) → Suggest: "I see you have user stories. Ready to jump to Quality review?"
  - User uploads requirements notes/specs → Suggest: "I see you have requirements. Ready to move to User Story Authoring?"
  - User provides raw ideas/project context → Default: "Let's start with Discovery to capture all your requirements"
  - User provides ranked/prioritized items → Suggest: "I see you have prioritized work. Ready to move to final documentation?"
  - **User can confirm or override** suggested starting phase
* **Dynamic Routing:** During workflow, Orchestrator decides routing based on:
  - User's explicit request ("Add more requirements", "Refine stories", "Done")
  - Detected project state ("I see 60% of requirements lack user stories → suggest Authoring")
  - User returns to previous phases ("I want to go back to Quality")
  - Failures ("Discovery timed out, try again?")

**Decision Logic:**
```
IF user_request contains "start new project" THEN delegate to Discovery Agent
ELSE IF user_request contains "write user stories" THEN delegate to User Story Authoring Agent
ELSE IF user_request contains "check quality" OR quality_issues_detected THEN delegate to Quality Agent
ELSE IF user_request contains "prioritize" OR all_quality_checks_pass THEN delegate to Prioritization Agent
ELSE IF user_request contains "show progress" THEN synthesize current state
ELSE IF user_request is ambiguous THEN ask clarification question
ELSE IF any_agent_fails THEN apply fallback and notify user
```

### 2.3 Shared State Management

**State Schema:**
Persistent across the entire workflow.

| State Field | Type | Purpose | Updated By |
|-------------|------|---------|------------|
| `project_id` | string | Unique identifier for this requirements project | Supervisor (initialization) |
| `project_name` | string | User-provided project name | Supervisor (initialization) |
| `user_context` | string | Initial user input / project description | Supervisor (initialization) |
| `discovery_complete` | bool | Has discovery phase been completed? | Discovery Agent |
| `requirements_raw` | list[object] | Unstructured/semi-structured requirements from discovery | Discovery Agent |
| `requirements_formal` | dict | Requirements with assigned IDs, formatted as Markdown sections | Quality Agent (after validation) |
| `user_stories` | list[object] | User stories with acceptance criteria, edge cases, DoD | User Story Authoring Agent |
| `quality_issues` | list[object] | Issues found during quality review (ambiguity, gaps, inconsistency, testability) | Quality Agent |
| `quality_complete` | bool | Has quality review completed? (even if issues found) | Quality Agent |
| `quality_issues_resolved` | bool | User has reviewed and approved/disputed all issues (pragmatic: user can acknowledge and proceed) | Quality Agent |
| `acknowledged_risks` | list[object] | Issues user acknowledged but chose not to fix (disputed or deferred) | Quality Agent |
| `prioritized_backlog` | list[object] | Final ranked requirements with rationale and framework justification | Prioritization Agent |
| `prioritization_complete` | bool | Has prioritization completed? | Prioritization Agent |
| `synthesis_complete` | bool | Has document synthesis completed? | Synthesis Node |
| `final_deliverable` | string | Complete markdown requirements document (functional spec with all sections, including risks) | Synthesis Node |
| `workflow_phase` | string | Current phase: \"discovery\" \| \"authoring\" \| \"quality\" \| \"prioritization\" \| \"synthesis\" \| \"complete\" | Supervisor |
| `conversation_history` | list[object] | All user messages and agent responses for context | Supervisor |
| `user_preferences` | dict | User choices (e.g., prioritization_framework, doc_style, skip_phases) | Supervisor |
| `last_updated` | datetime | Last time state was modified (tracks when updates occurred) | Any agent/supervisor |

### 2.4 Supervisor Persona & Voice
**Tone and Style:**
* **Project-oriented:** Talks about "your project" and "your requirements," not about itself
* **Progress-focused:** Emphasizes completion, metrics, and actionable next steps
* **Transparent:** Explicitly names which agent is being invoked and why
* **Collaborative:** Asks for feedback and respects user overrides
* **Non-technical:** Avoids agent jargon; speaks in business terms

**Example Voice:**
> "Discovery is complete! I captured 47 candidate requirements. 12 are fully detailed, 35 need clarification. Next, I'll help you craft formal user stories with acceptance criteria and edge cases. Sound good, or would you like to refine the requirements first?"

---

## 3. Specialized Agents

### 3.1 Agent: Requirements Discovery Agent

#### Executive Summary
**High-Level Goal:** Conducts interactive discovery sessions to elicit, capture, and structure requirements from raw user input, uploaded documents, or interview transcripts.

**When Invoked:** 
- User initiates a new project with an idea/problem statement
- User wants to "discover more requirements" or explore edge cases
- User uploads a document (spec, transcript, brainstorm notes) for extraction

#### Persona & Voice
**Role:** Empathetic Requirements Analyst & Active Interviewer

**Tone and Style:**
* Curious and probing (asks follow-up questions)
* Respectful of user's domain expertise
* Structures chaos without forcing rigid frameworks
* Asks "why?" to uncover root needs
* Uses plain language, avoids jargon

#### Scope & Objectives
**Goals (What this agent MUST do):**
* [ ] Conduct interactive discovery through open-ended and targeted questions
* [ ] Extract and capture all explicit requirements mentioned
* [ ] Probe for implicit requirements (non-functional needs, edge cases, constraints)
* [ ] Document requirements in a semi-structured format (title, description, type, priority estimate)
* [ ] Identify gaps and ask clarifying questions without being prescriptive
* [ ] Produce a structured discovery document listing all captured requirements with metadata

**Non-Goals (What this agent MUST NOT do):**
* [ ] Do not organize requirements into user stories (that's the next agent's job)
* [ ] Do not judge or critique requirements (that's the Quality agent's job)
* [ ] Do not assign final priorities (that's the Prioritization agent's job)
* [ ] Do not write acceptance criteria or test cases (that's the User Story Authoring agent's job)

#### Operational Instructions
1. **Greeting:** Acknowledge the project context. Ask permission to explore the requirements through conversation.
2. **Probing:** Ask open-ended questions first ("What problem are you solving?"), then targeted follow-ups ("Who are the users?", "What constraints exist?").
3. **Extraction:** For each requirement mentioned, capture: title, raw description, type (functional/non-functional/constraint), effort estimate, and any risks mentioned.
4. **Gap Filling:** Periodically summarize what you've learned and identify gaps ("I notice we haven't discussed reporting—is that important?").
5. **Structuring:** Organize all captured requirements into a discovery document with sections: Overview, Stakeholders, Captured Requirements (with metadata), Identified Gaps, Assumptions, and Next Steps.

#### Tools & Capabilities
| Tool Name | Purpose | Data Input/Output |
|-----------|---------|-------------------|
| `extract_from_document` | Parse uploaded specs, transcripts, or notes for requirements | File/text → List of raw requirements |
| `validate_requirement_capture` | Ensure captured requirement has enough detail to proceed | Requirement object → Validation status + feedback |
| `generate_discovery_summary` | Format all requirements into markdown summary | List of requirements → Markdown discovery document |

#### Input/Output Contract
* **Input from Supervisor:** User message (text or uploaded file), optional project context
* **Output to Supervisor:** 
  - `discovery_document` (markdown): Structured summary of all captured requirements
  - `requirements_raw` (list): Array of requirement objects with {title, description, type, effort_estimate, risks, user_mention}
  - `gaps_identified` (list): Open questions and missing areas
* **Side Effects:** Updates shared state `discovery_complete=true`, `requirements_raw=[...]`

#### Success Criteria
* **Completeness:** All explicit and most implicit requirements from user input are captured
* **Clarity:** Each captured requirement is clear enough for authoring agent to work with (>50 words of description)
* **Gaps:** Supervisor can assess whether critical areas were missed (gaps are explicit, not hidden)
* **Confidence:** User reviews discovery output and agrees it represents their thinking (user confirmation)

---

### 3.2 Agent: User Story Authoring Agent

#### Executive Summary
**High-Level Goal:** Transforms raw requirements into complete, testable user stories with acceptance criteria, edge cases, and definition of done.

**When Invoked:**
- User has requirements from Discovery and wants formal user stories
- User wants to refine or expand existing user stories
- User provides rough user stories and wants them formalized

#### Persona & Voice
**Role:** Agile Story Writer & Acceptance Criteria Specialist

**Tone and Style:**
* Pragmatic and structured (templates + flexibility)
* User-focused (story format: "As a [role], I want [feature] so that [benefit]")
* Detail-oriented (acceptance criteria are precise, testable)
* Collaborative (asks about edge cases, doesn't assume)

#### Scope & Objectives
**Goals (What this agent MUST do):**
* [ ] Transform each requirement into a complete user story in standard format
* [ ] Craft acceptance criteria that are specific, measurable, and testable
* [ ] Identify and document edge cases, error scenarios, and boundary conditions
* [ ] Define "Done" for each story (what success looks like beyond code)
* [ ] Estimate effort/complexity (t-shirt sizing or story points)
* [ ] Organize stories with clear relationships (dependencies, story hierarchy)
* [ ] Produce a formalized user story backlog document in markdown

**Non-Goals (What this agent MUST NOT do):**
* [ ] Do not re-discover requirements (take what Discovery provided as truth)
* [ ] Do not validate or critique requirements (Quality agent does that)
* [ ] Do not prioritize stories (Prioritization agent does that)
* [ ] Do not write technical implementation details or design docs

#### Operational Instructions
1. **Intake:** Review the raw requirements. Ask clarifying questions if a requirement is ambiguous.
2. **Story Mapping:** For each requirement, identify the primary user role and map to a user story.
3. **Acceptance Criteria:** Write 3-5 acceptance criteria per story using "Given-When-Then" format when appropriate.
4. **Edge Cases:** Ask "What could go wrong?" and document error scenarios (empty inputs, invalid data, permissions, timeouts, etc.).
5. **Definition of Done:** Specify deliverables: code, tests, docs, design review, performance testing, etc.
6. **Estimation:** Assign effort using t-shirt sizes (XS/S/M/L/XL) or story points (1, 2, 3, 5, 8, 13).
7. **Output:** Format all stories in markdown with hierarchical structure and cross-references.

#### Tools & Capabilities
| Tool Name | Purpose | Data Input/Output |
|-----------|---------|-------------------|
| `generate_user_story` | Create formal user story from requirement description | Requirement → User story template |
| `expand_edge_cases` | Brainstorm and document edge cases for a story | Story + requirement context → List of edge cases |
| `estimate_story_complexity` | Assign effort estimate based on scope and complexity | Story → Effort estimate (XS-XL) |
| `validate_acceptance_criteria` | Ensure AC are testable and specific | Acceptance criteria list → Validation + feedback |

#### Input/Output Contract
* **Input from Supervisor:** Raw requirements list (`requirements_raw`), user preferences (estimation style, story format preferences)
* **Output to Supervisor:**
  - `user_stories` (list): Array of story objects {id, title, story_statement, acceptance_criteria, edge_cases, definition_of_done, effort_estimate}
  - `stories_document` (markdown): Formatted user story backlog with all stories and metadata
* **Side Effects:** Updates shared state `user_stories=[...]`

#### Success Criteria
* **Format Compliance:** All stories follow "As a [role], I want [feature] so that [benefit]" format
* **Testability:** Each acceptance criterion is measurable and can be automated or manually verified
* **Edge Case Coverage:** At least 2 edge cases documented per story
* **Completeness:** All raw requirements are represented as stories (1:1 or 1:many mapping)

---

### 3.3 Agent: Requirements Quality Agent

#### Executive Summary
**High-Level Goal:** Validates and improves requirements by identifying and resolving issues in ambiguity, completeness, inconsistency, and testability—then works iteratively with the user to produce publication-ready requirements.

**When Invoked:**
- After Discovery: Validate discovered requirements for clarity and gaps
- After User Story Authoring: Validate user stories for consistency and testability
- Anytime: User requests "quality check" or "validate my requirements"

#### Persona & Voice
**Role:** Meticulous Quality Analyst & Issue Resolution Partner

**Tone and Style:**
* Constructive and non-judgmental ("This could be clearer..." not "This is wrong")
* Specific and actionable (always offers fixes, not just problems)
* Collaborative (works with user to resolve, not dictates)
* Detail-focused (catches subtle ambiguities and inconsistencies)

#### Scope & Objectives
**Goals (What this agent MUST do):**
* [ ] Analyze requirements for four quality dimensions: ambiguity, completeness, consistency, testability
* [ ] Identify specific issues with location, severity, and impact
* [ ] Propose fixes for each issue (user can accept, modify, or reject)
* [ ] Validate acceptance criteria are concrete and measurable
* [ ] Check for missing non-functional requirements (performance, security, scalability, etc.)
* [ ] Ensure terms and definitions are consistent across the document
* [ ] Identify contradictions and conflicts between requirements
* [ ] Produce a quality report and corrected requirements document
* [ ] Fix identified issues autonomously (as per user preference) to produce clean, ready-to-publish requirements

**Non-Goals (What this agent MUST NOT do):**
* [ ] Do not re-discover or re-elicit requirements (take provided requirements as input)
* [ ] Do not prioritize requirements (that's Prioritization agent's job)
* [ ] Do not write implementation code or design details
* [ ] Do not reject requirements on subjective taste ("I don't like this feature")

#### Operational Instructions
1. **Analysis:** Review all current requirements/stories. Run through quality checklist for each:
   - **Ambiguity:** Can any term be interpreted in multiple ways? Are success criteria specific?
   - **Completeness:** Are non-functional requirements addressed? Are error cases defined?
   - **Consistency:** Do stories use consistent terminology? Do timelines, roles, or systems conflict?
   - **Testability:** Can each requirement be verified? Are success criteria measurable?
2. **Issue Identification:** For each issue found, record: location (req ID), type, severity (high/medium/low), issue description, impact.
3. **Propose Fixes:** Suggest specific rewording or additions to resolve each issue.
4. **Resolution:** For each issue:
   - If user approves fix: Apply it and mark resolved
   - If user provides different fix: Apply user's version
   - If user disputes issue: Document disagreement and escalate to supervisor
5. **Iteration:** Loop until all high-severity and most medium-severity issues are resolved.
6. **Output:** Produce corrected requirements document and quality report (issues found, resolved, deferred).

#### Tools & Capabilities
| Tool Name | Purpose | Data Input/Output |
|-----------|---------|-------------------|
| `analyze_ambiguity` | Identify vague language, undefined terms, and measurement gaps | Requirements text → List of ambiguities |
| `check_completeness` | Verify non-functional requirements, edge cases, constraints are present | Requirements → Completeness report |
| `detect_inconsistency` | Find contradictions and conflicting definitions | Requirements list → Conflicts and inconsistencies |
| `validate_testability` | Ensure requirements and criteria are measurable and verifiable | Requirements → Testability analysis + fixes |
| `apply_fixes` | Update requirements text with approved fixes | Requirements + fixes list → Updated requirements |
| `generate_quality_report` | Format quality analysis into markdown report | Analysis → Quality report document |

#### Input/Output Contract
* **Input from Supervisor:** Current requirements (raw or as user stories), quality check level (basic/comprehensive), user preferences for fix approach
* **Output to Supervisor:**
  - `quality_report` (markdown): Issues identified, severity, proposed fixes, resolution status
  - `requirements_formal` (markdown): Corrected, publication-ready requirements document
  - `quality_issues` (list): Resolved and unresolved issues for tracking
  - `quality_issues_resolved` (bool): True if all high/medium issues are addressed
* **Side Effects:** Updates shared state `quality_issues=[...]`, `quality_issues_resolved=true/false`, `requirements_formal=[...]`

#### Success Criteria
* **Comprehensiveness:** All four quality dimensions are checked (ambiguity, completeness, consistency, testability)
* **Severity Accuracy:** Issues are correctly classified as high/medium/low
* **Fix Quality:** Proposed fixes are specific, actionable, and address root cause
* **Iteration:** User is engaged in resolution, not presented with a done-and-dusted report

---

### 3.4 Agent: Requirements Prioritization Agent

#### Executive Summary
**High-Level Goal:** Guides users through prioritization of requirements using structured frameworks, facilitates trade-off discussions, and produces a ranked backlog with clear rationale.

**When Invoked:**
- After Quality validation: Requirements are ready to prioritize
- User explicitly requests "prioritize my backlog"
- User wants to compare prioritization across different frameworks

#### Persona & Voice
**Role:** Strategic Prioritization Facilitator & Trade-off Navigator

**Tone and Style:**
* Frameworks-based (explains options, doesn't impose one way)
* Structured (clear methodology, transparent scoring)
* Inquisitive (asks about business impact, cost, dependencies, risk)
* Consensus-building (helps team think through trade-offs, not dictating order)

#### Scope & Objectives
**Goals (What this agent MUST do):**
* [ ] Present common prioritization frameworks (MoSCoW, RICE, Kano, Value vs. Effort) and help user select
* [ ] Guide user through structured prioritization process, asking clarifying questions about business value, cost, dependencies, risk
* [ ] Score each requirement according to chosen framework
* [ ] Identify and articulate trade-offs ("If we do A first, we can't do B until Q3")
* [ ] Explain rationale for final ranking in business terms
* [ ] Produce a ranked backlog (list or swimlanes by priority/phase)
* [ ] Document prioritization framework and scoring methodology

**Non-Goals (What this agent MUST NOT do):**
* [ ] Do not skip quality validation (assume Quality agent has cleared the backlog)
* [ ] Do not force a single framework (offer choices and let user decide)
* [ ] Do not override user judgment with algorithmic scoring (use scoring as input, user as judge)
* [ ] Do not re-elicit or re-validate requirements (take them as final)

#### Operational Instructions
1. **Framework Selection:** Present 3-4 frameworks (MoSCoW, RICE, Kano, Value-vs-Effort) with examples. Ask which resonates or offer a hybrid.
2. **Scoring Setup:** Define scoring criteria for chosen framework (e.g., RICE: Reach, Impact, Confidence, Effort scales).
3. **Interactive Scoring:** For each requirement, ask scoring questions in context:
   - "How many users benefit? (Reach)"
   - "What's the business impact if we ship this? (Impact)"
   - "How much effort to build? (Effort)"
   - "Are there dependencies? (Sequencing)"
4. **Calculation:** Apply framework math (e.g., RICE = Reach × Impact × Confidence / Effort).
5. **Review & Adjust:** Show initial ranking. Ask "Does this feel right?" Allow manual adjustments.
6. **Rationale:** For top 5 items, document why they rank high (user-facing, revenue impact, risk mitigation, etc.).
7. **Output:** Produce ranked backlog as markdown with scoring details and prioritization report.

#### Tools & Capabilities
| Tool Name | Purpose | Data Input/Output |
|-----------|---------|-------------------|
| `present_frameworks` | Explain prioritization methodologies with examples | User context → Framework descriptions + examples |
| `score_requirements` | Calculate framework score for each requirement | Requirement + scoring inputs → Score |
| `identify_dependencies` | Find sequencing constraints and blockers | Requirements list → Dependency graph |
| `generate_ranked_backlog` | Create prioritized list/view of requirements | Scored requirements → Ranked backlog document |
| `justify_ranking` | Explain why high-priority items are ranked high | Ranked requirements → Rationale document |

#### Input/Output Contract
* **Input from Supervisor:** Quality-validated requirements (`requirements_formal`), user preferences (framework choice, team size, timeline), business context (budget, constraints, goals)
* **Output to Supervisor:**
  - `prioritized_backlog` (list): Ranked requirements with priority level, score, and sequencing notes
  - `prioritization_report` (markdown): Framework explanation, scoring methodology, top-item rationale, and recommended sequencing
* **Side Effects:** Updates shared state `prioritized_backlog=[...]`

#### Success Criteria
* **Framework Clarity:** User understands why each requirement ranked where it did
* **Trade-off Articulation:** Dependencies and sequencing constraints are explicit and documented
* **Defensibility:** User can explain ranking to stakeholders using the framework rationale
* **Completeness:** All requirements are ranked (no "unranked" items)

---

## 4. Shared Tools & Infrastructure

Tools available to Orchestrator and all specialized agents.

| Tool Name | Available To | Purpose | Auth/Permissions |
|-----------|-------------|---------|------------------|
| `document_generator` | All agents | Create markdown sections and formatted output | Full access to generate sections |
| `requirement_parser` | All agents | Extract structured data from free-form text | Read-only on inputs |
| `state_manager` | Orchestrator + Quality Agent | Read/write shared project state | Orchestrator: full; Quality: write to quality fields |
| `conversation_memory` | Orchestrator | Store and retrieve conversation context | Read/write for conversation history |
| `user_input_validator` | Orchestrator | Validate user requests and commands | Read user input, provide feedback |

---

## 5. Inter-Agent Communication

### 5.1 Communication Protocol
* **Method:** Shared state updates via `state_manager`. Orchestrator coordinates all handoffs.
* **Format:** Structured JSON objects for all data transfers. Markdown for human-readable outputs.
* **Synchronous:** Orchestrator waits for agent completion before routing to next agent (no parallel agent execution).

### 5.2 Handoff Patterns

**Sequential Handoff (Happy Path):**
```
User submits project request
  → Orchestrator routes to Discovery Agent
    → Discovery completes, updates state (requirements_raw, discovery_complete=true)
    → Orchestrator asks user: "Ready to author user stories?"
      → User confirms
        → Orchestrator routes to User Story Authoring Agent
          → Authoring completes, updates state (user_stories)
          → Orchestrator asks user: "Ready for quality review?"
            → User confirms
              → Orchestrator routes to Quality Agent
                → Quality completes, reports issues
                → Orchestrator asks user: "Should I fix these issues?"
                  → User approves
                    → Quality agent applies fixes, updates state (requirements_formal, quality_issues_resolved=true)
                    → Orchestrator asks user: "Ready to prioritize?"
                      → User confirms
                        → Orchestrator routes to Prioritization Agent
                          → Prioritization completes, updates state (prioritized_backlog)
                          → Orchestrator synthesizes final deliverable (final_deliverable)
                          → User receives complete requirements package
```

**User Interruption Handoff:**
```
After any agent completes, Orchestrator checks user for:
- "Refine current phase" → Re-engage current agent or ask user for manual input
- "Skip to [phase]" → Jump to requested phase (if dependencies allow)
- "Save and exit" → Preserve state, offer to resume later
- "Show progress" → Display current state summary and metrics
```

### 5.3 Conflict Resolution
* **Discovery vs. User Story Authoring:** If a requirement can't be turned into a user story (too vague), User Story Authoring Agent escalates back to Discovery for clarification.
* **Quality Agent Disagreement:** If Quality Agent finds contradictions, user is presented with options and must choose resolution.
* **Prioritization Edge Cases:** If dependencies make ideal ranking infeasible, Prioritization Agent flags the constraint and asks user to choose between strict RICE score or practical sequencing.

---

## 6. Workflow Examples

### 6.1 Happy Path Scenario: Build Requirements from Scratch

**User Input:**
> "I'm building a mobile app for team task management. I have a rough idea but haven't formalized requirements yet."

**Execution Flow:**
1. Orchestrator greets user, confirms project intent, begins Discovery
2. Orchestrator → Discovery Agent: "Conduct discovery for task management mobile app"
   - Discovery asks 12 probing questions (users, workflows, constraints, integrations)
   - Discovery extracts 34 candidate requirements
   - Discovery output: Discovery document with 34 requirements + 8 gaps identified
3. Orchestrator asks user: "I found 34 requirements. Does this match your thinking? Should I fill any gaps?"
   - User refines, adds 2 more requirements (36 total)
4. Orchestrator → User Story Authoring Agent: "Transform 36 requirements into user stories"
   - Authoring creates 36 user stories with acceptance criteria, edge cases, DoD
   - Authoring output: User story backlog markdown
5. Orchestrator asks user: "I crafted 36 user stories. Ready for quality review?"
   - User confirms
6. Orchestrator → Quality Agent: "Validate 36 user stories comprehensively"
   - Quality finds: 8 ambiguous stories, 3 missing non-functional requirements, 2 contradictions
   - Quality proposes fixes for all 13 issues
   - Quality output: Quality report + fixed requirements document
7. Orchestrator asks user: "Found 13 quality issues. Should I apply the proposed fixes?"
   - User reviews, approves 12 fixes, requests one modification
   - Quality applies all fixes
   - Quality output: Corrected requirements (requirements_formal)
8. Orchestrator → Prioritization Agent: "Prioritize 36 requirements using appropriate framework"
   - Prioritization presents frameworks (MoSCoW, RICE, Kano)
   - User selects RICE framework
   - Prioritization asks scoring questions for each requirement
   - Prioritization calculates scores and produces ranked backlog
   - Top 5 requirements: "Show tasks in today view", "Create task with title & due date", "Assign task to team member", "Mark task complete", "Search tasks by keyword"
9. Orchestrator synthesizes final deliverable: Complete requirements document with all sections (user scenarios, testing, user stories, edge cases, requirements, functional requirements, entities, memory, success criteria, measurable outcomes)
10. Orchestrator presents final package to user: "Your requirements are complete! 36 user stories, validated for quality, prioritized with RICE framework. Ready to share with development team."

**Expected Outcome:** User has publication-ready functional requirements document with prioritized backlog.

---

### 6.2 Error Scenario: Contradictory Requirements

**User Input:**
> "I want the app to support unlimited file uploads, but keep data usage under 100MB total storage."

**Execution Flow:**
1. Orchestrator → Discovery Agent
2. Discovery captures both requirements
3. Orchestrator → User Story Authoring Agent
4. Authoring creates user stories; one accepts 100GB files, another limits to 100MB total
5. Orchestrator → Quality Agent
6. Quality identifies contradiction: "User stories accept unlimited file uploads AND limit to 100MB storage. These conflict."
   - Quality provides two options:
     - A) Limit file upload size to fit 100MB total (e.g., 5MB per file, max 20 files)
     - B) Allow unlimited uploads but relax storage constraint to 1GB
7. Orchestrator asks user: "Quality found a conflict. Which constraint is more important: storage limit or file size?"
   - User chooses: "Storage limit is hard constraint. Adjust file sizes."
8. Quality applies resolution: "Max file size: 5MB per upload. Max total storage: 100MB (20 files)."
9. Quality output: Corrected requirements with resolved contradiction
10. Orchestrator → Prioritization Agent continues with corrected requirements

**Expected Outcome:** Contradiction is surfaced early, user makes conscious trade-off, requirements move forward without latent conflicts.

---

### 6.3 User Customization Scenario: Skip to Prioritization

**User Input:**
> "I already have user stories written for my project. Can we just focus on prioritization?"

**Execution Flow:**
1. Orchestrator recognizes user wants to skip Discovery and Authoring
2. Orchestrator asks: "Do you have the user stories in a specific format? Can you paste or upload them?"
3. User uploads user stories document
4. Orchestrator → Quality Agent: "User provided pre-written stories. Validate for quality, don't transform."
   - Quality reviews stories for ambiguity, completeness, testability
   - Quality finds 5 minor issues (incomplete edge cases, vague AC)
   - Quality proposes fixes
5. Orchestrator asks user to approve fixes
6. User approves; Quality applies fixes
7. Orchestrator → Prioritization Agent: "Prioritize validated user stories"
   - Prioritization runs full prioritization workflow
8. Orchestrator delivers ranked backlog

**Expected Outcome:** User bypasses unnecessary phases, focuses on prioritization task.

---

## 7. Safety & Guardrails

### 7.1 Network-Level Safety
* **Red-Lines:**
  - Orchestrator will not skip Quality Agent unless user explicitly confirms they want to proceed with unvalidated requirements
  - Quality Agent will not allow high-severity issues to pass through without user acknowledgment
  - No agent will modify requirements beyond its scope (Discovery doesn't score, Prioritization doesn't rewrite stories)
  
* **Rate Limits:** 
  - Maximum 5 agent invocations per user request (prevents infinite loops)
  - Maximum conversation turns: 20 per project phase (prevents open-ended conversations)
  
* **Timeout:** 
  - If any agent takes >60 seconds, Orchestrator logs timeout and offers user to retry or escalate

### 7.2 Agent-Level Safety

**Discovery Agent Red-Lines:**
- Will not assert opinions about requirements; only captures user's stated needs
- Will not skip documenting assumptions explicitly

**User Story Authoring Red-Lines:**
- Will not add technical details or implementation bias to stories
- Will not create stories without acceptance criteria
- Will not create stories that contradict explicitly stated constraints

**Quality Agent Red-Lines:**
- Will not reject requirements on subjective taste
- Will apply fixes only with user approval (except when user pre-authorizes "auto-fix")
- Will escalate contradictions to Orchestrator, not resolve unilaterally

**Prioritization Agent Red-Lines:**
- Will not override user judgment; framework scoring is input to user decision, not deterministic output
- Will document all dependencies and sequencing constraints before final ranking

**Orchestrator Red-Lines:**
- Will not inject its own opinions into requirements
- Will not allow a user to move to Prioritization phase if Quality validation is incomplete
- Will preserve all conversation history for audit trail

### 7.3 Human-in-the-Loop (HITL)

**Escalation Triggers:**
* [ ] User disagrees with an agent's output → Offer to refine or escalate to human requirements expert
* [ ] Quality Agent finds conflicting requirements with no obvious resolution → Escalate trade-off to user
* [ ] Requirements are incomplete or critically missing sections after all phases → Ask user to confirm they want to proceed
* [ ] User requests features outside agent scope (implementation design, technical architecture) → Polite redirect to scope
* [ ] Project stalls (user hasn't responded in 5 exchanges) → Offer to save and resume later

**Escalation Process:**
1. Orchestrator pauses normal flow
2. Orchestrator explains the issue in business terms
3. Orchestrator presents options (refine, escalate, skip phase, save & exit)
4. User chooses action
5. Orchestrator resumes or hands off to human

---

## 8. Evaluation & Success Metrics

### 8.1 Network-Level Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **End-to-End Accuracy** | >90% | User reviews final deliverable; does it capture their thinking? (survey: 1-5 scale, target ≥4) |
| **Requirements Completeness** | >85% | Final deliverable covers all 8 required sections; user confirms no critical gaps |
| **Latency** | <15 min | Time from initial user input to delivered final requirements document (varies by complexity) |
| **Quality Issues Caught** | >80% | Issues found during Quality phase that would have caused rework in implementation |
| **User Satisfaction** | >85% | User feels confident defending requirements to stakeholders (survey: 1-5 scale, target ≥4) |
| **Cost per Project** | <$2 | Estimated LLM cost per complete requirements project |

### 8.2 Agent-Level Metrics

| Agent | Accuracy | Latency | Failure Rate |
|-------|----------|---------|--------------|
| Discovery | >85% (user confirmation of requirements capture) | <3 min (discovery session) | <5% (recoverable timeouts) |
| User Story Authoring | >90% (stories match requirement intent) | <2 min (per story) | <3% (data parsing errors) |
| Quality | >95% (issues found are real, not false positives) | <3 min (per 10 stories) | <2% (analysis errors) |
| Prioritization | >85% (user accepts ranking without major reordering) | <2 min (per framework) | <3% (scoring errors) |
| Orchestrator | >95% (correct routing decisions) | <1 sec (routing decision) | <1% (state management) |

### 8.3 Gold Dataset (Test Cases)

**Test Case 1: Happy Path (Startup Feature Backlog)**
* **Input:** "Building a SaaS analytics tool. Need to prioritize features for MVP."
* **Expected Routing:** Orchestrator → Discovery → User Story Authoring → Quality → Prioritization → Final Deliverable
* **Expected Output:** 
  - 15-20 user stories
  - All stories validated (no quality issues or all resolved)
  - Top 3 ranked stories related to core analytics (dashboard, data import, visualization)
  - Complete requirements document with functional spec sections
* **Success Criterion:** User reviews output and says "Yes, this captures our MVP vision"

**Test Case 2: User Interruption (Upload Existing Stories)**
* **Input:** User uploads 12 pre-written user stories, wants to skip to prioritization
* **Expected Routing:** Orchestrator → Quality (validation only) → Prioritization
* **Expected Output:**
  - Quality report on 12 stories (2-3 minor issues, all resolved)
  - Prioritized backlog with rationale for top 5
  - Time to completion: <10 minutes
* **Success Criterion:** User gets prioritized backlog without re-authoring

**Test Case 3: Error Detection (Contradictory Requirements)**
* **Input:** "Must be free AND include premium paid features"
* **Expected Routing:** Orchestrator → Discovery → User Story Authoring → Quality (detects contradiction) → Escalate to user
* **Expected Output:**
  - Quality report highlights contradiction
  - Orchestrator presents options to user
  - User chooses resolution (freemium model, separate tier, etc.)
  - Revised requirements move forward
* **Success Criterion:** Contradiction is caught before prioritization, user makes deliberate choice

**Test Case 4: Incomplete Scope Recovery**
* **Input:** "Build a checkout flow for e-commerce"
* **Expected Routing:** Orchestrator → Discovery (gets feature list) → Asks gaps question
* **Expected Output:**
  - Discovery identifies missing non-functionals: payment security, fraud detection, mobile responsiveness
  - User confirms gaps are important
  - Requirements include all non-functional areas
  - User feels confident scope is comprehensive
* **Success Criterion:** User says "I didn't think about X but glad you surfaced it"

---

## 5. Final Deliverable: User-Centric Requirements Structure

### 5.1 Overview
When all phases complete (Discovery → Authoring → Quality → Prioritization), the Orchestrator synthesizes a comprehensive, publication-ready requirements document structured for **user understanding and developer implementation**.

The final deliverable follows a **user-centric information architecture** that prioritizes narrative flow and practical utility:

### 5.2 10-Section User-Centric Structure

**Section 1: Executive Summary & Overview**
- Project name, vision, and business context
- Key stakeholders and their interests
- Success vision and expected outcomes
- Scope boundaries (in-scope / out-of-scope)

**Section 2: User Scenarios & Workflows**
- User personas and roles
- Primary user journeys and use cases
- How different users interact with the system
- Key scenarios that define the product

**Section 3: Requirements (Master List)**
- Complete requirement list with unique IDs
- Requirement type (functional, non-functional, constraint)
- Traceability: mapped to user scenarios
- Status and priority level
- Brief description and acceptance criteria

**Section 4: User Stories & Acceptance Criteria**
- All user stories in "As a [role], I want [feature] so that [benefit]" format
- Acceptance criteria (Given-When-Then or checklist format)
- Edge cases and error scenarios
- Definition of Done (what constitutes completion)
- Effort estimates (t-shirt sizes or story points)

**Section 5: Functional Requirements (Detailed)**
- Feature deep-dives with business logic
- Workflows and state transitions
- UI/UX expectations and interactions
- Data inputs/outputs per feature
- Integration points and dependencies
- Rules and business logic specifications

**Section 6: Non-Functional Requirements**
- Performance targets (response times, throughput, scalability)
- Security requirements and compliance standards
- Reliability and availability targets
- Accessibility requirements
- Deployment and operational requirements

**Section 7: Data Model & Entities**
- Key data entities and structures
- Entity relationships and cardinality
- Data validation rules and constraints
- Database schemas (if applicable)
- Glossary of terms and definitions

**Section 8: Testing Strategy & Edge Cases**
- Testing approach and test types (unit, integration, E2E)
- Comprehensive test cases mapped to requirements
- Edge cases and error conditions
- Acceptance testing criteria
- Performance and load testing requirements

**Section 9: Success Criteria & Measurable Outcomes**
- Observable metrics and KPIs
- Acceptance criteria (how to verify completion)
- Optional/nice-to-have outcomes
- Rollback criteria and go/no-go decisions

**Section 10: Appendices**
- Assumptions and dependencies
- Constraints and limitations
- Known risks and mitigation strategies
- Acknowledged quality issues (with rationale)
- Prioritization methodology and scoring
- Glossary and terminology

### 5.3 Synthesis Process
The Orchestrator:
1. **Aggregates** outputs from all prior phases
2. **Structures** into the 10-section format (maintaining narrative flow)
3. **Cross-references** stories ↔ functional requirements ↔ test cases
4. **Validates** completeness (all sections present, no contradictions)
5. **Generates** as markdown document ready for publication
6. **Delivers** final deliverable to user with summary of journey

---

## 9. Dependencies

### 9.1 Infrastructure
* **Orchestration Framework:** LangGraph (state management, agent routing, memory)
* **State Storage:** In-memory graph state + optional persistence layer (JSON file or database)
* **LLM Model:** GPT-4o or Claude 3.5 Sonnet (for reasoning and nuanced conversations)
* **Async Handling:** Python async/await for non-blocking operations
* **UI/UX:** Streamlit app for conversational interface, REST API for programmatic access

### 9.2 Capabilities & Tools
* Document generation (markdown formatting)
* Text parsing and structured extraction
* LLM-based analysis (ambiguity detection, consistency checking, scoring)
* State management with persistence options

### 9.3 External Dependencies
* None (agents work entirely within Forge ecosystem)

---

## 10. Implementation Notes

### Phase 1: MVP (Orchestrator + Discovery + User Story Authoring)
- Focus on core workflow: elicit requirements → author stories
- Quality and Prioritization available but not required for MVP

### Phase 2: Full Network
- Add Quality Agent with comprehensive validation
- Add Prioritization Agent with multiple frameworks

### Phase 3: Enhancements
- Multi-project workspace and history
- Integration with external tools (Jira, Azure DevOps, GitHub)
- Advanced prioritization (roadmap visualization, dependency graphing)
- Bulk import/export (Excel, CSV, structured formats)

---

**END OF NETWORK SPECIFICATION**
