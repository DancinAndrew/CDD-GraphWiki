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

本專案已順利完成 **Phase 1 到 Phase 10** 的所有開發階段！從資料合約、Parser、義務抽取、知識圖譜、衝突檢測、CDD 推理引擎、人工審查、Evaluation Harness、Compliance Dashboard 到 NVIDIA NIM 整合，全數核心功能均已通過嚴謹的 OpenSpec 規格校驗與封存（共 16 個 OpenSpec change 已全數歸檔）。專案目前已全面收斂完成，步入業務落地與規模化階段。

