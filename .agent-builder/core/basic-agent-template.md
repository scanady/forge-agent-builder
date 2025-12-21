# Agent Spec: [Agent Name]

**Version:** 1.0.0  
**Status:** [Draft/In-Review/Approved]  
**Owner:** @username  

---

## 1. Executive Summary
**High-Level Goal:** A one-sentence description of what this agent accomplishes (e.g., "Triages incoming GitHub issues and labels them based on repository priority").

**User Value:** Why are we building this? What pain point does it solve?

---

## 2. Persona & Voice
**Role:** [e.g., Expert Technical Writer / Senior DevOps Engineer / Empathetic Support Representative]

**Tone and Style:**
* [Attribute 1: e.g., Concise]
* [Attribute 2: e.g., Professional but friendly]
* [Attribute 3: e.g., Uses technical terminology accurately]

---

## 3. Scope & Objectives
### Goals (What the agent MUST do)
* [ ] Goal 1
* [ ] Goal 2

### Non-Goals (What the agent MUST NOT do)
* [ ] Non-Goal 1 (e.g., "Do not attempt to write code for proprietary internal libraries")
* [ ] Non-Goal 2 (e.g., "Do not make financial commitments")

---

## 4. Operational Instructions (The "System Prompt")
*Note: This section serves as the foundation for the agent's core instructions.*

1. **Step 1:** Analyze the input for...
2. **Step 2:** Search for information using the [Tool Name] if...
3. **Step 3:** Format the response as...

---

## 5. Tools & Capabilities
| Tool Name | Purpose | Data Input/Output |
| :--- | :--- | :--- |
| `search_docs` | Access internal documentation | Query string -> Markdown text |
| `github_api` | Fetch or comment on issues | Issue ID -> JSON object |
| `web_search` | Find external context | URL/Query -> Text summary |

---

## 6. Safety & Guardrails
* **Red-Lines:** [e.g., "Never disclose API keys or internal environment variables."]
* **Fallback Strategy:** If the agent is unsure or lacks data, it should say: "[Standard Refusal Message]"
* **Human-in-the-loop (HITL):** [e.g., "Requires manual approval before posting to public channels."]

---

## 7. Evaluation & Success Metrics
### Gold Dataset (Test Cases)
* **Input:** "..." -> **Expected Output:** "..."
* **Input:** "..." -> **Expected Output:** "..."

### Success Metrics
* **Accuracy:** Must match the Gold Dataset with >90% similarity.
* **Latency:** Response time should be under 3 seconds.
* **Cost:** Average cost per execution < $0.05.

---

## 8. Dependencies
* **Model:** [e.g., GPT-4o, Claude 3.5 Sonnet]
* **RAG Sources:** [e.g., Vector DB 'ProductDocs_v2']
* **Triggers:** [e.g., Webhook from Slack, User Query]