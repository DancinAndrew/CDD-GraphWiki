## Why

CDD-GraphWiki currently has strong research notes and a roadmap, but it lacks a controlling development system that turns the idea into verifiable requirements, implementation tasks, and architectural decisions.

This change establishes OpenSpec plus ADRs as the project foundation so future work stays spec-first, evidence-backed, and scoped to an achievable AML / CDD MVP.

## What Changes

- Add a discussion-first `SPEC.md` that defines product thesis, MVP scope, non-goals, data object sketches, acceptance scenarios, evaluation, and open questions.
- Add OpenSpec artifacts for the first active change: `bootstrap-cdd-graphwiki`.
- Add requirement specs for knowledge compilation, compliance data contracts, manual gold dataset, CDD decisioning, and governance / audit.
- Add a design document explaining how the project should move from research notes to implementation.
- Add trackable OpenSpec tasks for the bootstrap and first implementation phases.
- Add ADR infrastructure under `docs/adr/` and initial ADRs for the major architectural choices.
- Add a README as the repository entry point.

## Capabilities

### New Capabilities

- `knowledge-compilation-pipeline`: Preserves sources, segments clauses, links derived objects to provenance, and separates wiki generation from machine-readable compliance reasoning.
- `compliance-data-contracts`: Defines the first structured objects needed before extraction, graph construction, or checklist generation.
- `manual-gold-dataset`: Establishes a small human-authored dataset for clauses, obligations, concept pages, customer profiles, expected checklists, and conflicts.
- `cdd-decisioning`: Produces CDD / EDD checklist output from structured customer context and source-linked obligations.
- `governance-and-audit`: Tracks material decisions, citations, conflicts, review status, and human approval requirements.

### Modified Capabilities

- None. This repository has no existing OpenSpec capabilities yet.

## Impact

- Affects project documentation and planning artifacts only.
- Adds no runtime dependencies, application services, package managers, model providers, or external integrations.
- Establishes the expected future repo structure for `schemas/`, `data/`, `knowledge/`, `src/`, and `tests/`, but does not implement those directories yet.

