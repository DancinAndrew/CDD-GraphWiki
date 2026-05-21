# source-document-parser Specification

## Purpose
TBD - created by archiving change create-source-document-parser. Update Purpose after archive.
## Requirements
### Requirement: Semantic Hierarchical Chunking
法規源解析器 **MUST** 根據原始 Markdown 文件的標題層級（如 `#` 到 `####`）與列表編號（如 `(a)`, `(b)`），將文件切分為樹狀結構的 `Clause` 實體，保留條款的父子語意關係。

#### Scenario: Verify Hierarchical Tree Construction
*   **GIVEN** 包含嵌套標題與列表的原始法規 Markdown 文件。
*   **WHEN** 執行 Ingestion Parser 解析該文件時。
*   **THEN** 產生的 `Clause` 實體 **SHALL** 滿足：
    *   每個子條款的 `parent_clause_id` 必須正確指向其直接父標題條款的 ID。
    *   頂級標題條款的 `parent_clause_id` 必須為 `null`。
    *   每個條款的 `section_ref` 必須包含其層級路徑（例如 `"Section 4/Paragraph 2/sub-paragraph a"`）。

---

### Requirement: Stable ID Generation
法規源解析器 **MUST** 採用基於文獻標識與物理路徑的 ID 生成演算法，以確保 `clause_id` 在重複運行 (rerun) 與無結構性修改時 100% 保持穩定，杜絕 counter-based 移位漂移。

#### Scenario: Verify ID Stability and Idempotency
*   **GIVEN** 一個原始法規 Markdown 文件。
*   **WHEN** 執行兩次或多次 Parser 運行，或者在不改變樹狀層級結構的前提下修改內容（如調整空格或部分無關文字）。
*   **THEN** 產生的所有 `Clause` 實體的 `clause_id` **SHALL** 保持完全恆定不變，且 **MUST NOT** 發生任何物理移位。

---

### Requirement: Contract Compliance and Output Serialization
法規源解析器產出的所有實體 **MUST** 100% 符合強型別 Pydantic 資料合約，並自動序列化導出。

#### Scenario: Verify Output Pydantic Compliance
*   **GIVEN** Ingestion Parser 執行完畢。
*   **WHEN** 將產生的 `data/processed/clauses.yaml` 與 `data/processed/source_documents.yaml` 載入為 Python Pydantic 物件時。
*   **THEN** 所有資料對象 **SHALL** 順利通過 `BaseModel` 的型別校驗，且 **MUST NOT** 拋出任何 `ValidationError`。

