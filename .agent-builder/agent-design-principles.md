# Core Design Principles for AI Agent Functional Design

## Purpose

These principles guide the translation of existing business processes into effective AI agent functional requirements. They focus on defining what the agent should accomplish and how it fits into business workflows, not how it will be technically implemented.

---

## 1. Foundational Philosophy

### Start Simple, Iterate
Begin with the minimum viable agent function and validate it works reliably before expanding scope. Each increment of functionality should be justified by demonstrated need rather than anticipated requirements.

**Application**: Define core function first, add supporting functions only after core is proven.

### User-Centric Design
Design agent functions around user mental models and needs, not around what's technically possible. Users should understand what the agent does, when it will act, and what outcomes to expect.

**Application**: Match agent functional design to how users conceptualize the process, not how systems execute it.

### Outcome-Oriented Thinking
Focus functional requirements on business outcomes the agent produces, not tasks it performs or tools it uses.

**Application**: "Agent produces validated policy data ready for underwriting review" not "Agent extracts data from documents."

---

## 2. Process-to-Agent Mapping Principles

### Identify Natural Decision Points
Map where humans currently make decisions in existing processes and categorize them:
- Deterministic decisions (rule-based, could be automated without AI)
- Judgment-based decisions (require context interpretation, pattern recognition)
- Approval/validation decisions (require authority or expertise verification)

**Application**: Agent functional scope should align with clusters of related decisions, not arbitrary process steps.

### Preserve Process Intent, Not Process Steps
Understand what the process is trying to achieve and design agent functionality around those outcomes. Don't simply automate existing manual steps.

**Application**: If the process intent is "ensure compliance with policy X," the agent function is compliance verification, not form filling and routing.

### Map Current Authority to Agent Autonomy
Existing process authority levels should map directly to agent decision-making capabilities. High-stakes decisions should translate to agent recommendations, not autonomous agent decisions.

**Application**: If only managers can approve exceptions today, the agent recommends exceptions for manager approval rather than approving them autonomously.

---

## 3. Functional Boundary Definition

### Define Scope by Outcome Ownership
An agent should own complete responsibility for producing a specific outcome, not just performing isolated tasks. The agent should deliver a complete, usable result within its domain.

**Application**: Agent owns "validated application data" not just "data extraction" - validation and usability are part of the outcome.

### One Process Phase, One Agent Scope
Don't design agents that span multiple process phases with different objectives. Each distinct process phase with its own success criteria should be a separate agent function.

**Application**: Separate agents for data gathering, risk assessment, and pricing rather than one agent for all underwriting activities.

### Avoid the "Assistant" Anti-Pattern
Functional definitions like "helps underwriters with their work" are too vague. Specify concrete outcomes and decisions.

**Application**: Refine to "Generates summary of policy changes for underwriter review" or "Identifies applications requiring additional documentation."

### Distinguish Decisions from Recommendations
Be explicit in functional requirements about what the agent decides autonomously versus what it recommends for human decision.

**Application**: Clearly specify "Agent categorizes requests (autonomous)" vs "Agent suggests priority ranking (recommendation)."

---

## 4. Decision Authority and Autonomy

### Explicitly Define Decision Authority Spectrum
For each type of decision the agent makes, specify the level of authority:
- **Full autonomy**: Agent decides and acts
- **Bounded autonomy**: Agent decides within defined constraints
- **Recommendation with opt-out**: Agent recommends, proceeds unless overridden
- **Recommendation requiring approval**: Agent recommends, waits for confirmation
- **No authority**: Agent provides information only

**Application**: Create a decision authority matrix mapping each decision type to its authority level.

### Identify Escalation Triggers
Define what conditions move work from agent to human in functional terms:
- Confidence thresholds (agent uncertain)
- Business rule violations (outside normal parameters)
- Risk thresholds (financial, compliance, reputational)
- User preference (user chooses to take over)
- Complexity thresholds (task exceeds agent capabilities)

**Application**: Specify "Escalate to underwriter when premium calculation varies more than 15% from guideline" not just "escalate when uncertain."

### Design for Appropriate Human Oversight
Different types of work require different oversight patterns. Define functional oversight requirements based on risk and complexity.

**Application**: Low-risk categorization may require audit trail only. High-risk pricing decisions may require explicit approval before proceeding.

---

## 5. User Interaction Patterns

### Map User Roles to Interaction Modes
Different users need different functional interfaces to the same agent:
- **Initiators**: Start the agent, provide input, receive final output
- **Collaborators**: Work alongside agent iteratively
- **Supervisors**: Monitor agent work, intervene when needed
- **Consumers**: Receive agent outputs without initiating

**Application**: Specify which roles interact with the agent and what functional capabilities each role requires.

### Define Conversation vs Transaction Modes
Functionally classify the agent's interaction pattern:
- **Transaction**: User requests, agent performs, returns result
- **Conversation**: Iterative refinement toward a goal
- **Monitor and Alert**: Watch for conditions, notify when triggered
- **Orchestration**: Coordinate multiple activities over time

**Application**: This classification drives the functional requirements for how users interact with the agent.

### Provide Clear Action Transparency
Users should understand what the agent is doing, especially for long-running operations. Define what status information the agent provides during execution.

**Application**: Specify progress indicators like "Validating 15,000 records, currently at record 8,423" rather than generic "Processing."

---

## 6. Information Flow and Dependencies

### Map Information Dependencies
Identify what information the agent needs to perform its function:
- What must be provided by the user upfront?
- What can the agent retrieve from existing systems?
- What must the agent request from other agents/systems?
- What does the agent produce for downstream consumers?

**Application**: Create a functional data contract specifying all inputs, retrievals, and outputs.

### Define Trigger Conditions and Invocation Patterns
Specify how the agent knows when to act:
- User-initiated (explicit request)
- Event-triggered (system event occurs)
- Schedule-driven (time-based execution)
- Condition-based (monitoring threshold exceeded)
- Workflow-sequenced (previous step completed)

**Application**: Make implicit triggers in existing processes explicit in agent functional requirements.

### Specify Pre-conditions and Post-conditions
Define functional contracts with upstream and downstream process steps:
- **Pre-conditions**: What must be true before the agent can perform its function?
- **Post-conditions**: What will be true after the agent successfully completes?

**Application**: "Pre-condition: Application data is present in system. Post-condition: All required fields validated and categorized by risk level."

---

## 7. Success Criteria and Outcomes

### Define Observable Success Criteria in Business Terms
Focus on business outcomes, not technical metrics. Success criteria should be measurable and meaningful to business stakeholders.

**Application**: "Agent identifies all compliance gaps that manual review would catch" not "Agent uses correct tool 95% of the time."

### Specify Functional Exception Handling
Define what the agent should do functionally when exceptions occur:
- Required information is missing
- User provides conflicting inputs
- Downstream systems are unavailable
- Business rules conflict
- Results are ambiguous

**Application**: "When premium cannot be calculated due to missing risk factors, agent requests specific missing information from user and saves partial progress."

### Establish Completion Criteria
Define what "done" looks like for this agent's function in business terms.

**Application**: "Complete when all policy changes are summarized, categorized by impact level, and delivered to underwriter queue with supporting documentation."

---

## 8. Process Integration Points

### Define Handoff Protocols
When the agent completes its function, specify:
- What it delivers (outputs, artifacts, recommendations)
- In what format (structured data, narrative summary, decision)
- To whom (next process step, user, system)
- With what metadata (confidence, reasoning, alternatives considered)

**Application**: "Agent delivers structured JSON with validated fields, confidence scores, and list of assumptions made, to underwriting system API."

### Maintain Process Context Across Handoffs
When work passes between agents or between agent and human, specify what context must be preserved and transferred.

**Application**: "Agent passes original request, all gathered data, decision rationale, and conversation history to supervisor for review."

### Design Clear Integration Points
Specify where the agent connects to existing systems and processes:
- What systems does it read from?
- What systems does it write to?
- What notifications does it send?
- What audit trails does it create?

**Application**: "Agent reads from policy management system, writes validated data to underwriting queue, sends notification to assigned underwriter, logs all actions to audit database."

---

## 9. Scope Constraint Principles

### Single Responsibility
Each agent should have one clearly defined functional responsibility. If you can describe the agent's function with "and" in the middle, it's likely two agents.

**Application**: "Risk Assessment Agent" not "Risk Assessment and Pricing Agent."

### Bounded Context
Define clear functional boundaries for what the agent knows about and acts upon. The agent should not need to understand the entire business domain, only its specific area.

**Application**: Data Validation Agent understands policy data structure and validation rules, but not pricing algorithms or risk assessment criteria.

### Modular and Focused Tasks
Within an agent's function, break complex workflows into small, single-objective tasks. Each task should have clear inputs, outputs, and success criteria.

**Application**: "Validate applicant data" breaks into "Check required fields present," "Validate field formats," "Cross-check data consistency," each as distinct functional tasks.

---

## 10. Key Questions for Functional Design

When translating a process into agent functional requirements, systematically answer:

1. **What outcome is this agent responsible for producing?** (not what tasks it performs)
2. **Who initiates the agent and who consumes its output?** (defines interaction model)
3. **What decisions can this agent make autonomously?** (defines authority)
4. **What triggers escalation to human decision-makers?** (defines boundaries)
5. **How does success get measured in business terms?** (defines acceptance criteria)
6. **What information must be true before the agent can act?** (defines pre-conditions)
7. **What does "done" look like for this agent's function?** (defines completion criteria)
8. **How does this agent function fit into the larger process?** (defines integration points)
9. **What existing authority levels must be preserved?** (defines decision autonomy)
10. **What risks exist if this agent function fails?** (defines oversight requirements)
