# Phase 6: CDD Checklist Reasoning Engine Tasks

## 1. CDD Checklist Engine Implementation
- [x] 1.1 Create decision engine codebase under `src/decision/engine.py`
- [x] 1.2 Implement `CDDChecklistEngine` to load CustomerContext, Obligations, and Conflicts
- [x] 1.3 Implement reasoning branches for low risk individual, corporate standard, individual PEP, high risk PEP, and unclear UBO corporate scenarios
- [x] 1.4 Implement risk triggers and action control flags auto-identification (e.g. `internal_ubo_threshold_triggered_10_percent`, `pep_from_high_risk_jurisdiction`, `onboarding_prohibited_by_policy`, `unclear_ubo_status`, `excessive_layering_5`, `missing_source_of_funds_evidence`)
- [x] 1.5 Map required evidence documents and extract human readable citations ensuring clause-level provenance

## 2. Checklist Evaluator Implementation
- [x] 2.1 Implement `ChecklistEvaluator` under `src/decision/engine.py` to compare generated checklists with gold checklists in `data/gold/checklists.yaml`
- [x] 2.2 Calculate precision, recall, and F1-score evaluation metrics on fields: `decision`, `required_documents`, `risk_triggers`, `applicable_obligations`, `human_review_required`, and `citations`
- [x] 2.3 Ensure perfect alignment F1-score of 1.00 on the 5 benchmark customer scenarios

## 3. Verification and Testing
- [x] 3.1 Write comprehensive unit tests in `tests/test_cdd_reasoning.py` covering all 5 customer scenarios and evaluation metrics
- [x] 3.2 Execute testing suite via `.venv/bin/python -m pytest tests/` and verify all 30+ tests pass (F1-score = 1.00)
- [x] 3.3 Validate the active OpenSpec change using `openspec validate create-cdd-checklist-reasoning-engine`
- [x] 3.4 Archive the change using `openspec archive create-cdd-checklist-reasoning-engine`

