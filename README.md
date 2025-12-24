# Forge Agent Builder

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Table of Contents

- [Overview](#overview)
- [What is Forge Agent Builder?](#what-is-forge-agent-builder)
- [Core Components](#core-components)
- [Quick Start](#quick-start)
- [Agent Development Workflow](#agent-development-workflow)
- [Contributing](#contributing)
- [License](#license)

## Overview

**Forge Agent Builder** is a framework for rapidly designing, specifying, planning, and implementing autonomous AI agents. It provides a structured workflow and collection of prompts/templates to guide teams through the entire agent development lifecycle.

Rather than starting from scratch, Forge Agent Builder gives you a proven methodology to:
- **Specify** agent behavior, tone, and capabilities
- **Define Persona** for agent communication style and personality
- **Clarify** agent requirements and success criteria
- **Plan** architecture and implementation details
- **Tasks** for the implementation
- **Implement** and test the agent
- **Generate** comprehensive documentation

## What is Forge Agent Builder?

Forge Agent Builder is not a single agent—it's a **meta-framework** consisting of:

1. **Forge Agent Suite**: Specialized agents (Specify, Clarify, Plan, Tasks, Implement)
2. **Prompt Library**: Prompts that trigger each agent
3. **Agent Templates**: Starting templates for different agent patterns
4. **Documentation Generators**: Automated README and documentation creation

## Core Components

#### Agent Definitions - `.github/agents/`

Agent configuration and definition files:

- **`forge.agent.specify.agent.md`**: Specify agent definition
- **`forge.agent.clarify.agent.md`**: Clarify agent definition
- **`forge.agent.plan.agent.md`**: Plan agent definition
- **`forge.agent.tasks.agent.md`**: Tasks agent definition
- **`forge.agent.implement.agent.md`**: Implement agent definition

#### Agent Prompts - `.github/prompts/`

Prompts that trigger each agent:

- **`forge.agent.specify.prompt.md`**: Instructions for specifying detailed agent behavior and capabilities
- **`forge.agent.clarify.prompt.md`**: Questions and methodology for clarifying agent requirements
- **`forge.agent.plan.prompt.md`**: Architecture and technical planning guidance
- **`forge.agent.tasks.prompt.md`**: Task breakdown and milestone planning
- **`forge.agent.implement.prompt.md`**: Code generation and implementation strategy

#### Agent Templates - `.agent-builder/core/`

Starting templates for building new agents:

- **`basic-agent-template.md`**: Simple agent specification template
- **`supervisor-agent-template.md`**: Multi-agent supervisor pattern
- **`tool-use-agent-template.md`**: Agent with tool/function calling

## Quick Start 

See **[GETTING STARTED](GETTING_STARTED.md)** for details.

### Create a New Agent

1. **Use Nexus Specify Agent** to detail behavior:
   - Define agent persona and communication style
   - List capabilities and tools
   - Specify success metrics

2. **Use Nexus Clarify Agent** to refine requirements:
   - Ask clarifying questions about agent purpose, scope, and constraints
   - Document acceptance criteria and edge cases

3. **Use Nexus Plan Agent** to design architecture:
   - Plan state management and data flow
   - Define nodes/graph structure
   - Design tool schemas

4. **Use Nexus Tasks Agent** to break down implementation:
   - Create a task list and milestones
   - Assign priorities and dependencies

5. **Use Nexus Implement Agent** to generate code:
   - Generate agent implementation
   - Create unit and integration tests
   
6. **Use Nexus Document Agent** to generate documentation:
   - Produce documentation

## Agent Development Workflow

The typical Agent Builder workflow:

```
1. SPECIFY
   └─> What is the agent's personality?
       What capabilities does it need?

2. PERSONA
   └─> How should the agent communicate?
       What is its tone and values?
            
3. CLARIFY
   └─> What problem does this agent solve?
       What are the constraints?
            
4. PLAN
   └─> What is the architecture?
       How should data flow?

5. TASKS
   └─> What are the implementation steps?
       What are the milestones?

6. IMPLEMENT
   └─> Generate the code
       Write tests
       
6. DOCUMENT
   └─> Auto-generate README (`forge-document-readme.prompt.md`)
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
   - Add new templates in `.agent-builder/core/`
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
- **Improve existing templates**: Enhance `.agent-builder/core/` with new patterns
- **Create example agents**: Build complete agents that showcase the framework
- **Improve documentation**: Help clarify the agent development process
- **Report issues**: Found a bug or limitation? Let us know

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

**Get Started**: Use the Nexus Agent Suite to build your first agent. Begin with `.agent-builder/core/` and follow the workflow outlined above.
