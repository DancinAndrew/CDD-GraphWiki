## Context

The repository currently contains research and roadmap documents for CDD-GraphWiki. It does not yet contain runtime code, schemas, datasets, tests, or application infrastructure.

The roadmap already establishes the core architecture: raw regulatory sources, clause segmentation, obligation extraction, human-readable wiki pages, machine-readable regulatory graph, contradiction / supersession tracking, CDD decisioning, and evidence retrieval.

## Goals / Non-Goals

**Goals:**

- Make OpenSpec the controlling workflow for requirements, acceptance criteria, design, and task tracking.
- Make ADRs the controlling workflow for architectural rationale.
- Convert the current roadmap into a buildable MVP sequence.
- Keep the first implementation anchored on small, reviewable, source-linked data objects.
- Preserve an explicit distinction between human-readable wiki pages and machine-readable compliance reasoning.

**Non-Goals:**

- Build a chatbot UI.
- Add package dependencies or runtime services.
- Connect to live financial institution systems.
- Automate legal judgment without human review.
- Ingest a broad multi-jurisdiction corpus before the small gold dataset exists.

## Decisions

### Decision 1: Use OpenSpec plus ADRs

OpenSpec will track requirements, specs, design, and tasks. ADRs will track why architecture decisions were made and what alternatives were rejected.

Alternatives considered:

- Roadmap-only development: easier to start, but weak for acceptance criteria and implementation tracking.
- ADR-only development: good for decisions, but weak for scenario-level requirements.
- Issue tracker only: useful later, but too operational before the product shape is stable.

### Decision 2: Start With Data Contracts and Manual Gold Dataset

The project will define compliance data contracts and manual gold examples before building extraction or decisioning automation.

Alternatives considered:

- Build extraction first: faster demo, but likely unstable and hard to evaluate.
- Build UI first: attractive for portfolio screenshots, but would hide the actual compliance reasoning problem.
- Start with a graph database first: powerful, but premature before the object model is validated.

### Decision 3: Treat Wiki as Human-Readable Layer, Not the Whole System

Wiki pages will help humans review concepts, definitions, aliases, ambiguities, and linked obligations. Machine-readable objects will remain the authoritative reasoning layer.

Alternatives considered:

- Markdown-only wiki: simple, but cannot reliably support CDD / EDD decisions.
- Pure knowledge graph: machine-friendly, but less useful for human review and compliance explanation.

### Decision 4: Keep MVP Corpus Small

The MVP will use FATF Recommendation 10, MAS Notice 626 CDD / EDD clauses, and one mock internal AML / KYC policy.

Alternatives considered:

- Add FCA, HKMA, and more internal policies immediately: more realistic, but likely to expand scope before the pipeline is reliable.
- Use only one regulation: simpler, but weak for conflict and policy gap examples.

## Risks / Trade-offs

- Scope creep into chatbot UI -> Keep OpenSpec tasks focused on data contracts, gold examples, and checklist correctness.
- Over-modeling before implementation -> Start with JSON / YAML examples, then promote stable objects into code.
- Legal interpretation risk -> Treat all material compliance decisions as pending human review.
- Citation drift -> Preserve stable clause identifiers and source metadata from the first dataset.
- Graph storage premature choice -> Start with graph-ready records; decide storage format in a later ADR.

## Migration Plan

1. Accept this bootstrap change as the working foundation.
2. Create first-pass schemas and examples under future `schemas/` and `data/gold/`.
3. Implement deterministic validation and checklist generation against the gold dataset.
4. Add extraction and graph construction only after the manual dataset can verify correctness.

Rollback is simple at this stage: remove the planning artifacts or supersede them with a new OpenSpec change before implementation begins.

## Open Questions

- Should schemas start as JSON Schema, Python dataclasses, Pydantic models, or a combination?
- Should the first graph artifact be JSON adjacency records, RDF, or a graph database import format?
- Which exact source excerpts become the first 10 gold clauses?
- Should the first executable surface be CLI, notebook, or minimal web UI?

