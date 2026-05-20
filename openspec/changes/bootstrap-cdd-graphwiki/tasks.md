## 1. Bootstrap Planning System

- [ ] 1.1 Review and confirm `SPEC.md` as the discussion-level product spec.
- [ ] 1.2 Review and confirm OpenSpec change `bootstrap-cdd-graphwiki`.
- [ ] 1.3 Review and confirm the initial ADRs under `docs/adr/`.
- [ ] 1.4 Decide whether future product spec edits live in root `SPEC.md`, `docs/spec.md`, or both.

## 2. Data Contracts

- [ ] 2.1 Create `schemas/source_document.schema.json` with one example.
- [ ] 2.2 Create `schemas/clause.schema.json` with one example.
- [ ] 2.3 Create `schemas/obligation.schema.json` with one example.
- [ ] 2.4 Create `schemas/customer_context.schema.json` with one example.
- [ ] 2.5 Create `schemas/conflict.schema.json` with one example.
- [ ] 2.6 Create `schemas/cdd_checklist.schema.json` with one example.

## 3. Manual Gold Dataset

- [ ] 3.1 Create `data/gold/clauses.yaml` with 10 manually segmented clauses.
- [ ] 3.2 Create `data/gold/obligations.yaml` with 10 manually extracted obligations.
- [ ] 3.3 Create `knowledge/wiki/` with 5 initial concept pages.
- [ ] 3.4 Create `data/gold/customer_profiles.yaml` with 5 structured customer profiles.
- [ ] 3.5 Create `data/gold/expected_checklists.yaml` with 5 expected outputs.
- [ ] 3.6 Create `knowledge/conflicts/` with 3 mock conflict examples.

## 4. First Deterministic Prototype

- [ ] 4.1 Add a deterministic checklist generator that reads gold objects.
- [ ] 4.2 Add validation for required provenance and review status fields.
- [ ] 4.3 Add tests for the corporate high-risk UBO EDD scenario.
- [ ] 4.4 Add tests for internal policy conflict visibility.
- [ ] 4.5 Add tests for UBO / beneficial owner / controlling party alias handling.

## 5. Verification and Documentation

- [ ] 5.1 Run `openspec validate bootstrap-cdd-graphwiki --strict --no-interactive`.
- [ ] 5.2 Document any OpenSpec validation limitations or follow-up fixes.
- [ ] 5.3 Update `README.md` with the next exact command or file to open.
- [ ] 5.4 Review `git diff` before implementation begins.

