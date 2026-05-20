# Agent Roles

This project uses Codex role files in `.codex/agents/`.

## Available Local Roles

| Role | Purpose | When to Use |
|------|---------|-------------|
| explorer | Read-only evidence gathering | Codebase questions and impact analysis |
| reviewer | Correctness, security, and tests | Review after meaningful changes |
| docs_researcher | API and release-note verification | Version-sensitive docs questions |

## Usage Policy

- Use role delegation only when the active harness supports it and current
  system/developer instructions permit it.
- Keep delegated work concrete, bounded, and non-overlapping.
- Do not delegate work that blocks the immediate next step.
- If delegation is unavailable, perform the work locally with the same review
  standards.

## Parallel Work

Parallelize independent reads, searches, and verification tasks when the tools
support it. Keep writes coordinated and avoid overlapping ownership.
