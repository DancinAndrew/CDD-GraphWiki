# CDD-GraphWiki

CDD-GraphWiki is an AI-assisted risk workflow and graph-based knowledge organization project developed for a Technology Risk Management course.

It explores how compliance documents, risk obligations, customer/entity information, review decisions, and audit evidence can be organized into a traceable workflow instead of a generic "upload PDF and chat" application.

## 30-Second Summary

- **What it is:** a proof-of-concept compliance workflow system for AML / CDD due diligence scenarios.
- **What it demonstrates:** structured compliance knowledge extraction, graph-based relationship mapping, CDD / EDD checklist generation, human review routing, and tamper-evident audit logs.
- **Why it matters:** risk and compliance work depends on fragmented documents, requirements, entities, evidence, approvals, and historical decisions. This project shows one way AI and knowledge graphs can support that workflow while keeping human judgment and provenance visible.
- **Current status:** course final project / working prototype, not a production legal or compliance decision system.

## Problem

Risk and compliance review often requires searching across fragmented documents, policies, entity records, obligations, and historical review decisions. This creates several practical problems:

- information is scattered across documents and systems
- relationships between entities, documents, risks, obligations, and evidence are hard to track
- manual lookup slows down compliance review and due diligence workflows
- teams need explainable, traceable retrieval instead of opaque model answers
- high-risk decisions still need human review, escalation, and auditability

## Solution

CDD-GraphWiki organizes compliance knowledge into structured objects and graph relationships, then uses that structure to support risk review workflows.

The prototype pipeline is:

1. Ingest regulatory or policy sources.
2. Segment sources into stable clause records.
3. Extract compliance obligations and evidence requirements.
4. Build a regulatory knowledge graph linking documents, clauses, obligations, customers, conflicts, and checklists.
5. Generate CDD / EDD checklist outputs from structured customer context.
6. Route high-risk cases to human-in-the-loop review.
7. Record reasoning, routing, and reviewer decisions in a tamper-evident SHA-256 audit chain.

The goal is not to replace compliance judgment. The goal is to make information retrieval, relationship mapping, review routing, and audit evidence easier to inspect.

## Relevance to Compliance / Risk Management

The demo domain is AML / CDD, but the design pattern is relevant to broader risk and compliance workflows, including product compliance contexts.

Product compliance teams often need to manage:

- regulatory requirements and standards
- product requirements and test evidence
- certification or approval records
- risk findings and mitigation decisions
- document-to-product relationships
- cross-functional review history

CDD-GraphWiki demonstrates transferable workflow ideas for these settings:

- document and requirement retrieval
- risk evidence organization
- entity / document / obligation relationship mapping
- traceable AI-assisted review support
- human approval boundaries for high-risk decisions
- audit logs for later review

## Key Features

- **Structured compliance data contracts:** JSON Schema and Pydantic models for source documents, clauses, obligations, customer contexts, conflicts, checklists, graph nodes, and audit logs.
- **CDD / EDD decisioning:** rule-based checklist generation from structured customer context, including required documents, risk triggers, citations, conflicts, and human review flags.
- **Human-in-the-loop review:** review queue for high-risk or ambiguous cases, with reviewer decisions and notes captured through FastAPI validation.
- **Tamper-evident audit trail:** SHA-256 hash-chain logging for reasoning, case routing, and reviewer overrides.
- **Regulatory graph visualization:** D3-based interactive graph linking source documents, clauses, obligations, conflicts, customers, and generated checklists.
- **Neo4j graph support:** optional graph database synchronization and Cypher-based UBO ownership traversal / loop detection.
- **PDF ingestion workflow:** PDF upload, text extraction, LLM-assisted clause chunking, structured obligation extraction, YAML merge, cache refresh, and graph/checklist update.
- **Evaluation and governance artifacts:** gold datasets, evaluation harness, OpenSpec requirements, ADRs, and system roadmap documents.

## Demo And Visual Assets

The live demo is available after running the app locally:

- Frontend dashboard: `http://localhost:3000`
- Backend API docs: `http://localhost:8000/docs`
- Neo4j Browser: `http://localhost:7474`

Existing visual assets:

![Phase 1-10 Architecture](docs/assets/phase_1_10_architecture.png)

- Architecture diagram: [`docs/assets/phase_1_10_architecture.png`](docs/assets/phase_1_10_architecture.png)
- Future development direction preview: [`docs/assets/future_development_direction_preview.png`](docs/assets/future_development_direction_preview.png)
- Demo narration for slides/pages 15-21: [`docs/presentation_script_pages_15_21.md`](docs/presentation_script_pages_15_21.md)

The project slides include the fuller dashboard walkthrough, including the dashboard, review queue, audit timeline, graph view, ingestion console, and user guide.

## Screenshots

These are screenshots of the working demo. Each page handles one step of the compliance review workflow.

### 1. Compliance Dashboard

![Compliance dashboard](images/01-dashboard.png)

The home page. It shows a quick summary at the top (how many customers, how many cases need a person to look at them, how many are done). You pick a customer from the list on the left, and the system automatically generates a checklist of what documents and checks are required for that customer — including which official rule each item comes from.

### 2. Human Review Queue

![Human review queue](images/02-review-queue.png)

When a case is risky or unclear, the system does not decide on its own — it sends the case here for a real person to review. The reviewer reads the case, picks a decision (approve, ask for deeper checks, or reject), writes a note explaining why, and submits. This keeps a human in control of the important calls.

### 3. Audit Trail

![Tamper-evident audit trail](images/03-audit-trail.png)

A complete history log of everything that happened — every decision and every review, in order. Each entry is locked together using a digital "fingerprint" (hash) chain, so if anyone tried to secretly change an old record, it would be obvious. This is the proof you can show later that the process was followed correctly.

### 4. Knowledge Graph View

![Regulatory knowledge graph](images/04-graph-view.png)

An interactive map showing how everything connects — rules, documents, customers, requirements, and the generated checklists are drawn as dots, with lines showing how they relate. Instead of digging through separate files, you can see the whole picture and trace where any requirement came from.

### 5. Regulation Ingestion Console

![PDF ingestion console](images/05-ingestion.png)

Where new regulations get added to the system. You upload an official rule document (a PDF), and the system reads it, breaks it into clauses, and pulls out the obligations automatically. The panel on the right shows live progress as it processes the file.

## System Architecture

```text
Source PDFs / Markdown / Policies
        |
        v
PDF parser and source document records
        |
        v
Clause segmentation and structured obligation extraction
        |
        v
YAML gold / processed datasets + JSON Schema / Pydantic contracts
        |
        v
Regulatory graph: documents, clauses, obligations, conflicts, customers, checklists
        |
        v
CDD / EDD checklist generation
        |
        v
Human review queue + tamper-evident audit log
        |
        v
React dashboard, D3 graph view, FastAPI endpoints, optional Neo4j queries
```

Important design boundary: the system treats customer input as structured `CustomerContext`, not as an unconstrained prompt. High-risk decisions are routed to human review.

## Tech Stack

- **Frontend:** React 18, TypeScript, Vite, D3, lucide-react
- **Backend:** Python, FastAPI, Pydantic, PyYAML, jsonschema
- **Ingestion:** pypdf, PDF text extraction, structured clause and obligation extraction
- **Graph:** in-memory regulatory graph builder, D3 visualization, optional Neo4j Community Edition
- **AI / LLM:** NVIDIA NIM support, Gemini fallback, mock fallback for tests and demos
- **Data:** YAML gold datasets, processed datasets, JSON Schema contracts
- **Testing:** pytest backend tests, evaluation harness, sample schema examples
- **Deployment:** Docker, Docker Compose
- **Governance:** OpenSpec specs/changes and ADR decision records

## Project Materials

- Paper / written report: [Google Docs](https://docs.google.com/document/d/18sSEPHwYYoJUjvCJkYucqSJ-gF9ndiVysm-VFIubL8g/edit?tab=t.0)
- Presentation slides: [Google Slides](https://docs.google.com/presentation/d/1fYlCTjPTBb8Kf8QJfHVWZ1CbFYJCz8LnEv-pMoTzKeQ/edit?slide=id.g3ec91351360_1_53#slide=id.g3ec91351360_1_53)
- Product/spec thesis: [`docs/SPEC.md`](docs/SPEC.md)
- System roadmap: [`docs/system-build-roadmap.md`](docs/system-build-roadmap.md)
- Architecture decisions: [`docs/adr/`](docs/adr/)
- OpenSpec contracts: [`openspec/`](openspec/)

## How To Run

### Option A: Run With Docker Compose

```bash
git clone https://github.com/DancinAndrew/CDD-GraphWiki.git
cd CDD-GraphWiki
cp .env.example .env
docker compose -f deployment/docker-compose.yml up --build
```

Then open:

- Frontend: `http://localhost:3000`
- Backend API docs: `http://localhost:8000/docs`
- Neo4j Browser: `http://localhost:7474`
  - username: `neo4j`
  - password: `testpassword123`

The default `.env.example` contains placeholder AI keys. Core demo data and many workflows can still be inspected without real model keys; real PDF ingestion with LLM extraction requires a configured provider key.

### Option B: Run Backend And Frontend Separately

Backend:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
PYTHONPATH=backend uvicorn src.api.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 3000
```

Neo4j is optional for the basic demo. If Neo4j is unavailable, the API falls back to in-memory behavior for several graph workflows.

## Repository Guide

- [`backend/`](backend/) - FastAPI service, data contracts, decision engine, audit manager, graph builder, ingestion, evaluation, and tests
- [`frontend/`](frontend/) - React dashboard with compliance overview, review queue, audit timeline, regulatory graph, ingestion console, and user guide
- [`data/gold/`](data/gold/) - manual gold dataset for source documents, clauses, obligations, customers, checklists, and conflicts
- [`data/processed/`](data/processed/) - generated or merged runtime data, including processed source documents and audit logs
- [`schemas/`](schemas/) - JSON Schema contracts and examples
- [`docs/`](docs/) - product spec, roadmap, ADRs, paper notes, presentation support, and visual assets
- [`openspec/`](openspec/) - requirement specs and archived implementation changes
- [`deployment/`](deployment/) - Docker and Docker Compose configuration

## Example Workflow

1. Open the dashboard and inspect available customer contexts.
2. Select a customer to view generated CDD / EDD checklist output.
3. Inspect required documents, risk triggers, applicable obligations, and citations.
4. Open the review queue for cases requiring human approval.
5. Submit a reviewer decision and notes.
6. Verify that the audit timeline records the reasoning and review event.
7. Open the graph view to inspect relationships among documents, clauses, obligations, customers, conflicts, and checklists.
8. Optionally upload a regulatory PDF through the ingestion console and monitor extraction progress.

## Current Limitations

- This is a prototype for a course project, not production legal advice or a deployed compliance platform.
- The primary demo corpus is AML / CDD oriented, not a product compliance corpus.
- The CDD decision layer is intentionally constrained and rule-driven for explainability.
- LLM extraction depends on configured provider keys for real PDF ingestion.
- More rigorous retrieval evaluation, human annotation, access control, and production governance would be needed before real compliance use.

## Future Improvements

- Extend the corpus from AML / CDD examples to product compliance standards, product requirement documents, certification evidence, and test reports.
- Add evidence-grade retrieval with hybrid BM25, dense retrieval, GraphRAG, and character-span citation support.
- Expand graph reasoning for product-to-requirement, requirement-to-test, and risk-to-evidence traceability.
- Strengthen conflict and gap adjudication with NLI, LLM-assisted contradiction detection, and explicit human resolution workflows.
- Add role-based access control, reviewer permissions, and production deployment hardening.
- Build a richer screenshot/demo asset folder for quick recruiter and hiring-manager review.

## Disclaimer

CDD-GraphWiki is a learning and prototype project. It is intended to demonstrate AI-assisted compliance workflow design, graph-based knowledge organization, and auditability patterns. It should not be used as legal, regulatory, financial, or production compliance advice.
