## ADDED Requirements

### Requirement: Produce Evidence-Backed Checklist
The system SHALL produce a CDD / EDD checklist from a structured customer context using source-linked obligations and evidence requirements.

#### Scenario: Corporate high-risk UBO triggers EDD
- **WHEN** a corporate customer has complex ownership and a high-risk UBO jurisdiction
- **THEN** the checklist decision is EDD and includes required documents, applicable obligations, risk triggers, source citations, and human review flags

### Requirement: Avoid Unconstrained Legal Answers
The system SHALL NOT present unconstrained LLM-generated legal conclusions as final checklist output without structured obligation matching and citation attachment.

#### Scenario: User asks for onboarding documents
- **WHEN** the user asks what documents are needed for a customer scenario
- **THEN** the answer is grounded in structured obligations, conflicts, and citations rather than only a natural-language model response

### Requirement: Expose Conflicts In Decision Output
The system SHALL include unresolved conflicts or supersession questions in checklist output when they affect required actions, evidence, timing, or review requirements.

#### Scenario: Internal policy is looser than regulation
- **WHEN** internal policy requires high-risk review every 12 months but an external rule requires review every 6 months
- **THEN** the checklist shows the stricter external rule, records the conflict, and requires human review

### Requirement: Preserve Decision Explainability
The system SHALL explain why a checklist item is required by referencing matched obligations, triggering customer context fields, and supporting source clauses.

#### Scenario: Source of wealth is required
- **WHEN** source of wealth appears in a checklist
- **THEN** the output identifies the risk trigger, applicable obligation, and source citation supporting that requirement

