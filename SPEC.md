# CDD-GraphWiki SPEC

Status: Draft v0.1  
Last updated: 2026-05-15  
Controlling workflow: OpenSpec change `bootstrap-cdd-graphwiki`  
Decision log: `docs/adr/`

## 1. Product Thesis

CDD-GraphWiki is a human-readable and machine-reasonable knowledge compilation system for AML / CDD compliance.

The project MUST NOT start as a generic "upload PDFs and chat" RAG app. The system MUST first compile regulatory and internal policy text into structured, source-linked compliance objects that can support CDD / EDD decisions with evidence, conflict visibility, and human review.

## 2. MVP Scope

### 2.1 Source Corpus

The MVP SHALL use a deliberately small source corpus:

- FATF Recommendation 10
- MAS Notice 626 CDD / EDD related clauses
- One mock internal AML / KYC policy

FCA, HKMA, live bank systems, transaction monitoring, and production policy workflows are out of scope until the core data contracts and gold dataset are stable.

### 2.2 Customer Scenarios

The MVP SHALL cover at least these customer context patterns:

- individual customer
- corporate customer
- politically exposed person
- high-risk jurisdiction
- complex ownership structure
- unclear beneficial owner / UBO

### 2.3 Primary Output

The MVP SHALL produce an evidence-backed CDD / EDD checklist for a structured customer profile.

Each checklist item SHALL include:

- decision category: standard CDD, simplified CDD, or EDD
- applicable obligations
- required documents or evidence
- risk triggers
- unresolved conflicts
- human review flags
- source citations back to clause-level evidence

## 3. Users

Primary user:

- compliance analyst or compliance officer reviewing customer onboarding requirements

Secondary user:

- product or engineering builder validating that the system can compile legal/policy text into auditable data objects

## 4. Non-Goals

The MVP MUST NOT include:

- polished chatbot UI as the primary product surface
- vector database as the core architecture
- production legal judgment automation
- live financial institution integration
- broad multi-jurisdiction corpus ingestion
- transaction monitoring or suspicious activity detection
- automatic policy updates without human review

## 5. Required Capabilities

### 5.1 Knowledge Compilation Pipeline

The system SHALL preserve raw regulatory and internal policy sources, segment them into stable clause records, and connect each derived object back to source provenance.

### 5.2 Compliance Data Contracts

The system SHALL define explicit data contracts before implementation begins.

Required first-pass objects:

- `SourceDocument`
- `Clause`
- `Citation`
- `Concept`
- `Obligation`
- `EvidenceRequirement`
- `CustomerContext`
- `Conflict`
- `CDDChecklist`
- `ReviewCase`

### 5.3 Manual Gold Dataset

The system SHALL start with a small manual gold dataset before automated extraction.

Minimum gold dataset:

- 10 manually segmented clauses
- 10 manually extracted obligations
- 5 concept pages
- 5 customer profiles
- 5 expected CDD / EDD checklist outputs
- 3 conflict examples

### 5.4 CDD Decisioning

The system SHALL treat customer input as a structured `CustomerContext`, not as an unconstrained prompt.

The CDD decision layer SHALL match customer context against structured obligations, conflicts, evidence requirements, and review flags before producing checklist output.

### 5.5 Governance and Audit

The system SHALL track material architectural decisions in ADRs and requirement changes in OpenSpec.

Any output that affects regulatory thresholds, risk classification, required evidence, or escalation rules SHALL be marked as requiring human review until explicitly approved.

## 6. Canonical Object Sketches

### SourceDocument

```yaml
source_document_id: mas_notice_626
title: MAS Notice 626
issuer: MAS
jurisdiction: Singapore
version: example_version
effective_date: null
retrieval_date: 2026-05-15
source_url: null
local_path: data/sources/mas_notice_626.md
content_hash: null
```

### Clause

```yaml
clause_id: mas626_cdd_001
source_document_id: mas_notice_626
section_ref: example_section
parent_clause_id: null
raw_text: "..."
normalized_text: "..."
citations:
  - mas626_cdd_001
```

### Obligation

```yaml
obligation_id: identify_beneficial_owner
source_clause_ids:
  - mas626_cdd_001
jurisdiction: Singapore
actor: financial_institution
action: identify_and_verify
object: beneficial_owner
applies_to:
  customer_type: corporate_customer
conditions:
  - customer_type == corporate
exceptions: []
required_evidence:
  - ownership_structure_chart
  - identity_document
review_flags:
  - ubo_unclear
confidence: 0.82
review_status: pending_human_review
```

### CustomerContext

```yaml
customer_id: example_customer_001
customer_type: corporate
registration_jurisdiction: Singapore
ownership_layers: 3
ubo_status: identified
ubo_country_risk: high
pep_exposure: false
source_of_funds_available: false
source_of_wealth_available: false
```

### CDDChecklist

```yaml
checklist_id: checklist_example_customer_001
customer_id: example_customer_001
decision: enhanced_due_diligence
required_documents:
  - ownership_structure_chart
  - ubo_identity_document
  - source_of_funds
  - source_of_wealth
risk_triggers:
  - high_risk_ubo_jurisdiction
  - complex_ownership_structure
applicable_obligations:
  - identify_beneficial_owner
human_review_required: true
citations:
  - mas626_cdd_001
```

## 7. Acceptance Scenarios

### Scenario A: Corporate High-Risk UBO

Given a corporate customer registered in Singapore with three ownership layers and a high-risk UBO jurisdiction, the system SHALL output EDD, list required documents, attach source citations, and mark the case for human review.

### Scenario B: Internal Policy Conflict

Given an internal AML policy that requires high-risk customer review every 12 months and an external clause requiring review every 6 months, the system SHALL create a `Conflict` record and show the unresolved conflict in checklist output.

### Scenario C: Alias Deduplication

Given source text that uses "UBO", "beneficial owner", and "controlling party", the system SHALL map equivalent terms to a canonical concept while preserving aliases and source references.

## 8. Evaluation

The MVP SHALL be evaluated on:

- clause segmentation stability
- obligation extraction correctness against manual gold examples
- provenance completeness
- checklist correctness
- conflict visibility
- citation faithfulness
- human review routing

Each error SHOULD be classified as one of:

- source parsing error
- clause segmentation error
- obligation extraction error
- graph modeling error
- conflict handling error
- retrieval or citation error
- final checklist reasoning error

## 9. Open Questions

- Should the first implementation use JSON Schema only, or Python dataclasses plus JSON Schema export?
- Should graph export start as plain JSON adjacency records before adopting RDF, Neo4j, or another graph store?
- What exact source excerpts from FATF Recommendation 10 and MAS Notice 626 should become the first 10 gold clauses?
- Should the first demo expose a CLI, notebook, or minimal web UI after the data contracts exist?

## 10. Next Work

The next implementation step is not UI. The next step is to complete OpenSpec task group 1 and 2:

1. Confirm `SPEC.md`, OpenSpec artifacts, and ADRs as the controlling development system.
2. Create first-pass schemas and manual examples for `SourceDocument`, `Clause`, `Obligation`, `CustomerContext`, `Conflict`, and `CDDChecklist`.

