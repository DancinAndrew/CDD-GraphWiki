# Phase 7: Explainable Reasoner and Provenance Engine Tasks

## 1. Schema and Contract Setup
- [x] 1.1 Expand `src/contracts/models.py` to include `ProvenanceNode` class
- [x] 1.2 Expand `src/contracts/models.py` to include `ExplanationPath` class
- [x] 1.3 Update `src/contracts/__init__.py` to export both new classes in `__all__`
- [x] 1.4 Compile new JSON schemas using `scripts/compile_schemas.py` and verify `ProvenanceNode.schema.json` and `ExplanationPath.schema.json`

## 2. Provenance Engine Implementation
- [x] 2.1 Create provenance engine codebase under `src/decision/provenance.py`
- [x] 2.2 Implement `ProvenanceEngine.explain_item` to trace CDDChecklist required documents and risk triggers back to CustomerContext fields
- [x] 2.3 Implement obligation resolution to link checklist requirements to corresponding compliance obligations
- [x] 2.4 Implement legal snippet extraction to attach exact clause texts and source document metadata without hallucination

## 3. Audit Trail Report Generation
- [x] 3.1 Implement `ProvenanceEngine.generate_audit_report` to format explanation paths into a human-readable Markdown audit document
- [x] 3.2 Add directed visual flows and clear citation quote blocks to the Markdown report formatting

## 4. Verification and Testing
- [x] 4.1 Write comprehensive unit tests in `tests/test_explainable_provenance.py covering model validation, exact path tracing for PEP/Corporate scenarios, and markdown report format
- [x] 4.2 Run testing suite via `.venv/bin/python -m pytest tests/` and verify all 35+ tests pass (provenance accuracy = 100%)
- [x] 4.3 Validate the active OpenSpec change using `openspec validate create-explainable-provenance-engine`
- [x] 4.4 Archive the change using `openspec archive create-explainable-provenance-engine`
