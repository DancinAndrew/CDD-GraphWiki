# human-in-the-loop-audit Specification

## Purpose
TBD - created by archiving change create-human-in-the-loop-audit. Update Purpose after archive.
## Requirements
### Requirement: ReviewCase Pydantic Contract
The system SHALL define a Pydantic-validated data contract for `ReviewCase` to track the state of human intervention cases. The model MUST enforce validation on the approval status (`pending_review`, `approved`, `rejected`, `needs_evidence`) and reviewer decisions.

#### Scenario: Validate ReviewCase Schema
* **GIVEN** a dictionary containing `case_id`, `customer_id`, `checklist_id`, `review_reason`, `approval_status`, and `reviewer_decision`
* **WHEN** the system instantiates a `ReviewCase` object with these values
* **THEN** the object SHALL pass Pydantic validation and preserve type safety, raising an error if `approval_status` contains an invalid enum value.

---

### Requirement: Audit Logger Traceability and Tamper Evident
The system SHALL provide an `AuditLogger` engine to record the decision-making history. Every audit log entry MUST be chained using cryptographic hash cascading (Hash Chain) to ensure tamper-evident storage. Any unauthorized modification to past logs SHALL cause subsequent chain hashes to fail integrity verification.

#### Scenario: Write Audit Log and Validate Chain Hash
* **GIVEN** an active `AuditLogger` with multiple recorded events
* **WHEN** the system invokes `verify_integrity()` on the logger
* **THEN** it SHALL return `True` indicating a stable hash chain.
* **BUT WHEN** any attribute of an old log entry is manually altered
* **THEN** `verify_integrity()` SHALL immediately return `False`, indicating a broken integrity chain.

---

### Requirement: Human in the Loop Decision Overwrite
The system SHALL support decision overrides by authorized compliance officers. When a review case is approved with a reviewer decision, the system MUST overwrite the corresponding `CDDChecklist` decision, clear the `human_review_required` flag, and log the overwrite action.

#### Scenario: Reviewer Approves and Overwrites Checklist Decision
* **GIVEN** a corporate customer checklist with an automated decision of `standard_cdd` and `human_review_required = True`
* **WHEN** a compliance officer invokes `apply_review_decision` with `reviewer_decision = "enhanced_due_diligence"`
* **THEN** the associated `CDDChecklist` decision SHALL be updated to `enhanced_due_diligence`, the `human_review_required` flag SHALL become `False`, and a `case_reviewed` audit log entry SHALL be recorded.

---

### Requirement: Compliance Audit Package Export
The system SHALL support exporting a unified "Compliance Audit Package" for each customer profile. The exported package MUST be available in both Markdown and HTML formats. The HTML report MUST adopt the dark glassmorphic styling system and redact PII sensitive fields.

#### Scenario: Export Audit Report to HTML with Glassmorphic Style
* **GIVEN** a customer context, its final overwritten checklist, and its chained audit log entries
* **WHEN** the system invokes `generate_audit_report` for this customer
* **THEN** the system SHALL successfully write out Markdown and HTML files, containing the complete decision provenance, and any PII customer details (like `customer_id`) in the display panels SHALL be redacted.

