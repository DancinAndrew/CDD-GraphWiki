# ADR 0001: Use OpenSpec And ADRs For Spec-First Development

Status: Accepted  
Date: 2026-05-15

## Context

CDD-GraphWiki is still early. The repo has research notes and a roadmap, but no code, schemas, tests, data fixtures, or implementation workflow. The project needs a way to keep requirements, acceptance scenarios, implementation tasks, and architecture rationale synchronized before implementation starts.

## Decision

Use OpenSpec as the controlling workflow for requirement changes, capability specs, design notes, and task tracking. Use ADRs under `docs/adr/` to record material architecture decisions and alternatives considered.

## Alternatives Considered

- Roadmap only: simple, but weak for verification and future implementation tracking.
- ADRs only: captures decisions, but does not define requirement scenarios or tasks.
- GitHub issues only: useful later, but too operational before the product shape is stable.
- A single `SPEC.md` only: good for discussion, but less structured for capability-level change tracking.

## Consequences

- Every meaningful product or architecture change should update `SPEC.md`, OpenSpec artifacts, and ADRs when relevant.
- Implementation should not outrun accepted requirements.
- Future contributors can understand both what the system must do and why key decisions were made.

