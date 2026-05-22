# Gemini 代理程式專屬開發守則 (gemini.md)

本文件是為 CDD-GraphWiki 專案的 Gemini 核心代理程式 (Antigravity) 訂定的最高開發憲法與規範指南，確保未來的開發流程 100% 依循 OpenSpec (OPSX) 的規範、高標準的軟體工程實踐，並完美融合 Everything Claude Code (ECC) 的敏捷與安全技能。

---

## 1. 核心溝通與文件語言限制

> [!IMPORTANT]
> - **必須完全使用繁體中文 (Traditional Chinese)** 進行所有回覆、說明、系統規劃文件 (如 Proposal, Design, Tasks, Walkthrough 等) 的撰寫。
> - 代碼註解與系統提示訊息也應優先使用繁體中文。
> - 技術術語、API 欄位名稱、變數名、方程式等，可保持其原始英文形式，以確保語意精確。

---

## 2. 標準化開發生命週期 (SOP)

非 trivially simple 的變更（如中大型功能、API 合約修改、核心實作等），**必須 (MUST)** 嚴格遵循以下五個階段的開發流程：

### 2.1 階段一：調研與文件閱讀 (Research)
在動手寫任何代碼或規劃前，必須：
1. 全面閱讀相關背景文件，包含專案根目錄的 [SPEC.md](file:///Users/andrew-ideaslab/Documents/CDD-GraphWiki/SPEC.md)、[HANDOVER.md](file:///Users/andrew-ideaslab/Documents/CDD-GraphWiki/HANDOVER.md)。
2. 閱讀 `docs/adr/` 目錄下的架構決策紀錄 (ADRs)，理解系統架構的設計哲學（例如 [ADR-0004](file:///Users/andrew-ideaslab/Documents/CDD-GraphWiki/docs/adr/0004-schema-representation-and-python-dataclass-strategy.md) 的混合元模型策略）。
3. 檢查現有的程式碼與已有的 OpenSpec changes，避免重複造輪子。

### 2.2 階段二：建立變更與提案 (Propose & Plan)
1. 在 `openspec/changes/` 下建立專屬的變更目錄（例如 `create-manual-gold-dataset`）。
2. **必須一次性備齊且寫滿**以下四個核心文件（嚴禁殘缺）：
   - **`proposal.md`**：明確定義動機 (Why)、變更範圍 (What Changes)、系統能力 (Capabilities) 與影響範圍 (Impact)。不涉及技術代碼細節。
   - **`design.md`**：說明具體技術實現方案 (How)，明確關聯架構決策 (ADR-XXXX 等)，列出預計變更的檔案列表與測試策略。
   - **`tasks.md`**：建立顆粒度精細的 checkbox 實作任務清單，包含相依關係，且必須包含獨立的「驗證/測試」任務。
     > [!IMPORTANT]
     > - **任務標題必須嚴格按照 OpenSpec 規範使用英文**（例如 `## 1. Group Name` 與 `- [ ] 1.1` 格式），以便 parser 能正確識別並進行狀態追蹤與自動勾選。
   - **`specs/<capability-name>/spec.md`**：定義系統行為合約的 Delta Spec。
     > [!IMPORTANT]
     > - 必須使用 OpenSpec 解析器支援的標準 Section 標題：
     >   - `## ADDED Requirements`
     >   - `## MODIFIED Requirements`
     >   - `## REMOVED Requirements`
     > - 每個 Requirements 標題必須使用標準英文前綴：`### Requirement: [名稱]`。
     > - 語意描述中必須使用 **SHALL** 或 **MUST**。
     > - 每個 Requirement 下面必須至少包含一個標準英文前綴的 Scenario：`#### Scenario: [場景名稱]`。
     > - 推薦使用 `GIVEN` / `WHEN` / `THEN` 格式來界定初始條件、觸發事件與預期結果。
3. **規劃階段對齊 (Grill-Me Alignment) [新增強約束]**：
   * **在上述四個規劃文件備齊後、正式送交審批前，代理程式必須 (MUST) 主動建議並觸發 `/grill-me` 深度面試技能。**
   * 透過 `/grill-me` 功能，代理程式應與使用者針對該變更的最關鍵設計決策（如第三方依賴引入、API 邊界顆粒度、持久化策略）進行一對一問答，直到雙方達成明確共識。
   * **對齊的決策必須正式寫入並更新至 `design.md` 中的「深度面試對齊之核心決策設計 (/grill-me 共識)」小節**，確保有案可稽。

### 2.3 階段三：使用者審查阻斷器 (Review & Approve)
1. 將上述四個規劃文件備齊且**完成 `/grill-me` 設計面試與決策歸檔**後，代理程式**必須暫停**，將變更計畫與實作計畫以連結方式呈現給使用者。
2. **在獲得使用者明確的「審查批准」或指示「開始實作」前，嚴禁修改 `src/` 或 `data/` 底下的核心代碼。**
3. 使用者在此階段只需專注於 Review Plan。

### 2.4 階段四：實作與防禦性開發 (Apply & Implement)
獲得批准後，代理程式開始自動化開發：
1. **遵守 Everything Claude Code (ECC) 守則**：
   - **手術式修改 (Surgical Edits)**：精準修改與需求相關的程式碼，不隨意重構，保持註解與風格一致。清除自己造成的無用 imports/變數。
   - **最小化依賴 (Minimal Dependencies)**：優先使用 Python 標準庫，引入任何第三方套件（如 Pydantic、jsonschema 等）必須在設計階段聲明並獲得批准。
   - **條款級溯源 (Clause-level Provenance)**：合規系統中的每一項規則、合規決策、對象與 checklist，必須保留並標記其源自 FATF 10、MAS 626 或 internal policies 的具體 clause 編號與來源。
   - **Python 標準**：遵循 PEP 8，使用 Type Hinting。在邊界處做防禦性校驗並拋出明確的異常。
2. **融入合規技能：API 設計規範（/api-design）**：
   - 資源 URL 命名為複數、小寫、`kebab-case`（例如 `/api/v1/compliance-rules`）。
   - 語意化 HTTP 方法（GET, POST, PUT, PATCH, DELETE）與正確的 Status Codes（例如 201 Created 且含 Location 標頭，422 Unprocessable Entity 做語意校驗，絕不在 200 OK 回應中包裝 `"success": false`）。
   - 標準 Collection 回應分頁包裝（`data` 陣列、`meta` 屬性包含 `total`, `has_next`, `next_cursor`）。
   - 錯誤回應使用標準 `error` 物件，包含 `code`, `message` 及可選的欄位錯誤列表 `details`。
3. **融入合規技能：安全與防禦性編程（/security-review）**：
   - **Secrets Management**：嚴禁在代碼中硬編碼 API keys、密鑰或密碼。必須從環境變數讀取並校驗其存在性。
   - **Input Validation**：所有外部輸入在進入業務邏輯前，必須使用強型別 Schema（例如 Pydantic）進行白名單校驗。
   - **SQL Injection Prevention**：任何資料庫或圖資料庫查詢，必須使用參數化查詢（parameterized queries），絕不使用字串拼接。
   - **Sensitive Data Redaction**：日誌中嚴禁列印個人資料（PII）或密碼；錯誤訊息必須脫敏，對用戶顯示通用訊息，詳細錯誤僅輸出於伺服器日誌（不洩漏 stack trace）。
4. **即時追蹤進度**：實作中必須隨時依進度勾選 `tasks.md` 內部的 checkbox，保持文件與程式碼一致性。

### 2.5 階段五：驗證、審查與交付 (Verify & Deliver)
實作完成後，代理程式必須執行以下自動化驗證與交付流程：
1. **自主 Code Review**：在提交前，代理程式應自行審查代碼變更，確認語意正確、無語法與安全漏洞、無多餘無用代碼。
2. **測試驗證**：執行本地測試套件（`pytest`），確保新增的單元測試與現有測試 100% 通過（測試覆蓋率應達到 80%+）。
3. **OpenSpec 校驗**：執行 `openspec validate [change-name] --strict --no-interactive`，必須保證輸出為 valid。
4. **封存 Change**：驗證無誤後，執行 `openspec archive [change-name] --yes` 將 Delta Specs 合併至主 specs 目錄並封存。
5. **常規提交與推送 (Conventional Commit & Push)**：
   - 撰寫符合 Conventional Commits 規範的 commit message（例如 `feat(cdd): add manual gold dataset validation`）。
   - 執行 `git commit`。
   - 執行 `git push` 推送至遠端倉庫。
6. **撰寫 Walkthrough**：更新或撰寫 [walkthrough.md](file:///Users/andrew-ideaslab/Documents/CDD-GraphWiki/walkthrough.md) 以總結所做變更、測試成果，並向用戶報告。

---

## 3. 當前開發階段 (Current Phase)

- **當前階段**：**Phase 2: Create Manual Gold Dataset (手動黃金數據集建立)**
- **活動變更**：`create-manual-gold-dataset`
- **架構指導**：[ADR-0004](file:///Users/andrew-ideaslab/Documents/CDD-GraphWiki/docs/adr/0004-schema-representation-and-python-dataclass-strategy.md)
