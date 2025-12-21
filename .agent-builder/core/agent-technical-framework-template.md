# Technical Implementation Reference

## 1. Core Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Orchestration** | LangGraph | Complex stateful workflows, conditional routing, human-in-the-loop patterns |
| **LLM Provider** | OpenAI | Strong reasoning, context retention, structured output support |
| **Language** | Python | Type hints, async support, modern features |
| **Data Validation** | Pydantic | State schema validation, tool parameter schemas, structured outputs |
| **Frontend** | Streamlit | Rapid prototyping, file uploads, real-time chat interface |
| **Testing** | Pytest | Unit tests, integration tests, async test support |
| **MCP Integration** | Model Context Protocol | Expose agent as reusable tool for other applications |
| **Environment** | python-dotenv | Configuration management via `.env` |

---

## 2. Persona & Communication Framework

**When designing agent communication**, use these patterns:

**Behavioral Directives**
- Map each spec behavior to implementation mechanisms (node logic, routing, prompts)
- Example: Directive "Be encouraging" → All LLM prompts include positive language

**Communication Profile**
- Define voice guidelines: tone, formality, patterns
- Specify adaptive behavior based on user signals
- Document error framing and risk communication

**Implementation**
- Load persona directives from `.md` files in `persona/` directory
- Inject into LLM system messages (one per node)
- Use routing logic to enforce communication boundaries

---

## 3. Decision Authority & Guardrails

**Mapping Spec Guardrails to Implementation**

Extract guardrails from spec and determine authority level:

| Decision Type | Authority Level | Implementation Mechanism |
|---------------|-----------------|--------------------------|
| [from spec] | Autonomous / Bounded / Recommend / Escalate | [node logic / routing / LLM constraint / data validation] |

**Authority Levels**
- **Autonomous**: Agent decides alone (node logic)
- **Bounded**: Agent acts within defined constraints (state validation, routing bounds)
- **Recommend**: Agent suggests, user decides (state pending user confirmation)
- **Escalate**: Agent defers to external authority (handoff, error state)

**Implementation Patterns**
- Use routing to enforce exclusive/inclusive constraints
- Use state validation (Pydantic) for data guardrails
- Use pending state for user confirmations
- Use node logic for tone/communication guardrails

---

## 4. Frontend Deployment Options

Choose based on deployment context:

**Streamlit Web App**
- Best for: Interactive MVP, rapid iteration, file handling
- Includes: UI scaffolding, session management
- Entry point: `streamlit_app.py`

**CLI Interface**
- Best for: Testing, automation, headless environments
- Includes: Terminal interaction, batch processing
- Entry point: `main.py`

**MCP Server**
- Best for: Composability, integration with Claude Desktop and other agents
- Includes: Tool registration, protocol compliance
- Entry point: `mcp_server.py`
- Use when: Agent should be a reusable tool in other workflows

**REST API**
- Best for: Scalable deployment, multiple client integration
- Requires: Custom implementation
- Use when: Multiple frontends or services need agent access

## 5. Testing & Validation Strategy

**Forge-Specific Test Requirements**

- **Behavioral Tests**: Verify each spec behavior is implemented in node logic or prompts
- **Guardrail Tests**: Validate authority levels and decision boundaries from spec
- **Spec Goal Coverage**: Every goal has ≥1 test proving implementation
- **Non-Goal Validation**: Every explicit non-goal has exclusion logic tested


