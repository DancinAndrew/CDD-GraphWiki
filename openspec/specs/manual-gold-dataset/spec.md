# manual-gold-dataset Specification

## Purpose
TBD - created by archiving change bootstrap-cdd-graphwiki. Update Purpose after archive.
## Requirements
### Requirement: Create Manual Gold Clauses
The MVP SHALL include at least 10 manually segmented clause examples before automated clause segmentation is trusted.

#### Scenario: Clause segmentation is evaluated
- **WHEN** a parser segments the MVP source corpus
- **THEN** its output can be compared against the 10 manually segmented clause examples

### Requirement: Create Manual Gold Obligations
The MVP SHALL include at least 10 manually extracted obligation examples with actor, action, object, conditions, exceptions, required evidence, source clauses, confidence, and review status.

#### Scenario: Obligation extraction is evaluated
- **WHEN** an extraction prompt or rule pipeline produces obligations
- **THEN** its output is compared against the manual gold obligations

### Requirement: Create Expected Customer Outcomes
The MVP SHALL include at least 5 structured customer profiles and 5 expected CDD / EDD checklist outputs.

#### Scenario: CDD decisioning is evaluated
- **WHEN** the decision engine processes a gold customer profile
- **THEN** its checklist output can be compared to the expected decision, required documents, risk triggers, citations, and review flags

### Requirement: Include Conflict Examples
The MVP SHALL include at least 3 manually authored conflict examples covering internal policy versus external regulation, stricter-than relationships, and unresolved human review cases.

#### Scenario: Conflict appears in checklist
- **WHEN** a customer checklist depends on a conflicted rule
- **THEN** the checklist output shows the conflict and marks the case for human review

