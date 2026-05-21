# Delta Spec: Manual Gold Dataset

本文件定義了 CDD-GraphWiki 「人工黃金數據集」的系統行為合約與規格約束。

## ADDED Requirements

### Requirement: Gold Dataset Completeness
系統的人工黃金數據集 **MUST** 滿足最低的實體數量與覆蓋範疇，以作為評估自動化 pipeline 的黃金標準（Ground Truth）。

#### Scenario: Verify Minimum Entity Counts
*   **GIVEN** 系統初始化了人工黃金數據集。
*   **WHEN** 測試套件載入 `data/gold/` 底下的所有合規數據。
*   **THEN** 數據集 **SHALL** 至少包含：
    *   3 個 `SourceDocument` 實體。
    *   10 個手動切分的 `Clause` 實體。
    *   10 個手動抽取的 `Obligation` 實體。
    *   3 個法規政策 `Conflict` 實體。
    *   5 個不同風險情境的 `CustomerContext` 實體。
    *   5 個與客戶畫像精準對應的 `CDDChecklist` 預期輸出實體。
    *   5 個以 Markdown 撰寫的 `Concept` 核心百科頁面。

---

### Requirement: Schema-Light and Executable Compliance
人工黃金數據集的所有 YAML 資料對象 **MUST** 100% 符合 Phase 1 所實作的強型別 Pydantic 資料合約。

#### Scenario: Contract Schema Compliance
*   **GIVEN** Phase 1 定義好的 Pydantic 模型（`SourceDocument`、`Clause`、`Obligation`、`CustomerContext`、`Conflict`、`CDDChecklist`）。
*   **WHEN** 將 `data/gold/` 中的 YAML 檔案載入並解封（deserialize）為對應的 Python 物件時。
*   **THEN** 載入過程 **SHALL** 順利完成，且 **MUST NOT** 拋出任何 `ValidationError`。

---

### Requirement: Traceable Clause-Level Provenance
黃金數據集中的所有衍生合規實體 **MUST** 保持嚴格的條款級溯源（Clause-Level Provenance）與關聯完整性，形成封閉的邏輯鏈條。

#### Scenario: Referential Integrity and Provenance Check
*   **GIVEN** 載入成功的全套黃金數據對象。
*   **WHEN** 測試套件執行完整性分析時。
*   **THEN** 系統 **SHALL** 驗證並通過以下約束：
    *   每個 `Clause` 的 `source_document_id` 必須指向一個確實存在的 `SourceDocument`。
    *   每個 `Obligation` 的 `source_clause_ids` 中的每一個 ID，必須指向一個確實存在的 `Clause`。
    *   每個 `Conflict` 的 `source_clause_ids` 中的每一個 ID，必須指向一個確實存在的 `Clause`。
    *   每個 `CDDChecklist` 的 `customer_id` 必須指向一個確實存在的 `CustomerContext`。
    *   每個 `CDDChecklist` 的 `applicable_obligations` 中的每個 ID，必須指向一個確實存在的 `Obligation`。
    *   每個 `CDDChecklist` 的 `unresolved_conflicts` 中的每個 ID，必須指向一個確實存在的 `Conflict`。
