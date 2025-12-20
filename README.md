# Agent Builder

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Table of Contents

- [Overview](#overview)
- [What is Agent Builder?](#what-is-agent-builder)
- [Core Components](#core-components)
- [Quick Start](#quick-start)
- [Agent Development Workflow](#agent-development-workflow)
- [Contributing](#contributing)
- [License](#license)

## Overview

**Agent Builder** is a framework for rapidly designing, specifying, planning, and implementing autonomous AI agents. It provides a structured workflow and collection of prompts/templates to guide teams through the entire agent development lifecycle.

Rather than starting from scratch, Agent Builder gives you a proven methodology to:
- Clarify agent requirements and success criteria
- Specify agent behavior, tone, and capabilities
- Plan architecture and implementation details
- Implement and test the agent
- Generate comprehensive documentation

## What is Agent Builder?

Agent Builder is not a single agent—it's a **meta-framework** consisting of:

1. **Forge Agent Suite**: Specialized agents (Clarify, Specify, Plan, Implement, Tasks)
2. **Prompt Library**: Pre-written instructions for each agent
3. **Agent Templates**: Starting templates for different agent patterns
4. **Documentation Generators**: Automated README and documentation creation

## Tech Stack

- **Prompt Management**: Markdown-based prompt templates in `.github/prompts/`
- **Documentation**: Automated README generation via Forge agents

## Core Components

### `.github/prompts/` - Agent Prompts

Pre-written prompts that guide each Forge agent:

- **`forge.agent.clarify.prompt.md`**: Questions and methodology for clarifying agent requirements
- **`forge.agent.specify.prompt.md`**: Instructions for specifying detailed agent behavior and capabilities
- **`forge.agent.plan.prompt.md`**: Architecture and technical planning guidance
- **`forge.agent.implement.prompt.md`**: Code generation and implementation strategy
- **`forge.agent.tasks.prompt.md`**: Task breakdown and milestone planning

### `.github/agents/` - Agent Definitions

Agent configuration and definition files:

- **`forge.agent.clarify.agent.md`**: Clarify agent definition
- **`forge.agent.specify.agent.md`**: Specify agent definition
- **`forge.agent.plan.agent.md`**: Plan agent definition
- **`forge.agent.implement.agent.md`**: Implement agent definition
- **`forge.agent.tasks.agent.md`**: Tasks agent definition

### `.agent-builder/templates/` - Agent Templates

Starting templates for building new agents:

- **`basic-agent.template.md`**: Simple agent specification template
- **`supervisor-agent.template.md`**: Multi-agent supervisor pattern
- **`tool-use-agent.template.md`**: Agent with tool/function calling

## Quick Start

### Create a New Agent

1. **Start with a template**:
   ```bash
   cp .agent-builder/templates/basic-agent.template.md agent-specs/my-agent/spec.md
   ```

2. **Use Nexus Clarify Agent** to refine requirements:
   - Ask clarifying questions about agent purpose, scope, and constraints
   - Document acceptance criteria and edge cases

3. **Use Nexus Specify Agent** to detail behavior:
   - Define agent persona and communication style
   - List capabilities and tools
   - Specify success metrics

4. **Use Nexus Plan Agent** to design architecture:
   - Plan state management and data flow
   - Define nodes/graph structure
   - Design tool schemas

5. **Use Nexus Implement Agent** to generate code:
   - Generate Python agent implementation
   - Create unit and integration tests
   - Produce documentation

## Agent Development Workflow

The typical Agent Builder workflow:

```
1. CLARIFY
   └─> What problem does this agent solve?
       What are the constraints?
       
2. SPECIFY
   └─> What is the agent's personality?
       What capabilities does it need?
       
3. PLAN
   └─> What is the architecture?
       How should data flow?
       
4. IMPLEMENT
   └─> Generate the code
       Write tests
       
5. DOCUMENT
   └─> Auto-generate README
       Update specifications
```

Each step produces artifacts that feed into the next, ensuring alignment and reducing rework.

## Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository** on GitHub
2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes** following the guidelines in [`.github/copilot-instructions.md`](.github/copilot-instructions.md):
   - Add new prompts in `.github/prompts/`
   - Add new agent definitions in `.github/agents/`
   - Add new templates in `.agent-builder/templates/`
   - Use Python 3.10+ features with type hints
   - Follow LangGraph patterns for state management
   - Add docstrings to all functions and classes
4. **Test your changes**:
   ```bash
   pytest tests/
   ```
5. **Commit with clear messages**:
   ```bash
   git commit -m "feat: add new agent prompt or template"
   ```
6. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```
7. **Open a Pull Request** with a clear description of changes and rationale

### Ways to Contribute

- **Add new agent prompts**: Create specialized prompts for specific agent types
- **Improve existing templates**: Enhance `.agent-builder/templates/` with new patterns
- **Create example agents**: Build complete agents that showcase the framework
- **Improve documentation**: Help clarify the agent development process
- **Report issues**: Found a bug or limitation? Let us know

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

**Get Started**: Use the Nexus Agent Suite to build your first agent. Begin with `.agent-builder/templates/` and follow the workflow outlined above.
