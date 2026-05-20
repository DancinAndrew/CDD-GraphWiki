# ADR 0003: Start With Manual Gold Dataset Before Automation

Status: Accepted  
Date: 2026-05-15

## Context

CDD-GraphWiki will eventually need extraction, concept deduplication, graph construction, contradiction detection, and evidence retrieval. Those components are difficult to evaluate without trusted examples. Starting with automation alone risks producing plausible but unverified outputs.

## Decision

Create a small manual gold dataset before automated extraction. The first dataset should include 10 clauses, 10 obligations, 5 concept pages, 5 customer profiles, 5 expected checklist outputs, and 3 conflict examples.

## Alternatives Considered

- Automate extraction immediately: faster, but hard to tell whether errors come from parsing, extraction, graph modeling, retrieval, or final reasoning.
- Use a large public legal dataset first: useful for later benchmarking, but less aligned with the AML / CDD MVP.
- Handwrite only a demo checklist: too narrow and does not test source provenance or reusable data contracts.

## Consequences

- Early progress will emphasize correctness and traceability over scale.
- Every later automated component gets a concrete evaluation target.
- The project can explain failures by comparing outputs to the manual gold dataset.

