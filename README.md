# CDD-GraphWiki

CDD-GraphWiki 是一個 AML / CDD 法規知識編譯與合規推理系統。它的目標不是做一般 RAG chatbot，而是把法規與內規文件轉成：

- 人類可讀的 wiki concept pages
- 機器可推理的 regulatory knowledge graph
- 可追溯 citation 的 CDD / EDD checklist
- 可審查的 contradiction / supersession / human review log

## Start Here

1. 讀 [docs/SPEC.md](docs/SPEC.md)：目前的產品規格、MVP 邊界、資料物件與驗收方向。
2. 讀 [docs/system-build-roadmap.md](docs/system-build-roadmap.md)：完整系統路線圖與論文閱讀順序。
3. 讀 [openspec/changes/restructure-project-directories/proposal.md](openspec/changes/restructure-project-directories/proposal.md)：重構專案資料夾結構之變更提案。
4. 讀 [docs/adr/](docs/adr/)：目前已確認的架構決策。

## Project Directories Layout

本專案採用對稱的前後端分離工程結構：
- `backend/`：後端 Python 核心代碼及測試（`backend/src/`、`backend/tests/`）。
- `frontend/`：前端應用代碼。
- `deployment/`：基礎設施與佈署相關設定（如 `Dockerfile`、`docker-compose.yml`）。
- `docs/`：頂層規格書（`docs/SPEC.md`）、ADR 設計決策以及架構 roadmaps 文件。
- `openspec/`：OpenSpec 變更計畫、行為合約與任務清單管理。

## Current OpenSpec Change

Active change:

```bash
openspec show restructure-project-directories
openspec validate restructure-project-directories --strict --no-interactive
```

Change artifacts:

- `openspec/changes/restructure-project-directories/proposal.md`
- `openspec/changes/restructure-project-directories/design.md`
- `openspec/changes/restructure-project-directories/tasks.md`
- `openspec/changes/restructure-project-directories/specs/*/spec.md`

## Current Phase

專案正處於 Phase 2: Create Manual Gold Dataset (手動黃金數據集建立) 階段，目前已引進後端 API、數據合約與圖資料編譯推理架構。
