# Agent Spec: [Supervisor Name]

**Version:** 1.0.0
**Agent Type:** Orchestrator / Multi-Agent Manager
**Status:** [Draft/Approved]
**Team Size:** [Number of sub-agents managed]

---

## 1. Orchestration Objective
**High-Level Goal:** Describe the complex problem this supervisor solves (e.g., "Coordinates the end-to-end research, writing, and fact-checking of technical blog posts").

**Success Definition:** What does a "perfect" orchestration look like? (e.g., "The final output is factually accurate, follows the style guide, and cited properly").

---

## 2. Managed Sub-Agents (The Team)
*List the specialized agents this supervisor has the authority to call.*

| Agent Name | Role / Specialty | Key Responsibilities |
| :--- | :--- | :--- |
| **[Sub-Agent A]** | [e.g., Researcher] | Gathering raw data from web/DB. |
| **[Sub-Agent B]** | [e.g., Writer] | Drafting content based on research. |
| **[Sub-Agent C]** | [e.g., Editor] | Checking for grammar and tone consistency. |

---

## 3. Workflow Strategy & State
*Define how the supervisor moves through the task.*

**Execution Pattern:**
* [ ] **Sequential:** Agent A -> Agent B -> Agent C.
* [ ] **Parallel:** Agents A and B work at the same time; Agent C merges.
* [ ] **Iterative/Cyclic:** Supervisor can send work back to an agent for "re-work."

**Shared State (Memory):**
What information must be passed between agents? (e.g., `research_notes`, `draft_v1`, `feedback_log`).

---



## 4. Routing & Decision Logic
*How does the supervisor decide who does what?*

* **Trigger 1:** If the user provides a URL -> Delegate to **Researcher**.
* **Trigger 2:** If the Researcher provides data -> Delegate to **Writer**.
* **Trigger 3:** If the Writer's draft is > 500 words -> Delegate to **Editor**.

---

## 5. Synthesis & Reporting
**Final Assembly:** How should the supervisor combine the individual outputs?
1.  **Summary:** Briefly explain the steps taken (e.g., "I researched X, wrote Y, and verified Z").
2.  **The Artifact:** Present the final code, document, or answer.
3.  **Disclaimer:** Add any necessary warnings or "human-needed" checks.

---

## 6. Failure Modes & Conflict Resolution
* **Sub-Agent Timeout:** What if a sub-agent doesn't respond?
* **Conflicting Info:** If Agent A and Agent B provide contradictory data, how does the supervisor decide which is "correct"?
* **Escalation:** At what point does the supervisor stop trying and ask the Human for help?

---

## 7. Performance Benchmarks
* **Handoff Efficiency:** Time taken between sub-agent transitions.
* **Accuracy of Delegation:** Percentage of tasks routed to the correct sub-agent.
* **Synthesis Quality:** Does the final output feel cohesive or disjointed?