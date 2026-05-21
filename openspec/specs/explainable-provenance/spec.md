# explainable-provenance Specification

## Purpose
TBD - created by archiving change create-explainable-provenance-engine. Update Purpose after archive.
## Requirements
### Requirement: Provenance Node and Explanation Path Models
系統 **MUST** 擴充 Pydantic 資料合約，新增強型別且符合 schema 驗證的 `ProvenanceNode` 與 `ExplanationPath` 類，以表達結構化的溯源系譜。
* `ProvenanceNode` **SHALL** 包含：
  * `node_id`: 節點 ID
  * `node_type`: 節點類型 (例如 `customer_fact`, `obligation`, `clause`, `document`)
  * `label`: 人類可讀標籤
  * `properties`: 包含具體事實屬性（如客戶屬性 `pep_exposure = True` 或法條明文 `raw_text`）的字典 payload
* `ExplanationPath` **SHALL** 包含：
  * `target_item`: 被解釋的目標項目（如 `"Senior Management Approval Form"`）
  * `path_nodes`: 由起點 `ProvenanceNode` 到終點 `ProvenanceNode` 依序組成的有向路徑列表
  * `description`: 人類可讀的合規論述摘要

#### Scenario: Explanation Model Validation
* **GIVEN** 合規溯源的強型別 `ProvenanceNode` 與 `ExplanationPath` 模型。
* **WHEN** 載入或實例化包含完整溯源路徑的物件時。
* **THEN** Pydantic 校驗 **SHALL** 順利通過，且能正確序列化為 JSON Schema。

---

### Requirement: Compliance Decision Explainer and Lineage
系統 **SHALL** 實作 `ProvenanceEngine` 決策解釋器，能夠為 `CDDChecklist` 中的任何要求或風險標記，推理產出 100% 忠實的「合規解釋鏈」。
* 對於 `CDDChecklist` 中的必備佐證文件（如 `"Source of Funds Declaration & Evidence"`），`ProvenanceEngine` **MUST** 自動回溯至引發它的客戶屬性特徵（如 `pep_exposure = True`）、適用的義務（如 `ob_pep_edd_mas`）以及源法源條文（如 `mas626_clause_04`）。
* 解釋鏈中的 `Clause` 節點 **MUST** 精確引述原始條文的明文（如 `raw_text` 或 `normalized_text`），確保解釋有理有據，杜絕生成模型幻覺。

#### Scenario: Explaining PEP Senior Management Approval Requirement
* **GIVEN** 客戶情境包含政要曝險且已被決策引擎推理產出的 `CDDChecklist`。
* **WHEN** 調用 `ProvenanceEngine.explain_item(checklist, "Senior Management Approval Form", customer, obligations, clauses, documents)` 時。
* **THEN** 產出的 `ExplanationPath` **SHALL** 成功生成：
  * 其首個節點的 `node_type` 為 `customer_fact` 且屬性包含 `pep_exposure = True`。
  * 其必備包含適用義務 `ob_pep_edd_mas` 節點。
  * 其包含條款 `mas626_clause_04` 節點，且該節點的屬性包含 `MAS Notice 626 Paragraph 7.2` 的 raw_text 明文。

---

### Requirement: Traceable Audit Trail Export
系統 **SHALL** 支援將合規解釋鏈導出為人類可讀的 Markdown 審計軌跡報告，以供合規官員與審計人員進行金檢複查。
* 導出的 Markdown 審計報告 **SHALL** 以清晰的層級與有向箭頭表示溯源路徑。
* 報告 **MUST** 忠實呈現條款級溯源引用，且不得丟失原始條文明文。

#### Scenario: Generating Human-Readable Audit Report
* **GIVEN** 一個結構化的 `ExplanationPath` 實例。
* **WHEN** 調用 `ProvenanceEngine.generate_audit_report(explanation_paths)` 時。
* **THEN** 系統 **SHALL** 返回一段格式完美的 Markdown 字串，其中包含清晰的引用引述（如 `> MAS Notice 626 Paragraph 7.2...`）與合規解釋脈絡。

