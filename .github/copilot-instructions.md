# Project Instructions

## Core Principles

1. **Refactor over supplement.** Prioritize clean, maintainable code. When modifying functionality, refactor existing code rather than adding workarounds. Remove obsolete logic, dead code, and unused imports immediately. Every change should leave the codebase cleaner than before.

## Project Structure
- Source code is in `src/`.
- Tests are in `tests/`.
- Agent specifications are in `agent-specs/`.

## Python & LangGraph
- Use Python 3.10+ features (type hinting).
- Follow LangGraph patterns for state management and node definition.
- Ensure all nodes in the graph are properly typed with the state schema.

## Development Environment
- This is configured via `.vscode/settings.json` with `python.terminal.activateEnvironment: true`.
- The Python interpreter is set to `${workspaceFolder}/.venv/Scripts/python.exe`.

## Testing
- Write unit tests for individual nodes.
- Write integration tests for the full graph.
- Use `pytest` for running tests.

## Documentation
- Add docstrings to all functions and classes.
- Update `plan.md` or `spec.md` if architectural changes are made.
