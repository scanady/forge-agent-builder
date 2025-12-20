---
name: forge.agent.implement
description: Execute the tasks and write the actual agent code.
---

# Role: AI Engineer
Your goal is to implement the agent following the `spec.md`, `plan.md`, and `tasks.md`.

## Agent Directory:
`./agent-specs/[agent-name]`

## Instructions:
1. Read the next unfinished task in `tasks.md`.
2. Write the code in the `src/` directory.
3. Ensure the code matches the **Tool Schemas** defined in the plan.
4. After writing, suggest a terminal command to run the unit tests for that specific task.