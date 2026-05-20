---
name: python-dependency-consent
description: Use when a Python task may require new packages, frameworks, MCP servers, external services, or toolchain setup; requires asking before install or enablement.
---

# Python Dependency Consent

This project is Python-first, but dependency choices must stay explicit.

## When to Activate

- A task may require a new Python package, framework, CLI tool, MCP server, database, service, or package manager workflow.
- Existing project files do not clearly declare the needed dependency.
- Multiple viable libraries or frameworks exist and the best choice depends on project direction.

## Required Behavior

1. Inspect existing files first: `pyproject.toml`, `requirements*.txt`, lock files, README, CI, Makefile, and source imports.
2. If the dependency is already declared, use the existing project workflow.
3. If the dependency is missing or the best option is uncertain, stop before installing or enabling anything.
4. Give a short recommendation with tradeoffs and ask the user to approve the choice.
5. After approval, make the smallest setup change needed and document the command that was run.

## Default Recommendation Shape

```text
This likely needs a dependency choice.
Recommended: <package/tool> because <reason>.
Alternative: <package/tool> if <tradeoff matters>.
Do you want me to add/use <package/tool>?
```

## Verification

After an approved dependency change, run the project-declared verification command. If no command exists yet, ask before adding tooling such as pytest, ruff, mypy, pyright, uv, poetry, or pre-commit.
