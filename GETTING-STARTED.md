# Forge Agent Builder - Getting Started

This guide walks you through creating an AI agent using the Forge workflow.

## The Forge Workflow

```
Specify → Persona → Clarify → Plan → Tasks → Implement → Test → Deploy
```

---

### 1. **Specify** - define what your agent does.

Create a clear specification document including agent name, purpose, key capabilities, core workflows, and safety guidelines and constraints.

**Example Usage**: `/forge.agent.specify A Requirements Assistant that helps users discover software requirements through Q&A or document analysis.`

**Output**: `agent-specs/your-agent/spec.md`

---

### 2. **Persona** - define agent personality and communication style.

Create a persona that defines how your agent presents itself: tone, values, communication style, and how it relates to users. This can be developed after Specify but should be finalized before Implement.

**Example Usage**: `/forge.agent.persona A professional yet approachable assistant that listens actively, asks clarifying questions, and provides clear, organized summaries.`

**Output**: Updated `spec.md` with persona details, or separate `persona.md` section

---

### 3. **Clarify** - answer critical questions about your agent.

Refine the specification by addressing: How should output be handed off? Who decides when the session ends? Should data be modifiable or append-only? What's the output format? These answers ensure your spec is unambiguous.

**Example Usage**: `/forge.agent.clarify` (interactive Q&A session)

**Output**: Updated `spec.md` with clarifications documented

---

### 4. **Plan** - design the technical architecture.

Create an implementation plan covering tech stack (LLM, framework, frontend), state schema, node definitions, and routing logic.

**Example Usage**: `/forge.agent.plan Use LangGraph for orchestration, Streamlit for UI, GPT-4.1 for the LLM.`

**Output**: `agent-specs/your-agent/plan.md`

---

### 5. **Tasks** - break the plan into actionable work items.

Organize tasks by phase: Foundation, Tools, Nodes, Graph, Frontend, Testing, and Polish. Track progress by marking tasks complete as you go.

**Example Usage**: `/forge.agent.tasks` (generates structured task list)

**Output**: `agent-specs/your-agent/tasks.md`

---

### 6. **Implement** - write the code.

Work through each phase systematically: state schemas, tools, nodes, graph routing, and frontend interface. Build incrementally and test as you go.

**Example Usage**: Implement nodes in `src/your-agent/nodes.py`, routing in `src/your-agent/graph.py`, UI in `src/your-agent/streamlit_app.py`

**Output**: Source code in `src/your-agent/`

---

### 7. **Test** - validate your implementation.

Write unit tests for individual logic and integration tests for complete flows. Run tests frequently to catch issues early.

**Example Usage**: `pytest tests/your-agent/ -v`

**Output**: Test suite in `tests/your-agent/`

---

### 8. **Deploy** - launch your agent.

Setup: Create `.env` with API keys, install dependencies, and start the Streamlit app. Access at `http://localhost:8501`.

**Example Usage**: `streamlit run src/your-agent/streamlit_app.py`

**Output**: Agent running and accessible via web browser at localhost:8501

---
  
### Next Steps

1. Review `spec.md` and `plan.md` in `agent-specs/requirements-elicitation-agent/`
2. Examine the implementation in `src/requirements_elicitation_agent/`
3. Run the tests: `pytest tests/requirements_elicitation_agent/ -v`
4. Start the app and interact with it
5. Use this as a template for your own agents

---

### Documentation Files

- **spec.md**: What the agent does and how it behaves
- **plan.md**: Technical architecture and design
- **tasks.md**: Implementation work items (track progress here)
- **README.md** (in src/): Usage guide for end users
- **USAGE.md**: This getting started guide
