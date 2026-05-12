# CDD-GraphWiki System Build and Reading Roadmap

Last updated: 2026-05-12

## One-Line Direction

CDD-GraphWiki should be built as a regulatory knowledge compilation and compliance reasoning system for AML / CDD, not as a generic RAG chatbot.

The core pipeline is:

```text
raw regulatory sources
-> clause segmentation and provenance
-> obligation / condition / exception extraction
-> human-readable wiki pages
-> machine-readable regulatory graph
-> contradiction / supersession / policy-gap tracking
-> evidence-grounded CDD / EDD checklist generation
-> human review for ambiguous or high-risk cases
```

## Product Thesis

The system's job is to convert complex regulatory and internal policy documents into a knowledge system that compliance officers can read and machines can reason over.

A weak version of this project would upload FATF / MAS / FCA / internal policy PDFs into a vector database and answer questions with an LLM. That may produce useful summaries, but it cannot reliably answer operational CDD questions such as:

- Which obligation applies to this customer type?
- Which jurisdiction or policy version controls this decision?
- Is this rule superseded by a newer or stricter rule?
- Does internal AML policy conflict with external regulation?
- Which documents are required for this exact CDD / EDD scenario?
- Which source clauses support each checklist item?

The better version separates document understanding, legal rule extraction, graph construction, conflict tracking, evidence retrieval, and decision generation.

## Target Architecture

### 1. Raw Regulatory Sources

Purpose: preserve original authority, provenance, and version history.

Inputs:

- FATF Recommendation 10
- MAS Notice 626
- FCA AML / financial crime guidance
- Internal AML / KYC policies
- Mock internal policy for MVP testing

Build requirements:

- Store source id, jurisdiction, issuer, document version, effective date, retrieval date, section id, clause id, page / paragraph reference, and raw text.
- Never allow downstream generated content to replace the original clause.
- Treat source provenance as a first-class data model, not as metadata pasted into a prompt.

### 2. Clause Segmentation and Legal Parsing

Purpose: turn long legal documents into stable units that can be cited, extracted, compared, and reviewed.

Build requirements:

- Segment documents into sections, clauses, subclauses, definitions, obligations, exceptions, and cross-references.
- Keep each segment connected to the original source location.
- Preserve hierarchy, because cross-references and exceptions often depend on parent clauses.

Main paper support:

- [RAGulating Compliance](https://arxiv.org/html/2508.09893v1): ingestion, triplet extraction, source-linked triplets, and agent-based KG construction.
- [Legal Requirements Translation from Law](https://arxiv.org/html/2507.02846v1): structural metadata such as sections, subsections, references, and rule relationships.
- [LegalBench-RAG](https://arxiv.org/abs/2408.10343): minimal, highly relevant legal snippet retrieval as an evaluation target.

### 3. Obligation Extraction Layer

Purpose: convert legal clauses into structured compliance obligations.

Canonical obligation shape:

```yaml
obligation_id: identify_beneficial_owner
source_clause_id: mas626_cdd_001
jurisdiction: Singapore
issuer: MAS
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
  - complex_ownership_structure
```

Build requirements:

- Extract actor, action, object, condition, exception, evidence, timing, frequency, threshold, and review trigger.
- Do not collapse obligation extraction into natural-language summary.
- Track extraction confidence and human review status.

Main paper support:

- [Approaching the AI Act... with AI](https://www.sciencedirect.com/science/article/pii/S2212473X25001026): modular workflow for identifying obligations, filtering deontic statements, analyzing deontic content, and building searchable KGs.
- [ComplianceNLP](https://arxiv.org/abs/2604.23585): multi-task obligation extraction and compliance gap detection against institutional policies.
- [Legal Requirements Translation from Law](https://arxiv.org/html/2507.02846v1): canonical executable representation of legal rules.

### 4. Human-Readable Wiki Layer

Purpose: give compliance officers readable concept pages without losing source grounding.

Example pages:

- Beneficial Owner / UBO
- Customer Due Diligence
- Enhanced Due Diligence
- Politically Exposed Person
- High-Risk Jurisdiction
- Source of Funds / Source of Wealth

Each page should include:

- Definition
- Aliases and equivalent terms
- Related concepts
- Applicable jurisdictions
- Source clauses
- Known ambiguities
- Linked obligations
- Review notes

Main paper support:

- [RAGulating Compliance](https://arxiv.org/html/2508.09893v1): triplet + original text retrieval for explainable regulatory QA.
- [Knowledge Graph Representations for LLM-Based Policy Compliance Reasoning](https://arxiv.org/abs/2604.27713): KG-augmented policy QA and schema choices.

### 5. Machine-Readable Regulatory Graph

Purpose: represent rules, concepts, obligations, conditions, exceptions, jurisdictions, evidence, and relationships in a typed graph.

Important node types:

- SourceDocument
- Clause
- Concept
- Obligation
- Condition
- Exception
- EvidenceRequirement
- Jurisdiction
- CustomerType
- RiskTrigger
- InternalPolicyRule
- Conflict
- ReviewCase

Important edge types:

- `defines`
- `requires`
- `applies_to`
- `conditioned_on`
- `except_when`
- `requires_evidence`
- `references_clause`
- `same_as`
- `broader_than`
- `narrower_than`
- `stricter_than`
- `supersedes`
- `conflicts_with`
- `derived_from`

Main paper support:

- [ComplianceNLP](https://arxiv.org/abs/2604.23585): regulatory KG plus KG-augmented RAG for cross-reference-heavy compliance tasks.
- [GraphCompliance](https://arxiv.org/abs/2510.26309): policy graph for normative structure and context graph for runtime facts.
- [Knowledge Graph Representations for LLM-Based Policy Compliance Reasoning](https://arxiv.org/abs/2604.27713): compares ontology-constrained and open-schema KG construction for policy QA.
- [RAGulating Compliance](https://arxiv.org/html/2508.09893v1): ontology-free triplet graph, normalization, deduplication, and evidence-linked retrieval.

### 6. Contradiction / Supersession Layer

Purpose: prevent the system from silently merging conflicting rules.

The system should record:

- Source A
- Source B
- Conflict type
- Whether the conflict is explicit or inferred
- Whether one rule supersedes another
- Whether one rule is stricter, narrower, or more recent
- Whether the issue is retrieval-verifiable or requires expert review
- Human review status and final resolution

Example conflict record:

```yaml
conflict_id: conflict_001
statement_a: "High-risk customer review every 12 months"
statement_b: "High-risk customer review every 6 months"
source_a: internal_aml_policy_v3
source_b: mas626_update_x
conflict_type: temporal_or_frequency
relationship: stricter_than
preferred_rule: mas626_update_x
status: pending_human_review
verifiability: retrieval_verifiable
```

Main paper support:

- [LegalWiz](https://arxiv.org/html/2510.03418v2): contradiction taxonomy, hybrid NLI + LLM contradiction detection, and human-in-the-loop validation.
- [ComplianceNLP](https://arxiv.org/abs/2604.23585): gap analysis between external regulations and institutional policies.
- [Legal Requirements Translation from Law](https://arxiv.org/html/2507.02846v1): explicit rule relationships, exceptions, and dependencies.

### 7. CDD Decision Layer

Purpose: generate CDD / EDD checklists from customer profiles using the regulatory graph, not free-form LLM guessing.

Customer context should become a graph or structured object:

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

Expected output:

- CDD / EDD decision
- Applicable obligations
- Required documents
- Risk triggers
- Conflicts or unresolved policy issues
- Human review flags
- Citations to source clauses

Main paper support:

- [GraphCompliance](https://arxiv.org/abs/2510.26309): align policy graph and context graph to support compliance judgment.
- [AI Application in Anti-Money Laundering for Sustainable and Transparent Financial Systems](https://arxiv.org/abs/2512.06240): KYC / CDD / EDD Graph RAG and customer relationship graph.
- [ComplianceNLP](https://arxiv.org/abs/2604.23585): evidence-grounded regulatory monitoring and policy mapping.

### 8. Evidence Retrieval and Audit Layer

Purpose: every generated answer, wiki page, obligation, conflict, and checklist item should be traceable to source clauses.

Build requirements:

- Retrieve clause-level evidence, not only document-level chunks.
- Prefer minimal supporting snippets over large vague context windows.
- Show citations beside each decision item.
- Separate "retrieved evidence" from "LLM interpretation."
- Record retrieval failures as system failures, not as harmless missing context.

Main paper support:

- [LegalBench-RAG](https://arxiv.org/abs/2408.10343): evaluates retrieval of minimal legal snippets and citation-ready evidence.
- [Legal RAG Bench](https://arxiv.org/abs/2603.01710): end-to-end legal RAG evaluation and error decomposition between retrieval and reasoning.
- [RAGulating Compliance](https://arxiv.org/html/2508.09893v1): retrieved triplets plus source text sections for traceable answers.

## Paper-to-Architecture Map

| Paper | Read when building | Main system component | What to extract |
| --- | --- | --- | --- |
| [ComplianceNLP](https://arxiv.org/abs/2604.23585) | First | Overall compliance architecture, obligation extraction, KG-augmented RAG, policy gap analysis | End-to-end shape: regulatory updates -> obligations -> KG -> internal policy mapping -> evidence-grounded gap detection |
| [GraphCompliance](https://arxiv.org/abs/2510.26309) | First | CDD Decision Layer | Policy graph vs context graph alignment; use this to model customer facts separately from regulatory rules |
| [AI Application in AML](https://arxiv.org/abs/2512.06240) | First | Customer risk graph and KYC / CDD / EDD workflow | How Graph RAG can support due diligence reporting from customer, account, transaction, sanctions, and PEP relationships |
| [Approaching the AI Act... with AI](https://www.sciencedirect.com/science/article/pii/S2212473X25001026) | Second | Obligation Extraction Layer | Deontic filtering, obligation type, addressee, predicate, and searchable KG construction |
| [Legal Requirements Translation from Law](https://arxiv.org/html/2507.02846v1) | Second | Machine-readable rule representation | Legal text -> canonical Python-like rule model with sections, references, conditions, exceptions, and obligations |
| [RAGulating Compliance](https://arxiv.org/html/2508.09893v1) | Second | Ingestion, concept dedupe, GraphRAG QA | Agent pipeline for document ingestion, SPO triplets, normalization, deduplication, retrieval, and answer generation |
| [Knowledge Graph Representations for Policy Compliance Reasoning](https://arxiv.org/abs/2604.27713) | Second | KG schema design and retrieval strategy | Compare formal ontology vs open LLM-discovered schema; task taxonomy from lookup to cross-policy reasoning |
| [LegalWiz](https://arxiv.org/html/2510.03418v2) | Third | Contradiction / Supersession Layer | Conflict taxonomy, hybrid scoring, retrieval-verifiable vs retrieval-resistant conflicts, human validation |
| [LegalBench-RAG](https://arxiv.org/abs/2408.10343) | Third | Evidence retrieval evaluation | Minimal relevant legal snippet retrieval and citation readiness |
| [Legal RAG Bench](https://arxiv.org/abs/2603.01710) | Third | End-to-end evaluation | Separate retrieval failure from reasoning failure; design final benchmark loops |

## Recommended Reading Order

### Round 1: Understand the Whole System Shape

1. [ComplianceNLP](https://arxiv.org/abs/2604.23585)

   You are reading this for the overall system skeleton. This corresponds to the path from regulatory sources to obligation extraction, regulatory KG, internal policy mapping, gap analysis, and grounded answer generation.

   Build after reading:

   - Draft the first `Obligation` schema.
   - Draft the first `InternalPolicyRule` schema.
   - Define how an external rule maps to an internal policy clause.

2. [GraphCompliance](https://arxiv.org/abs/2510.26309)

   You are reading this for the CDD Decision Layer. This corresponds to separating regulatory rules as a policy graph and customer facts as a context graph.

   Build after reading:

   - Draft a `CustomerContext` schema.
   - Define the first graph alignment question: "Does this customer profile trigger EDD?"
   - Write 5 sample customer profiles that should produce different CDD / EDD outcomes.

3. [AI Application in AML](https://arxiv.org/abs/2512.06240)

   You are reading this for AML / KYC domain grounding. This corresponds to the customer risk graph, due diligence report generation, audit trails, and human review expectations.

   Build after reading:

   - Draft the customer risk graph node and edge types.
   - Define which customer facts belong to regulatory reasoning and which belong to financial crime risk analysis.
   - Keep this as domain reference, not as the regulatory obligation graph itself.

### Round 2: Learn How to Compile Law into Data

4. [Approaching the AI Act... with AI](https://www.sciencedirect.com/science/article/pii/S2212473X25001026)

   You are reading this for obligation extraction. This corresponds to turning clauses into addressee, predicate, obligation type, and KG entries.

   Build after reading:

   - Create extraction prompts or rules for actor / action / object / condition / exception.
   - Create a small manually reviewed obligation dataset from FATF Recommendation 10 or MAS 626.

5. [Legal Requirements Translation from Law](https://arxiv.org/html/2507.02846v1)

   You are reading this for machine-readable representation. This corresponds to the internal canonical format that sits between source text and the regulatory graph.

   Build after reading:

   - Convert 5 obligations into a typed Python / YAML representation.
   - Explicitly model section hierarchy, cross-reference, condition, exception, and evidence requirement.

6. [RAGulating Compliance](https://arxiv.org/html/2508.09893v1)

   You are reading this for ingestion, triplet extraction, normalization, concept deduplication, and evidence-grounded QA.

   Build after reading:

   - Create the first concept alias map: UBO / Beneficial Owner / Controlling Party.
   - Create a source-linked triplet format.
   - Decide which triplets are useful for wiki generation and which are too weak for compliance decisions.

7. [Knowledge Graph Representations for Policy Compliance Reasoning](https://arxiv.org/abs/2604.27713)

   You are reading this for KG schema strategy. This corresponds to deciding whether CDD-GraphWiki should start with a strict ontology, an open schema, or a hybrid.

   Build after reading:

   - Define the MVP graph ontology.
   - Mark which relation types are strict and which can remain exploratory.
   - Create 5 graph QA tasks: definition lookup, relation enumeration, attribute retrieval, multi-hop reasoning, compliance check.

### Round 3: Make the System Trustworthy

8. [LegalWiz](https://arxiv.org/html/2510.03418v2)

   You are reading this for contradiction and review design. This corresponds to the conflict log, supersession layer, and human review queue.

   Build after reading:

   - Create a `Conflict` schema.
   - Define conflict types for AML / CDD: temporal, threshold, jurisdiction, authority, procedure, specificity, policy reversal.
   - Build mock examples such as 12-month vs 6-month high-risk review frequency.

9. [LegalBench-RAG](https://arxiv.org/abs/2408.10343)

   You are reading this for retrieval evaluation. This corresponds to proving that the system can retrieve exact supporting clauses, not just approximate chunks.

   Build after reading:

   - Create 20 query -> supporting clause test cases.
   - Score whether retrieval returns the minimal correct clause.
   - Track citation precision and recall.

10. [Legal RAG Bench](https://arxiv.org/abs/2603.01710)

   You are reading this for end-to-end evaluation. This corresponds to separating failures caused by retrieval from failures caused by reasoning.

   Build after reading:

   - Define the final benchmark categories: retrieval correctness, obligation extraction accuracy, graph consistency, conflict detection precision, checklist correctness, citation faithfulness.
   - Add an error taxonomy so each failed CDD answer has a clear cause.

## MVP Build Path

### Phase 0: Project Skeleton and Specs

Goal: make the project explainable before adding infrastructure.

Deliverables:

- `docs/system-build-roadmap.md`
- `docs/note.md`
- `docs/spec.md` or equivalent product specification
- MVP scope: FATF Recommendation 10, MAS Notice 626 CDD / EDD clauses, one mock internal AML policy

Done when:

- The project has a clear anti-RAG-chatbot thesis.
- The first architecture diagram and module boundaries are written.
- Every paper has a known role in the architecture.

### Phase 1: Data Contracts

Goal: define the shapes before building extraction logic.

Deliverables:

- `SourceDocument`
- `Clause`
- `Concept`
- `Obligation`
- `EvidenceRequirement`
- `CustomerContext`
- `Conflict`
- `CDDChecklist`

Done when:

- Each object has a JSON or YAML example.
- Each object has fields for provenance and review status.
- The first sample CDD checklist can be written manually from structured objects.

### Phase 2: Manual Gold Dataset

Goal: build a tiny trusted dataset before asking an LLM to automate extraction.

Deliverables:

- 10 manually segmented clauses.
- 10 manually extracted obligations.
- 5 concept pages.
- 5 customer profiles.
- 5 expected CDD / EDD checklist outputs.
- 3 conflict examples.

Done when:

- A human can inspect every source-to-output link.
- The examples cover individual customer, corporate customer, PEP, high-risk jurisdiction, complex ownership, and unclear UBO.

### Phase 3: Ingestion and Clause Segmentation

Goal: preserve source text and make every downstream object citeable.

Deliverables:

- Parser for source files.
- Clause segmentation output.
- Source metadata and version metadata.
- Clause ids that remain stable across reruns.

Done when:

- Each clause points back to source document, section, page or paragraph, and raw text.
- A generated wiki page or obligation never loses its source clause id.

### Phase 4: Obligation Extraction Prototype

Goal: turn clauses into structured obligations.

Deliverables:

- Extraction prompt or rule pipeline.
- Obligation schema validation.
- Human review queue for low-confidence extractions.
- Comparison against the manual gold dataset.

Done when:

- Extracted obligations contain actor, action, object, condition, exception, required evidence, and source clause.
- Failed extraction cases are categorized.

### Phase 5: Wiki and Concept Deduplication

Goal: produce human-readable concept pages connected to structured rules.

Deliverables:

- Concept page generator.
- Alias map.
- Related concept links.
- Source-backed ambiguity notes.

Done when:

- A concept page such as Beneficial Owner shows aliases, definitions, obligations, related concepts, source clauses, and ambiguity notes.
- Synonyms do not create duplicate concepts without review.

### Phase 6: Regulatory Graph

Goal: build the first machine-reasonable graph.

Deliverables:

- Graph schema.
- Nodes and edges for clauses, concepts, obligations, evidence, risk triggers, and jurisdictions.
- Graph export format such as JSON, RDF, or a graph database import file.

Done when:

- A query can find all obligations triggered by `corporate_customer + high_risk_jurisdiction + complex_ownership_structure`.
- Each graph answer can return source clauses.

### Phase 7: Contradiction and Supersession Log

Goal: stop the system from hiding conflicts.

Deliverables:

- Conflict schema.
- Supersession / stricter-than / narrower-than relationships.
- Human review status.
- Mock internal policy conflicts.

Done when:

- The system can record that one internal policy rule conflicts with or is weaker than an external regulatory rule.
- The CDD checklist can show unresolved conflicts instead of choosing silently.

### Phase 8: CDD Decision Engine

Goal: generate evidence-grounded CDD / EDD outputs from customer profiles.

Deliverables:

- Customer profile schema.
- Rule matching logic.
- Checklist generator.
- Human review flags.
- Citation attachment.

Done when:

- Given a corporate customer with complex ownership and a high-risk UBO jurisdiction, the system outputs EDD, required documents, applicable obligations, risk triggers, conflicts, and citations.

### Phase 9: Evaluation Harness

Goal: prove the system is better than a generic RAG demo.

Deliverables:

- Retrieval tests.
- Obligation extraction tests.
- Conflict detection tests.
- Checklist correctness tests.
- Citation faithfulness checks.

Done when:

- Each failed answer can be traced to retrieval, extraction, graph modeling, conflict handling, or final reasoning.
- The baseline comparison includes a simple vector-RAG chatbot, so the architecture difference is measurable.

## Suggested MVP Repository Shape

```text
CDD-GraphWiki/
  docs/
    note.md
    system-build-roadmap.md
    spec.md
  data/
    sources/
    processed/
    gold/
  knowledge/
    wiki/
    graph/
    conflicts/
  schemas/
    source_document.schema.json
    clause.schema.json
    obligation.schema.json
    customer_context.schema.json
    conflict.schema.json
    cdd_checklist.schema.json
  src/
    ingestion/
    extraction/
    graph/
    decision/
    evaluation/
  tests/
```

## What Not to Build First

Do not start with:

- A polished chatbot UI.
- A vector database as the core architecture.
- A broad multi-jurisdiction regulatory corpus.
- Live financial institution integrations.
- Fully automated legal judgment.

Start with:

- Small source set.
- Stable clause ids.
- Manual gold examples.
- Structured obligations.
- A tiny graph.
- Evidence-backed checklists.
- Explicit conflict handling.

## Best Portfolio Framing

Strong title:

> CDD-GraphWiki: A Human-Readable and Machine-Reasonable Knowledge Compilation System for AML Compliance

Research-style framing:

> Regulatory Knowledge Compilation for Customer Due Diligence: A Graph-Augmented LLM System for AML Compliance Reasoning

The contribution is not "a chatbot for compliance." The contribution is a layered architecture that compiles regulatory text into human-readable wiki pages and machine-readable compliance objects, then uses graph reasoning and evidence retrieval to generate auditable CDD / EDD decisions.
