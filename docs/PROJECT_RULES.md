# Project Rules & Standards

## 1. Language & Internationalization
- **English Only**: All documentation, code comments, variable names, commit messages, and artifacts must be written in English.
- **Standards**: Follow standard international coding conventions (PEP 8 for Python).

## 2. Documentation
- Keep `README.md` up to date with architecture and setup instructions.
- Ensure all API endpoints are documented (e.g., via FastAPI auto-docs).

## 3. Code Quality
- Use type hints in Python.
- Maintain modularity (State, Nodes, Graph, API).
- Ensure DB models are clearly defined in `models.py`.

## 4. AI & Agents
- Prompts should be clear and structured.
- Use `LangGraph` for state management.
- Ensure new nodes are added to `nodes.py` and connected in `graph.py`.
