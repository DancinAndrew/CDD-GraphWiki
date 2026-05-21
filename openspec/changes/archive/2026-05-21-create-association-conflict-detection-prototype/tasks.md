# Phase 5: Association & Conflict Detection Prototype Tasks

## 1. Schema Expansion
- [ ] 1.1 Expand `src/contracts/models.py` to include `Concept` class
- [ ] 1.2 Update `src/contracts/__init__.py` to export `Concept` in `__all__`
- [ ] 1.3 Compile new JSON schemas using `scripts/compile_schemas.py` and verify `Concept.schema.json`

## 2. Concept Mapper Implementation
- [ ] 2.1 Implement `ConceptLoader` to parse markdown files under `data/gold/concepts/`
- [ ] 2.2 Implement `ConceptMapper` to support alias deduplication mapping for CDD, EDD, PEP, SOFW, and UBO concepts
- [ ] 2.3 Ensure concept mapping handles exact matching, regex, and case-insensitivity

## 3. Conflict Detector Implementation
- [ ] 3.1 Implement `ConflictDetector` to parse Obligations and auto-detect UBO ownership thresholds numerical conflicts (`conf_ubo_threshold`)
- [ ] 3.2 Implement `ConflictDetector` to auto-detect PEP onboarding policy reversal/prohibition conflicts (`conf_pep_jurisdiction`)
- [ ] 3.3 Implement `ConflictDetector` to auto-detect occasional transaction thresholds numerical conflicts (`conf_occasional_threshold`)
- [ ] 3.4 Ensure detector outputs align 100% with the gold dataset conflicts in `data/gold/conflicts.yaml`

## 4. Verification and Testing
- [ ] 4.1 Write automated tests in `tests/test_association_conflict.py` covering mapper and detector
- [ ] 4.2 Run testing suite via `PYTHONPATH=. .venv/bin/pytest tests/` and verify all tests pass
- [ ] 4.3 Validate the active OpenSpec change using `openspec validate create-association-conflict-detection-prototype`
- [ ] 4.4 Archive the change using `openspec archive create-association-conflict-detection-prototype`
