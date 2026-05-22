# 設計方案：專案資料夾結構與規範整理

本設計說明了重構 CDD-GraphWiki 專案資料夾結構的具體執行路徑、搬移策略、規則合併邏輯，以及針對 `/grill-me` 深度面試中所達成的核心共識設計。

## 1. 深度面試對齊之核心決策設計 (/grill-me 共識)

在與使用者的 `/grill-me` 深度對齊面試中，我們達成了以下 100% 的一致共識：
- **後端 Python 目錄**：選擇將 `src/` 與 `tests/` 移動至 `backend/src/` 與 `backend/tests/`，以確保與前端 `frontend/` 資料夾形成完美的對稱（方案 A）。
- **規格文件定位**：將根目錄的 `SPEC.md` 移動至 `docs/SPEC.md`（方案 A），以將所有規劃文件與 ADR 集中收納於 `docs/` 下。
- **佈署資料夾命名**：選擇使用 `deployment/` 作為資料夾名稱，將與 Docker 相關的佈署檔案移入（方案 A）。
- **廢棄 Demo 處理**：對用不到的 `audit_report_demo.html`, `regulatory_graph_demo.html`, `demo.py` 以及 `demo_ingestion_nim.py` 進行完全刪除（方案 A），保持 git 歷史的簡潔性。
- **HANDOVER.md 處理**：直接刪除 `HANDOVER.md`，因其描述之歷史狀態已不適用於當前實作階段（方案 A）。

---

## 2. 具體搬移與調整策略

### 2.1 後端目錄結構 (backend/)
我們將重構為：
```text
backend/
├── src/           # 原根目錄 src/
├── tests/         # 原根目錄 tests/
└── requirements.txt
```
所有原 `src/` 底下的子套件（如 `src/api`、`src/graph`、`src/ingestion` 等）保持原來的模組結構，僅最上層目錄變更為 `backend/src/`。

### 2.2 佈署設定 (deployment/)
我們將建立：
```text
deployment/
├── Dockerfile
└── docker-compose.yml
```
> [!NOTE]
> 搬移後需注意：由於 `Dockerfile` 移動至 `deployment/`，其內部的 COPY 指令以及 Docker Compose 中的 `context` 路徑可能需要隨之調整。在實作時，我們會確保其路徑指針正確，避免構建失敗。

### 2.3 規劃與文件集約化 (docs/ 與 openspec/)
- 搬移：`SPEC.md` -> `docs/SPEC.md`
- 修正所有關聯參考：
  - `openspec/config.yaml`（更新規格描述與 `SPEC.md` 路徑）
  - `gemini.md`（更新條款與 Research 階段 SOP 裡提及的 `SPEC.md` 路徑）
  - `README.md`（更新專案架構說明）

### 2.4 AI 開發規範合併 (gemini.md)
將 `AGENTS.md` 中的精華內容併入 `gemini.md` 的 `## 4. CDD-GraphWiki 專案專屬約束與運作規則`，包含：
- **ECC 來源與本地參考說明**（`.agents/` 與 `.codex/`）
- **專案核心硬約束**（不轉為 generic RAG、Corpus 保持精簡、條款級溯源、人工審查機制）
- **行為護欄與開發 Workflow**
- **Python PEP 8 與邊界防禦標準**
合併完成後，刪除 `AGENTS.md`。

---

## 3. 預計變更的檔案列表

### 3.1 新增與移動檔案 [NEW / MOVE]
- `docs/SPEC.md` (自 `SPEC.md` 移動)
- `deployment/Dockerfile` (自 `Dockerfile` 移動)
- `deployment/docker-compose.yml` (自 `docker-compose.yml` 移動)
- `backend/requirements.txt` (自 `requirements.txt` 移動)
- `backend/src/*` (自 `src/*` 移動)
- `backend/tests/*` (自 `tests/*` 移動)

### 3.2 修改檔案 [MODIFY]
- `gemini.md` (合併 `AGENTS.md` 的規則，更新 `SPEC.md` 路徑)
- `openspec/config.yaml` (更新 `SPEC.md` 路徑與當前狀態描述)
- `README.md` (更新專案目錄結構描述與引用)

### 3.3 刪除檔案 [DELETE]
- `SPEC.md` (已移動)
- `Dockerfile` (已移動)
- `docker-compose.yml` (已移動)
- `requirements.txt` (已移動)
- `AGENTS.md` (已合併至 `gemini.md`)
- `HANDOVER.md` (已廢棄)
- `audit_report_demo.html` (已廢棄)
- `regulatory_graph_demo.html` (已廢棄)
- `demo.py` (已廢棄)
- `demo_ingestion_nim.py` (已廢棄)

---

## 4. 測試與驗證策略

本變更是目錄結構的重大整理，測試重點在於**環境完整性與 OpenSpec 驗證**：
1. **本地測試套件執行**：
   - 調整測試指令，從 `pytest` 改為在 `backend` 目錄下執行，或使用 `PYTHONPATH=backend/src pytest backend/tests`。
   - 確保所有測試正常運作。
2. **OpenSpec 變更驗證**：
   - 執行 `openspec validate restructure-project-directories --strict --no-interactive`，確保本次變更規範 100% 格式正確且 Valid。
