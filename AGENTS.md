# A short bullet list of the most critical rules the agent must follow before doing anything

- [ ] Read this file and `README.md` before acting.
- [ ] Update `CHANGELOG.md` for user-facing changes.
- [ ] Never try to read `uv.lock`

# A table or list of project-specific commands for install, lint, test, build, and span dev server

| Task                 | Command        |
|----------------------|----------------|
| Run unit tests       | `./.venv/bin/pytest tests`             |

# Feature development and decision making

- Make small, targeted changes instead of building for hypothetical future needs.
- If something is unclear, ask before making assumptions.

# UI and architecture guidelines

- Use existing design system components.
- Avoid inline styles.
- Follow current domain boundaries.
- Prefer extending existing services.