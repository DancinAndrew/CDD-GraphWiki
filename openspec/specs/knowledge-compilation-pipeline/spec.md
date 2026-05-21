# knowledge-compilation-pipeline Specification

## Purpose
TBD - created by archiving change bootstrap-cdd-graphwiki. Update Purpose after archive.
## Requirements
### Requirement: Preserve Raw Source Provenance
The system SHALL preserve each regulatory or internal policy source as an immutable source record with issuer, jurisdiction, version, retrieval metadata, local path or source URL, and content hash when available.

#### Scenario: Source document registered
- **WHEN** a FATF, MAS, or mock internal policy source is added to the MVP corpus
- **THEN** the system records enough metadata to identify the source, version, retrieval date, and storage location

### Requirement: Segment Sources Into Stable Clauses
The system SHALL segment source documents into stable clause records that preserve hierarchy, section references, parent-child relationships, raw text, and source document references.

#### Scenario: Clause can be cited
- **WHEN** a clause is used by an obligation, wiki page, conflict, or checklist item
- **THEN** the derived object references the stable clause identifier rather than only a free-text excerpt

### Requirement: Separate Wiki Pages From Reasoning Objects
The system SHALL treat human-readable wiki concept pages as a presentation and review layer, not as the only source of compliance reasoning.

#### Scenario: Concept page is generated from structured objects
- **WHEN** the system creates a Beneficial Owner concept page
- **THEN** the page includes aliases, definitions, related concepts, linked obligations, and source clauses while preserving structured obligations separately

### Requirement: Support Machine-Readable Regulatory Graph Construction
The system SHALL represent concepts, clauses, obligations, evidence requirements, jurisdictions, customer types, risk triggers, conflicts, and review cases as typed graph-ready records.

#### Scenario: High-risk corporate customer query
- **WHEN** a query asks which obligations apply to a corporate customer with high-risk UBO jurisdiction and complex ownership
- **THEN** the system can identify applicable obligations through structured records and graph relationships with source citations

