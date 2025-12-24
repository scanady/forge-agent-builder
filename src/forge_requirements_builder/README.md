# Forge Requirements Builder

A 5-agent orchestrated network built with LangGraph that guides teams through the complete requirements lifecycle: Discovery → Authoring → Quality → Prioritization → Synthesis.

## Project Status

**Current Phase:** Foundation Complete (Phase 1 of 7)  
**Implementation:** 18/200+ tasks complete  
**Next Phase:** Tools Implementation (Phase 2)

## Architecture Overview

### Multi-Agent Network

- **Orchestrator Node**: Routes work, manages workflow, synthesizes final deliverable
- **Discovery Agent**: Conducts interactive discovery, captures requirements
- **Authoring Agent**: Transforms requirements into user stories with INVEST principles
- **Quality Agent**: Validates requirements on 4 dimensions (pragmatic approach)
- **Prioritization Agent**: Ranks requirements using RICE/MoSCoW/Kano/Value-Effort
- **Synthesis Node**: Assembles 10-section requirements document

### Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Orchestration | LangGraph | Stateful workflows, conditional routing, human-in-the-loop |
| LLM | OpenAI GPT-4o | Strong reasoning for requirements analysis |
| Language | Python 3.10+ | Type hints, async support, modern features |
| State | Pydantic v2 | TypedDict state schema, validation |
| UI | Streamlit | Rapid prototyping, real-time chat interface |
| Testing | Pytest | Unit, integration, behavioral tests |

## What's Been Implemented (Phase 1)

### ✅ State Management (`state.py`)

**Domain Models (Pydantic):**
- `RequirementRaw` - Raw requirements from discovery
- `UserStory` - Stories with acceptance criteria and DoD
- `QualityIssue` - Issues from 4-dimension validation
- `AcknowledgedRisk` - Risks user accepted
- `PrioritizedRequirement` - Ranked requirements with rationale

**Shared State:**
- `ForgeRequirementsState` (TypedDict) - 18 fields for all workflow phases
- `create_project_state()` - State initialization
- `serialize_state()` / `deserialize_state()` - Persistence support

### ✅ Utilities (`utils.py`)

**Content Detection:**
- `detect_content_type()` - Smart phase detection (user stories, requirements, prioritized, raw ideas)

**Conversation Management:**
- `ConversationHistoryManager` - Add messages, retrieve context, format for prompts

**Logging:**
- `setup_logging()` - Structured logging with project_id context
- `ProjectLogger` - Context-aware logger

**Error Handling:**
- `@retry_with_backoff` - Exponential backoff decorator
- `FallbackHandler` - Primary/fallback execution patterns

### ✅ Project Structure

```
src/forge_requirements_builder/
├── __init__.py           # Package initialization
├── state.py              # State schema and models
├── utils.py              # Shared utilities
├── requirements.txt      # Dependencies
└── .env.example          # Configuration template

tests/forge_requirements_builder/
└── __init__.py

projects/                 # Project persistence (created)
```

## Next Steps (Phase 2: Tools Implementation)

### Tasks to Complete

1. **Discovery Agent Tools** (Tasks 2.1.1-2.1.4)
   - `extract_from_document()` - Parse PDF/DOCX/TXT files
   - `validate_requirement_capture()` - Validate requirement completeness
   - Document parsers for PDF and DOCX

2. **Authoring Agent Tools** (Tasks 2.2.1-2.2.3)
   - `validate_user_story()` - Validate story format
   - User story template formatter
   - Acceptance criteria validator

3. **Quality Agent Tools** (Tasks 2.3.1-2.3.5)
   - `validate_requirements_quality()` - 4-dimension validation
   - Ambiguity detection
   - Completeness checker
   - Consistency validator
   - Testability checker

4. **Prioritization Agent Tools** (Tasks 2.4.1-2.4.6)
   - `apply_prioritization_framework()` - Apply RICE/MoSCoW/Kano/Value-Effort
   - Framework-specific calculators (RICE, MoSCoW, Kano, Value-Effort)
   - Dependency graph analyzer

## Installation & Setup

### Prerequisites

- Python 3.10 or higher
- OpenAI API key

### Quick Start

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r src/forge_requirements_builder/requirements.txt

# Configure environment
cp src/forge_requirements_builder/.env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### Verify Installation

```bash
# Check Python version
python --version  # Should be 3.10+

# Verify core dependencies
pip freeze | grep -E "langgraph|pydantic|openai"

# Run tests (when implemented)
pytest tests/forge_requirements_builder/
```

## Development Workflow

### Task Tracking

All tasks are tracked in [tasks.md](../../agent-specs/forge-requirements-builder/tasks.md) with:
- ✅ Completed tasks marked with `[x]`
- 📝 Active tasks marked with `[ ]`
- References to plan.md and spec.md
- Verification criteria for each task

### Testing Strategy

1. **Unit Tests** - Individual functions and nodes
2. **Integration Tests** - Phase-to-phase transitions
3. **Behavioral Tests** - Persona compliance
4. **Validation Tests** - Spec compliance

### Code Standards

- Type hints for all functions (Python 3.10+)
- Docstrings with Args/Returns/Raises
- Pydantic models with examples
- Structured logging with context
- Error handling with retry/fallback patterns

## Documentation

- **Specification**: [NETWORK-SPEC.md](../../agent-specs/forge-requirements-builder/NETWORK-SPEC.md)
- **Implementation Plan**: [plan.md](../../agent-specs/forge-requirements-builder/plan.md)
- **Task Breakdown**: [tasks.md](../../agent-specs/forge-requirements-builder/tasks.md)
- **Persona Design**: [PERSONA-EXPERT-SYSTEMS-DESIGNER.md](../../agent-specs/forge-requirements-builder/PERSONA-EXPERT-SYSTEMS-DESIGNER.md)

## Progress Tracking

### Phase 1: Foundation ✅ Complete (18/18 tasks)
- [x] Environment & dependencies
- [x] State schema (5 Pydantic models + TypedDict)
- [x] Shared utilities (content detection, logging, error handling)

### Phase 2: Tools Implementation 📝 Next (17 tasks)
- [ ] Discovery Agent tools
- [ ] Authoring Agent tools
- [ ] Quality Agent tools
- [ ] Prioritization Agent tools

### Phase 3: Nodes Implementation (47 tasks)
### Phase 4: Graph Assembly (17 tasks)
### Phase 5: Testing (35 tasks)
### Phase 6: UI & Deployment (20 tasks)
### Phase 7: Documentation (11 tasks)

**Total Progress: 18/200+ tasks (9%)**

## License

Copyright © 2025 Forge Agent Builder

## Contact

For questions about implementation, refer to:
- Implementation mode instructions: `.github/prompts/forge.agent.implement.prompt.md`
- Design principles: `.agent-builder/agent-design-principles.md`
