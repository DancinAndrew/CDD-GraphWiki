# Gemini 代理程式專屬開發守則 (gemini.md)

本文件是為 CDD-GraphWiki 專案的 Gemini 核心代理程式 (Antigravity) 訂定的規範指南，確保未來的開發流程 100% 依循 OpenSpec (OPSX) 的規範與高標準的軟體工程實踐。

## 1. 核心溝通與文件語言限制

> [!IMPORTANT]
> - **必須完全使用繁體中文 (Traditional Chinese)** 進行所有回覆、說明、系統規劃文件 (如 Proposal, Design, Tasks, Walkthrough 等) 的撰寫。
> - 代碼註解與系統提示訊息也應優先使用繁體中文。
> - 技術術語、API 欄位名稱、變數名、方程式等，可保持其原始英文形式，以確保語意精確。

## 2. OpenSpec (OPSX) 工作流規範

為了避免規格漂移與無序開發，凡是非簡單的變更（如中大型功能、API 合約修改、核心實作等），**必須 (MUST)** 嚴格遵循 OpenSpec 行為規範：

### 2.1 建立變更階段 (Propose)
- 在 `openspec/changes/` 下建立專屬的變更目錄（例如 `implement-compliance-data-contracts`）。
- **必須一次性備齊且寫滿**以下四個核心文件，嚴禁「只寫 spec」的殘缺做法：
  1. `proposal.md`：明確定義動機 (Why)、變更範圍 (What Changes)、能力 (Capabilities)、影響範圍 (Impact)。不涉及技術代碼細節。
  2. `design.md`：說明技術實現方案 (How)，明確關聯架構決策 (ADR-0004 等)，列出預計變更的檔案列表與測試策略。
  3. `tasks.md`：建立顆粒度精細的 checkbox 實作任務清單，包含相依關係，且必須包含獨立的「驗證/測試」任務。
  4. `specs/<capability-name>/spec.md`：定義系統行為合約的 Delta Spec。

### 2.2 Delta Spec 語法硬性約束
- 必須使用 OpenSpec 解析器支援的標準 Section 標題：
  - `## ADDED Requirements`
  - `## MODIFIED Requirements`
  - `## REMOVED Requirements`
- 每個 Requirements 標題必須使用標準英文前綴：`### Requirement: [名稱]`。
- 語意描述中必須使用 **SHALL** 或 **MUST**。
- 每個 Requirement 下面必須至少包含一個標準英文前綴的 Scenario：`#### Scenario: [場景名稱]`。
- 推薦使用 `GIVEN` / `WHEN` / `THEN` 格式來界定初始條件、觸發事件與預期結果。

### 2.3 實作與驗證階段 (Apply & Verify)
- 唯有在上述規劃文件（Proposal, Spec, Design, Tasks）被使用者審查並**明確批准**後，方可開始修改 `src/` 底下的代碼。
- 實作中必須隨時依進度勾選 `tasks.md` 內部的 checkbox，保持文件與程式碼一致性。
- 實作完成後，必須執行以下驗證：
  - 本地測試套件（如 `pytest`），保證 100% 通過。
  - OpenSpec 語法校驗：`openspec validate [change-name] --strict --no-interactive`，必須保證輸出為 valid。

### 2.4 封存與同步階段 (Archive)
- 驗證無誤後，必須執行封存指令將 Delta Specs 同步至主 Specs 目錄並封存歷史：
  `openspec archive [change-name] --yes`

## 3. 當前開發階段 (Current Phase)

- **當前階段**：**Phase 1: Compliance Data Contracts (資料合約實作)**
- **活動變更**：`implement-compliance-data-contracts`
- **架構指導**：[ADR-0004](file:///Users/andrew-ideaslab/Documents/CDD-GraphWiki/docs/adr/0004-schema-representation-and-python-dataclass-strategy.md) (混合元模型策略)
