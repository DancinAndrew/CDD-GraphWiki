# Codex Profile

This supplements the root `AGENTS.md` with Codex-specific guidance for CDD-GraphWiki.

## Python-First ECC Setup

Available local skills in `.agents/skills/`:

- `python-patterns` - Python idioms, type hints, PEP 8, package/module structure
- `python-testing` - pytest, fixtures, parametrization, mocking, coverage
- `coding-standards` - cross-project readability and code quality baseline
- `tdd-workflow` - red/green/refactor development loop
- `security-review` - secrets, input validation, auth, injection, sensitive paths
- `verification-loop` - build, type, lint, test, security, diff review
- `git-workflow` - branches, commits, PR summaries
- `search-first` - research and reuse before custom implementation
- `api-design` - REST/API design patterns
- `backend-patterns` - backend service structure, data access, caching, boundaries
- `python-dependency-consent` - approval gate before adding packages, tools, MCP servers, or services

## CDD-GraphWiki Defaults

- Treat `SPEC.md` and OpenSpec as the controlling source of truth until implementation begins.
- Prefer ADRs under `docs/adr/` for material architecture choices.
- Keep compliance outputs evidence-backed and clause-cited.
- Do not automate legal or regulatory judgment without explicit human-review gates.

## Dependency Consent

Do not install or enable packages, MCP servers, framework plugins, database services, or package-manager workflows without user approval. If a task likely needs one, give a short recommendation and wait.

Some copied ECC skills include example install commands. Treat those examples as advisory text only, not permission to run them.

## MCP Servers

ECC's reference Codex config enables GitHub, Context7, Exa, Memory, Playwright, and Sequential Thinking MCP servers. They are intentionally left disabled in this project because most launch via `npx` or external services. Enable them only after the user approves the concrete need.

## Agent Roles

Project-local role files are in `.codex/agents/`:

- `explorer` - read-only codebase evidence gathering
- `reviewer` - correctness, security, and missing-test review
- `docs_researcher` - API and release-note verification

Use these roles only when the active harness supports them and the current system instructions permit delegation.
