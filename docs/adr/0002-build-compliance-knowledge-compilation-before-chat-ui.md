# ADR 0002: Build Compliance Knowledge Compilation Before Chat UI

Status: Accepted  
Date: 2026-05-15

## Context

The core project risk is mistaking CDD-GraphWiki for a generic RAG chatbot. A chatbot-first implementation could answer simple questions about documents, but it would not reliably handle clause provenance, obligation conditions, jurisdiction or policy conflicts, CDD / EDD decisioning, or human review.

## Decision

Build the knowledge compilation pipeline before any polished chat UI. The first implementation should focus on source records, stable clauses, structured obligations, concept pages, conflict records, customer context, and evidence-backed checklist output.

## Alternatives Considered

- Chat UI first: creates a fast demo, but hides whether the compliance reasoning layer actually works.
- Vector database first: useful later for retrieval, but not enough for structured obligation matching or conflict handling.
- Pure wiki first: useful for human reading, but insufficient for machine-readable CDD / EDD decisions.

## Consequences

- The first visible milestone may look less flashy than a chatbot, but it will test the real product thesis.
- UI work should wait until the data contracts and gold dataset can produce a deterministic checklist.
- The system remains easier to evaluate because outputs can be compared against source-linked gold examples.

