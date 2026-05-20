## ADDED Requirements

### Requirement: Define Core Compliance Objects
The project SHALL define first-pass data contracts for `SourceDocument`, `Clause`, `Citation`, `Concept`, `Obligation`, `EvidenceRequirement`, `CustomerContext`, `Conflict`, `CDDChecklist`, and `ReviewCase` before implementing extraction or decisioning logic.

#### Scenario: First implementation begins
- **WHEN** implementation work starts
- **THEN** each core compliance object has an explicit JSON or YAML example and documented required fields

### Requirement: Include Provenance On Derived Objects
Every derived object SHALL include references back to the source clauses or source documents used to create it.

#### Scenario: Obligation references source
- **WHEN** an `Obligation` is created from a MAS clause
- **THEN** the obligation includes at least one `source_clause_id` and can be traced back to raw source text

### Requirement: Include Review Status On Risky Objects
Compliance objects that affect legal interpretation, regulatory thresholds, conflict resolution, required evidence, or escalation requirements SHALL include review status.

#### Scenario: Low-confidence obligation
- **WHEN** an obligation is extracted with low confidence or ambiguous conditions
- **THEN** the obligation is marked `pending_human_review`

### Requirement: Keep Customer Context Structured
Customer input SHALL be represented as a structured `CustomerContext` object rather than only a natural-language prompt.

#### Scenario: Corporate customer profile is evaluated
- **WHEN** the system evaluates a corporate customer
- **THEN** it uses structured fields such as customer type, registration jurisdiction, ownership layers, UBO status, UBO country risk, PEP exposure, and evidence availability

