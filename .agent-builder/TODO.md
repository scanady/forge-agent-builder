### 1. Multi-Agent Systems

This group focuses on the collaboration and communication between multiple specialized agents to solve complex tasks.

| Pattern Type | Description | Design Representation |
| --- | --- | --- |
| **Network** | Uses a router to send tasks to specialized agents based on the nature of the request. | `User → Router → Specialized Agents` |
| **Supervisor** | A central supervisor agent orchestrates and manages the work of different sub-agents. | `User → Supervisor Agent ↔ Sub-Agents` |
| **Hierarchical Teams** | A supervisor orchestrates several teams of agents rather than just individuals. | `Supervisor → Multiple Agent Teams` |

---

### 2. Planning Agents

These patterns prioritize the agent's ability to break down a goal into smaller, actionable subtasks.

| Pattern Type | Description | Design Representation |
| --- | --- | --- |
| **Plan-and-Execute** | A planner generates subtasks; specialized agents execute them and report back for potential re-planning. | `Planner → Ordered Subtasks → Workers → Feedback` |
| **ReWOO** | Integrates multi-step planning with variable substitution; the entire plan is created upfront without intermediate observation steps. | `Planner → Fixed Plan → Worker Agents → Result` |

---

### 3. Reflection & Critique

These patterns use iterative loops to improve output quality through self-correction or evaluation.

| Pattern Type | Description | Design Representation |
| --- | --- | --- |
| **Basic Reflection** | A two-agent loop where a generator creates content and a critique provides feedback for improvement. | `Generator ↔ Critique Loop` |
| **Reflexion** | An advanced framework using verbal feedback, self-critique, and episodic memory to improve responses over time. | `Actor + Self-Reflection + Memory ↔ Evaluator` |
| **Tree of Thoughts** | Explores multiple reasoning paths and prunes those unlikely to lead to a solution. | `Expand → Score → Prune (Search Tree)` |
