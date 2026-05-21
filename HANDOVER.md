# CDD-GraphWiki Handover Summary

Generated: 2026-05-21  
Repository: `/Users/andrew-ideaslab/Documents/CDD-GraphWiki`  
Branch checked: `main`  
Latest commit observed: `05ffc92 chore: bootstrap cdd graphwiki specs and agent profile`

## 1. Current Engineering Status

CDD-GraphWiki is still in specification and architecture bootstrap. It is not yet an application repo.

Successfully bootstrapped:

- Root product spec: `SPEC.md`
- Repository entry point: `README.md`
- Project agent instructions: `AGENTS.md`
- OpenSpec project config: `openspec/config.yaml`
- Active OpenSpec change: `openspec/changes/bootstrap-cdd-graphwiki/`
- ADR infrastructure: `docs/adr/README.md`
- Accepted ADRs:
  - `docs/adr/0001-use-openspec-and-adrs-for-spec-first-development.md`
  - `docs/adr/0002-build-compliance-knowledge-compilation-before-chat-ui.md`
  - `docs/adr/0003-start-with-manual-gold-dataset-before-automation.md`
- Local ECC / Codex support files:
  - `.agents/`
  - `.codex/`

OpenSpec status:

- `openspec/config.yaml` uses `schema: spec-driven`.
- The active change is `bootstrap-cdd-graphwiki`.
- The change has all four expected artifact groups:
  - `proposal.md`
  - `design.md`
  - `specs/*/spec.md`
  - `tasks.md`
- Capability specs currently exist for:
  - `knowledge-compilation-pipeline`
  - `compliance-data-contracts`
  - `manual-gold-dataset`
  - `cdd-decisioning`
  - `governance-and-audit`
- `openspec/specs/` currently has no accepted baseline specs. The specs are still inside the active change directory.
- `openspec/changes/bootstrap-cdd-graphwiki/tasks.md` exists, but all task checkboxes are still unchecked.

Validation status as of this handover:

```bash
openspec validate bootstrap-cdd-graphwiki --strict --no-interactive
```

Result:

```text
Change 'bootstrap-cdd-graphwiki' is valid
```

Additional status command:

```bash
openspec status --change bootstrap-cdd-graphwiki
```

Result summary:

```text
Schema: spec-driven
Progress: 4/4 artifacts complete
[x] proposal
[x] design
[x] specs
[x] tasks
All artifacts complete!
```

Workspace / code status:

- No runtime application has been added.
- No package manager setup has been added.
- No dependencies have been installed.
- No source parser, graph engine, checklist engine, UI, model integration, schemas, data fixtures, or tests exist yet.
- No Python, JavaScript, TypeScript, or application code files were found.
- `git status --short` was clean before this handover file was added.
- `git status --short --ignored` only showed ignored `.DS_Store`.
- After this file is created, `HANDOVER.md` itself is the expected new uncommitted file.

Research / planning documents present:

- `docs/system-build-roadmap.md` is the older controlling roadmap and is still useful for architecture sequence and literature mapping.
- `docs/note.md` is a background explanatory note.
- The saved Medium article under `docs/` whose filename starts `The LLMWiki explained` is a source article / research note. Use `rg --files docs` rather than typing the long filename by hand.

There are no known experimental scripts, half-written implementation files, or abandoned prototypes in the workspace.

## 2. Next Immediate Steps

The very next project task should be to finish OpenSpec task group 1, then begin task group 2.

Immediate to-do list:

1. Review and confirm `SPEC.md` as the discussion-level product spec.
2. Review and confirm OpenSpec change `bootstrap-cdd-graphwiki`.
3. Review and confirm the three accepted ADRs under `docs/adr/`.
4. Decide whether future broad product spec edits live only in root `SPEC.md`, in `docs/spec.md`, or in both. Current repo uses root `SPEC.md`.
5. Start the first data contract slice:
   - `schemas/source_document.schema.json` with one example
   - `schemas/clause.schema.json` with one example
   - `schemas/obligation.schema.json` with one example
   - `schemas/customer_context.schema.json` with one example
   - `schemas/conflict.schema.json` with one example
   - `schemas/cdd_checklist.schema.json` with one example

The first coding challenge is not UI and not LLM extraction. The first challenge is to define stable, source-linked data contracts and examples that can later support parsing, graph construction, deterministic checklist generation, and testable provenance.

Recommended first implementation sequence:

1. Create `schemas/` and `data/examples/` or `data/gold/`.
2. Choose JSON Schema first unless the user approves a Python modeling dependency. This keeps the repo dependency-free.
3. Add tiny, manually authored examples for the core objects.
4. Add a minimal validation path only if it can run with existing tools, or ask before introducing dependencies.
5. Move to the manual gold dataset only after the schema shape is reviewed.

## 3. Key Technical Context And Decisions

Core product assumption:

- CDD-GraphWiki is an AML / CDD regulatory knowledge compilation and compliance reasoning system.
- It must not become a generic "upload PDFs and chat" RAG app.
- The system should compile source text into structured, source-linked compliance objects before any polished chat surface exists.

MVP source corpus:

- FATF Recommendation 10
- MAS Notice 626 CDD / EDD clauses
- One mock internal AML / KYC policy

Out of scope for the current MVP:

- FCA / HKMA expansion
- Live bank systems
- Transaction monitoring
- Production policy workflows
- Broad multi-jurisdiction ingestion
- Production legal judgment automation

Important data assumptions:

- Every derived object must preserve clause-level provenance.
- Customer input should become a structured `CustomerContext`, not an unconstrained prompt.
- Compliance outputs should include source citations, matched obligations, required evidence, risk triggers, conflicts, and human review flags.
- Legal, regulatory, threshold, conflict, required-evidence, and escalation decisions require human review until explicitly approved.
- Wiki pages are a human review / presentation layer. They are not the authoritative reasoning layer.
- The machine-readable objects and graph-ready records should remain the reasoning layer.

Accepted architecture decisions:

- ADR 0001: Use OpenSpec plus ADRs for spec-first development.
- ADR 0002: Build compliance knowledge compilation before chat UI.
- ADR 0003: Start with a manual gold dataset before automation.

Open questions still unresolved:

- JSON Schema only vs Python dataclasses plus JSON Schema export.
- JSON adjacency records vs RDF vs graph database import format for the first graph artifact.
- Exact FATF Recommendation 10 and MAS Notice 626 excerpts for the first 10 gold clauses.
- First executable surface after data contracts: CLI, notebook, or minimal web UI.

## 4. Tips For The Incoming Agent

Start here:

```bash
sed -n '1,220p' SPEC.md
sed -n '1,220p' openspec/config.yaml
sed -n '1,220p' openspec/changes/bootstrap-cdd-graphwiki/tasks.md
sed -n '1,220p' docs/adr/0001-use-openspec-and-adrs-for-spec-first-development.md
```

Useful OpenSpec commands:

```bash
openspec status --change bootstrap-cdd-graphwiki
openspec validate bootstrap-cdd-graphwiki --strict --no-interactive
openspec show bootstrap-cdd-graphwiki
```

Directory traps:

- `openspec/specs/` is empty right now. Do not assume the capability specs have been archived into accepted baseline specs.
- The active specs are under `openspec/changes/bootstrap-cdd-graphwiki/specs/`.
- The repo is docs-only by design. Do not "discover" missing runtime folders as accidental deletion.
- `.agents/` and `.codex/` are intentional local support/configuration material, not application source code.
- `.DS_Store` is ignored and should not be treated as a project artifact.

Development guardrails:

- Do not install packages, enable MCP servers, add package managers, or create runtime services without user approval.
- Prefer Python once implementation begins, unless the project later declares another stack.
- Keep the MVP source corpus small until schemas, gold data, and checklist correctness are stable.
- Do not add a chatbot UI, vector database, graph database, or extraction automation before the data contracts and manual gold examples are reviewed.
- If adding a material product requirement, update `SPEC.md` and the active OpenSpec change.
- If making an architecture choice, add or update an ADR.
- After edits, rerun:

```bash
openspec validate bootstrap-cdd-graphwiki --strict --no-interactive
git diff
```

Best first handoff action:

Open `openspec/changes/bootstrap-cdd-graphwiki/tasks.md`, complete the human confirmation items if the user approves the current planning foundation, then create the first schema and example pair for `SourceDocument` and `Clause`. That will turn the project from planning-only into the first testable data-contract slice without prematurely committing to a parser, graph store, or UI.
