## ADDED Requirements

### Requirement: Track Requirement Changes With OpenSpec
The project SHALL use OpenSpec changes to track new capabilities, modified requirements, design decisions, and implementation tasks.

#### Scenario: New capability is proposed
- **WHEN** a new product capability is added
- **THEN** it is represented in an OpenSpec proposal, spec file, design note when needed, and task checklist before implementation

### Requirement: Track Architecture Decisions With ADRs
The project SHALL record material architecture decisions in `docs/adr/` with context, decision, alternatives considered, and consequences.

#### Scenario: Graph storage decision is made
- **WHEN** the project chooses JSON, RDF, Neo4j, SQLite, or another graph storage approach
- **THEN** that choice is recorded as an ADR before implementation depends on it

### Requirement: Require Human Review For Material Compliance Changes
The system SHALL mark material compliance interpretations as requiring human review until approved.

#### Scenario: Threshold rule changes
- **WHEN** a source changes a regulatory threshold, timing requirement, escalation requirement, or evidence requirement
- **THEN** the derived wiki page, obligation, conflict, or checklist item is marked for human review

### Requirement: Preserve Audit Trail
The system SHALL preserve enough metadata to explain what source text produced each wiki claim, structured obligation, conflict record, and checklist item.

#### Scenario: Regulator asks for evidence
- **WHEN** a reviewer asks why a checklist required EDD
- **THEN** the system can show source clauses, derived obligations, triggering customer context fields, and review status

