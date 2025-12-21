# Project Instructions

## Project Structure
- Source code is in `src/`.
- Tests are in `tests/`.
- Agent specifications are in `agent-specs/`.

## Python & LangGraph
- Use Python 3.10+ features (type hinting).
- Follow LangGraph patterns for state management and node definition.
- Ensure all nodes in the graph are properly typed with the state schema.

## Development Environment
- The virtual environment (`.venv`) is automatically activated when opening new terminals.
- This is configured via `.vscode/settings.json` with `python.terminal.activateEnvironment: true`.
- The Python interpreter is set to `${workspaceFolder}/.venv/Scripts/python.exe`.

## Testing
- Write unit tests for individual nodes.
- Write integration tests for the full graph.
- Use `pytest` for running tests.

## Documentation
- Add docstrings to all functions and classes.
- Update `plan.md` or `spec.md` if architectural changes are made.
