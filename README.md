# CDD-GraphWiki

CDD-GraphWiki 是一個 AML / CDD 法規知識編譯與合規推理系統。它的目標不是做一般 RAG chatbot，而是把法規與內規文件轉成：

- 人類可讀的 wiki concept pages
- 機器可推理的 regulatory knowledge graph
- 可追溯 citation 的 CDD / EDD checklist
- 可審查的 contradiction / supersession / human review log

## Start Here

1. 讀 [SPEC.md](SPEC.md)：目前的產品規格、MVP 邊界、資料物件與驗收方向。
2. 讀 [docs/system-build-roadmap.md](docs/system-build-roadmap.md)：完整系統路線圖與論文閱讀順序。
3. 讀 [openspec/changes/bootstrap-cdd-graphwiki/proposal.md](openspec/changes/bootstrap-cdd-graphwiki/proposal.md)：目前 active OpenSpec change。
4. 讀 [docs/adr/](docs/adr/)：目前已確認的架構決策。

## Current OpenSpec Change

Active change:

```bash
openspec show bootstrap-cdd-graphwiki
openspec validate bootstrap-cdd-graphwiki --strict --no-interactive
```

Change artifacts:

- `openspec/changes/bootstrap-cdd-graphwiki/proposal.md`
- `openspec/changes/bootstrap-cdd-graphwiki/design.md`
- `openspec/changes/bootstrap-cdd-graphwiki/tasks.md`
- `openspec/changes/bootstrap-cdd-graphwiki/specs/*/spec.md`

## Current Phase

The project is in specification and architecture bootstrap:

- Phase 0: Project skeleton and spec
- Phase 1: Data contracts
- Phase 2: Manual gold dataset

No application runtime, package dependencies, data ingestion pipeline, UI, or model integration has been added yet.

