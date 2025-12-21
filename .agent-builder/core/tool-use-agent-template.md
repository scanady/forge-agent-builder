# Agent Spec: [Agent Name]

**Version:** 1.0.0
**Agent Type:** Tool-Enabled / Action-Oriented
**Status:** [Draft/Approved]
**Primary Logic:** [e.g., ReAct / OpenAI Function Calling / Tool-Use Loop]

---

## 1. Objective & Capabilities
**Core Purpose:** Briefly describe what this agent does (e.g., "Fetches customer order history and updates shipping addresses in the CRM").

**Key Capabilities:**
* [ ] Capability 1 (e.g., Read access to Database X)
* [ ] Capability 2 (e.g., Write access to API Y)

---

## 2. Technical Interface (The Tools)
*Define the functions the agent can call. This section acts as the source of truth for your JSON schemas.*

### Tool: `[tool_name]`
* **Description:** What does this tool do?
* **Parameters:**
  * `param_1` (type): Description.
  * `param_2` (type): Description.
* **Returns:** Expected data format (e.g., JSON, String, List).
* **Side Effects:** Does this tool change data (Write) or just fetch it (Read)?

---

## 3. Execution Logic
*This section defines the "Brain" of the tool-use process.*

1. **Analysis:** The agent must parse the user query to identify required parameters.
2. **Validation:** Before calling a tool, the agent must check if it has the required permissions/data.
3. **Execution:** The agent calls the tool and waits for a response.
4. **Post-Processing:** The agent translates technical JSON output into a human-readable summary.

---

## 4. Error Handling & Guardrails
* **Retry Policy:** [e.g., "Retry once on 5xx errors; fail immediately on 4xx errors."]
* **Safety Boundaries:** [e.g., "Never allow SQL injections; restrict queries to 'SELECT' statements only."]
* **Empty States:** How should the agent respond if a tool returns no results?

---

## 5. Security & Auth
* **Identity:** [e.g., Agent runs under service account `agent-service-prod`]
* **Scope:** [e.g., "Can only access records where `org_id` matches the user's header."]

---

## 6. Evaluation (Gold Dataset)
| Input (User Prompt) | Expected Tool Call | Expected Final Output |
| :--- | :--- | :--- |
| "Where is order #123?" | `get_order(id=123)` | "Order #123 is currently in transit..." |
| "Delete user 5" | *Refusal* | "I do not have permission to delete users." |