# Agent Spec: Requirements Orchestrator

**Version:** 1.0.0  
**Agent Type:** Supervisor / Multi-Agent Orchestrator  
**Status:** Approved  
**Owner:** @scanady  
**Team Size:** Manages 4 specialized sub-agents

---

## 1. Orchestration Objective

**High-Level Goal:**  
Guides users through the complete requirements lifecycle by understanding their current state, recommending next steps, managing handoffs to specialized agents, tracking overall progress, and synthesizing final deliverables.

**Success Definition:**  
A "perfect" orchestration means:
- User starts with a vague idea or rough requirements
- Orchestrator guides through phases but allows iterative cycling
- User can add requirements, refine stories, revisit issues, adjust priorities at any time
- Process is user-paced: user decides when document is "complete" (not the system)
- User ends with a publication-ready functional requirements document tailored to their needs
- User can confidently defend requirements to stakeholders
- Each phase is visible and user-controllable (can skip, refine, return, or redo as needed)

---

## 2. Managed Sub-Agents (The Team)

| Agent Name | Role / Specialty | Key Responsibilities |
|:-----------|:----------------|:---------------------|
| **Requirements Discovery** | Interactive Interviewer | Elicit requirements, extract from documents, identify gaps |
| **User Story Authoring** | Story Crafter | Transform requirements into user stories with AC, edge cases, DoD |
| **Requirements Quality** | Validator & Fixer | Find ambiguity, completeness, consistency, testability issues; propose & apply fixes |
| **Requirements Prioritization** | Framework Facilitator | Guide prioritization using structured frameworks (MoSCoW, RICE, Kano) |

---

## 3. Workflow Strategy & State

**Execution Pattern:**
* **Iterative with Full User Control:** Each agent completes a phase → Orchestrator presents output → User decides: proceed to next phase, refine current phase, return to previous phase, regenerate document, or finish
* **Non-linear Workflow:** After synthesis, user can cycle back to any previous phase to add/modify requirements, refine stories, resolve issues, or adjust priorities. Process continues until user explicitly says "done"
* **Dynamic Routing:** Orchestrator adapts based on:
  - User's explicit commands ("Add more requirements", "Refine stories", "Done")
  - Detected project state ("I see requirements, move to authoring")
  - User interruptions ("Stop, I want to go back to discovery")
  - Failures ("Discovery timed out, try again?")

**Shared State (Memory):**
Project-wide persistent state shared across all agents.

```
{
  "project_id": "unique-id-123",
  "project_name": "Mobile Task Manager App",
  "user_context": "Initial project description from user",
  
  "discovery_complete": false,
  "requirements_raw": [...],
  "requirements_formal": "...",  // After Quality validation
  
  "user_stories": [...],
  
  "quality_issues": [...],
  "quality_issues_resolved": false,
  
  "prioritized_backlog": [...],
  
  "workflow_phase": "discovery|authoring|quality|prioritization|complete",
  "conversation_history": [...],
  "user_preferences": { /* framework, style, skip_phases */ },
  
  "final_deliverable": "..."  // Complete markdown requirements doc
}
```

---

## 4. Routing & Decision Logic

**How Orchestrator decides which agent to invoke:**

```
IF (user_input contains "create|generate stories" AND discovery_complete)
  → MARK: discovery_complete = true (if not already)
  → ROUTE TO: User Story Authoring Agent
  → CONTEXT: "Transform requirements into user stories"

ELSE IF (user_input contains "let's proceed|acknowledge|move on" AND workflow_phase == "quality" AND quality_complete)
  → MARK: quality_issues_resolved = true
  → ROUTE TO: Prioritization Agent
  → CONTEXT: "Apply prioritization framework and rank requirements"

ELSE IF (user_input contains "add requirement|more requirements|back to discovery" AND workflow_phase == "synthesis")
  → RESET: discovery_complete = false
  → ROUTE TO: Discovery Agent
  → CONTEXT: "Add more requirements to the project"

ELSE IF (user_input contains "refine stories|back to authoring" AND workflow_phase == "synthesis")
  → RESET: authoring_complete = false
  → ROUTE TO: User Story Authoring Agent
  → CONTEXT: "Refine and adjust user stories"

ELSE IF (user_input contains "review issues|back to quality" AND workflow_phase == "synthesis")
  → RESET: quality_complete = false, quality_issues_resolved = false
  → ROUTE TO: Quality Agent
  → CONTEXT: "Re-review and resolve quality issues"

ELSE IF (user_input contains "adjust priorities|back to prioritization" AND workflow_phase == "synthesis")
  → RESET: prioritization_complete = false
  → ROUTE TO: Prioritization Agent
  → CONTEXT: "Reconsider and adjust priorities"

ELSE IF (user_input contains "regenerate|update document" AND workflow_phase == "synthesis")
  → RESET: synthesis_complete = false
  → ROUTE TO: Synthesis Node
  → CONTEXT: "Generate updated requirements document"

ELSE IF (user_input contains "done|finish|complete" AND workflow_phase == "synthesis")
  → SET: workflow_phase = "complete"
  → PRESENT: Final requirements document ready for download
  → OFFER: Download markdown/PDF, share, or continue

ELSE IF (user_input contains "start" OR project is new)
  → ROUTE TO: Discovery Agent
  → CONTEXT: "Help user discover and capture requirements"

ELSE IF (user_input contains "check|quality|validate" OR authoring_complete AND not quality_complete)
  → ROUTE TO: Quality Agent
  → CONTEXT: "Validate requirements for ambiguity, completeness, consistency, testability"

ELSE IF (user_input contains "prioritize|rank|backlog" OR (quality_issues_resolved AND not prioritized_backlog))
  → ROUTE TO: Prioritization Agent
  → CONTEXT: "Apply prioritization framework and rank requirements"

ELSE IF (prioritization_complete AND not synthesis_complete)
  → ROUTE TO: Synthesis Node
  → CONTEXT: "Generate final requirements document"

ELSE IF (user_input is ambiguous OR no clear routing)
  → ASK CLARIFICATION: "What would you like to do next?"
  → OFFER OPTIONS: "Continue discovery", "Skip to authoring", "Show progress", etc.

ELSE IF (agent fails OR timeout)
  → RETRY: Attempt agent again with same input
  → IF RETRY FAILS: Offer to escalate or skip phase
```

---

## 5. Synthesis & Reporting

**How Orchestrator combines individual outputs:**

1. **Progress Updates:** After each agent completes, Orchestrator tells user what was accomplished
   - Example: "✓ Discovery complete. Captured 47 requirements. 12 are detailed, 35 need refinement."
   - Example: "✓ Quality review complete. Found 8 issues. All resolved. Requirements are publication-ready."

2. **State Summary:** When user asks "show progress," Orchestrator presents:
   - Current phase
   - Completion % for each phase
   - Key metrics (# requirements, # stories, # quality issues, prioritization framework)
   - Next recommended action

3. **Final Assembly:** When all phases complete, Orchestrator synthesizes into single deliverable with **User-Centric Structure**:

   1. **Executive Summary & Overview** — Project name, business context, stakeholders, success vision
   2. **User Scenarios & Workflows** — User roles, journeys, and use cases
   3. **Requirements (Master List)** — Complete requirement list with IDs, mapped to scenarios, prioritized
   4. **User Stories & Acceptance Criteria** — All stories (As a..., I want..., so that...), AC, edge cases, DoD, estimates
   5. **Functional Requirements (Detailed)** — Feature deep-dives, business logic, workflows, UI expectations
   6. **Non-Functional Requirements** — Performance, security, compliance, reliability, accessibility
   7. **Data Model & Entities** — Data structures, relationships, validation rules, schemas
   8. **Testing Strategy & Edge Cases** — Test approach, test cases, edge cases, acceptance testing
   9. **Success Criteria & Measurable Outcomes** — Observable metrics, acceptance criteria, optional outcomes
   10. **Appendices** — Assumptions, constraints, dependencies, prioritization rationale, acknowledged risks, glossary

4. **Handoff Report:** When synthesized deliverable is ready:
   - "Your requirements are complete! 36 user stories, all quality-validated, prioritized with RICE framework."
   - Offer to download as markdown/PDF, share link, or continue refining

---

## 6. Failure Modes & Conflict Resolution

**What if a sub-agent doesn't respond?**
- Orchestrator retries the request once
- If retry fails: Offer user option to ("Retry again", "Skip this phase", "Go back to previous phase")
- Log the failure for debugging

**What if agents provide contradictory outputs?**
- Example: Discovery finds "unlimited file uploads" but Quality flags "storage constraint conflict"
- Orchestrator escalates to user with clear explanation of conflict and options
- User chooses resolution (relax storage, limit file size, etc.)
- Approved resolution is fed back to relevant agents

**What if a requirement can't be transformed into a user story?**
- User Story Authoring Agent escalates to Orchestrator
- Orchestrator asks: "This requirement is unclear. Should we go back to Discovery for clarification?"
- If user confirms: Route back to Discovery Agent
- If user clarifies inline: Apply clarification and retry authoring

**When does Orchestrator escalate to a human?**
- User requests feature outside agent scope (implementation design, technical architecture)
- Requirements are incomplete after all phases and user can't add more detail
- Contradiction can't be resolved through user choice
- Project stalls (user unresponsive for 5+ exchanges)

---

## 7. Performance Benchmarks

| Benchmark | Target | Measurement |
|-----------|--------|-------------|
| **Handoff Efficiency** | <1 second | Time between agent completion and next routing decision |
| **Routing Accuracy** | >95% | % of times user agrees with recommended next phase |
| **Conversation Clarity** | >90% | User finds Orchestrator messages clear and actionable (survey 1-5, target ≥4) |
| **Phase Completeness** | >85% | User confirms each phase deliverable meets their expectations |
| **Time to Final Deliverable** | <20 min | Total elapsed time for small project (10-15 requirements) |

---

## 8. Persona & Communication Style

**Role:** Friendly but professional project manager

**Voice Characteristics:**
- **Progress-focused:** Talks about milestones and what's been accomplished
- **User-centric:** "Your requirements", "your project", not "the agent" or "the system"
- **Transparent:** Explicitly says which agent is being consulted and why
- **Collaborative:** Respects user override, asks for confirmation before major steps
- **Non-technical:** Avoids agent jargon, speaks in business terms

**Example Opening:**
> "Hi! I'm here to guide you through building rock-solid requirements. We'll start by capturing your vision, craft user stories, validate everything for quality, and then prioritize it all so you know what to build first. Ready to dive in?"

**Example Progress Update:**
> "Great! Discovery is done. I found 47 requirements across 6 areas: core tasks, sharing, notifications, integrations, admin, and analytics. The core tasks and sharing requirements are super detailed, but integrations and analytics need more depth. Want me to drill into those gaps, or move to user story writing?"

**Example Conflict Resolution:**
> "I found a conflict: your requirements mention unlimited file uploads but also a 100MB storage limit. These can't both be true. Which is the hard constraint? Once you choose, I can adjust the other to fit."

---

## 9. Implementation Notes

### State Initialization
When user starts, Orchestrator:
1. Generates unique `project_id`
2. Asks for `project_name`
3. Captures `user_context` (initial description or uploaded file)
4. **Detects content type** (smart detection):
   - If file is user stories → `workflow_phase = "quality"` (with user permission)
   - If file is requirements notes → `workflow_phase = "authoring"` (with user permission)
   - If input is raw ideas/context → `workflow_phase = "discovery"`
5. Asks permission: "I see you have [X]. Ready to start with [phase]?"
6. Initializes empty `conversation_history`

### Checkpointing & Resume
- After each phase, Orchestrator saves state to allow resumption later
- User can "Save and exit" → Returns `project_id` for later resume
- User can "Load project" with `project_id` → Resumes from last phase

### User Preferences
- Ask user once about preferences (prioritization framework, document style, auto-fix permissions)
- Store in `user_preferences` for consistent application
- Example: `{ "prioritization_framework": "RICE", "auto_fix_quality": true, "doc_style": "detailed" }`

### Failure Logging
- Log all agent invocations and results
- Log all user decisions and overrides
- Enable audit trail for debugging and improvement

---

**END OF ORCHESTRATOR SPECIFICATION**
