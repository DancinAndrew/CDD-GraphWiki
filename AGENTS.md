# Project Agent Instructions

CDD-GraphWiki uses a Python-first subset of Everything Claude Code (ECC), adapted for a spec-first AML / CDD compliance knowledge-compilation project.

## Source Profile

- Source repo: `affaan-m/everything-claude-code`
- Source snapshot: `4e66b2882da9afb9747468b08a253ca2f09c85f3` from 2026-04-21
- ECC material copied locally under `.agents/`
- Codex-specific settings live under `.codex/`

## Project Context

- Product: AML / CDD regulatory knowledge compilation and compliance reasoning.
- Primary planning files: `SPEC.md`, `openspec/config.yaml`, `openspec/changes/bootstrap-cdd-graphwiki/`, and `docs/adr/`.
- Current phase: specification and architecture bootstrap.
- No runtime application, dependency setup, source parser, graph engine, UI, or tests have been added yet.

## Operating Rules

- Prefer Python for application code, scripts, tests, and automation unless the project later declares another stack.
- Do not install packages, enable MCP servers, run package-manager setup, or add runtime services without user approval.
- If the dependency, framework, or module choice is uncertain, explain the options and ask before changing project setup.
- Use existing project files as the source of truth once they exist: `pyproject.toml`, `requirements*.txt`, lock files, Makefiles, CI, and docs.
- Keep changes scoped to the requested work. Avoid broad refactors unless they are necessary for correctness.
- Preserve user changes in the worktree. Never revert unrelated edits.

## CDD-GraphWiki Constraints

- Do not turn the project into a generic "upload PDFs and chat" RAG app.
- Keep the MVP source corpus small until the core contracts are stable: FATF Recommendation 10, MAS Notice 626 CDD / EDD clauses, and one mock internal AML / KYC policy.
- Preserve clause-level provenance for every derived object.
- Route legal, regulatory, threshold, conflict, required-evidence, or escalation decisions through human review.
- Capture broad product changes in `SPEC.md`, requirement changes in OpenSpec, and architecture decisions in ADRs.

## Behavioral Guardrails

- Surface assumptions before consequential changes. If multiple interpretations would lead to materially different implementations, explain the tradeoff and ask.
- Bias toward the simplest maintainable solution. Do not add speculative features, unused flexibility, or single-use abstractions.
- Make surgical edits. Match the surrounding style, avoid cleaning up unrelated code, and ensure every changed line traces back to the request.
- Clean up only the unused imports, variables, functions, or files made obsolete by your own changes.
- For multi-step work, define brief success criteria before implementation and loop until they are verified.
- For non-trivial bugs and features, prefer a test that reproduces or protects the behavior before changing implementation when practical.

## Workflow

1. Inspect the repo before changing code.
2. Read `SPEC.md`, `openspec/config.yaml`, and the active OpenSpec change before implementing new behavior.
3. Search for existing project patterns before creating new abstractions.
4. For non-trivial features or bug fixes, write or update tests first when practical.
5. Implement the smallest maintainable change that satisfies the requirement.
6. Verify with the commands already configured by the project. For OpenSpec changes, prefer `openspec validate bootstrap-cdd-graphwiki --strict --no-interactive` when the active change is relevant.
7. Review `git diff` before finishing and document any verification that could not be run.

## Python Standards

- Follow PEP 8 and use type annotations on public functions and important internal boundaries.
- Prefer explicit, readable code over clever shortcuts.
- Use dataclasses, typed dictionaries, protocols, or small classes when they clarify data contracts.
- Validate inputs at system boundaries and raise specific exceptions.
- Keep secrets out of code. Use environment variables or an approved secret manager.
- Prefer pytest for tests once the project has approved testing dependencies.

## Local ECC References

- Core skills: `.agents/skills/`
- Common rules: `.agents/rules/common/`
- Python rules: `.agents/rules/python/`
- Codex roles and config: `.codex/`

The copied ECC skills/rules are advisory project knowledge. User instructions and the active Codex system/developer instructions remain higher priority.
