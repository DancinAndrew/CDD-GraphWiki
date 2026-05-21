# association-conflict-detection Specification

## Purpose
本規格定義了同義詞同名化 (Alias Deduplication) 與自動化合規衝突偵測引擎原型 (Association & Conflict Detection Prototype) 的核心行為與要求，確保別名映射與三類核心衝突 (Numerical 與 PolicyReversal) 能被自動精確識別、建立強型別 `Conflict` 實體，並保留條款級溯源鏈結。

## ADDED Requirements

### Requirement: Concept Strong-Typed Model
系統 **MUST** 擴充 Pydantic 資料合約，新增強型別且符合 schema 驗證的 `Concept` 類。
* `Concept` 實體 **SHALL** 包含：
  * `concept_id`: 標稱 ID (例如 `ubo`, `pep`, `cdd`, `edd`, `sofw`)
  * `name`: 概念顯示名稱
  * `description`: 概念的簡短中文描述
  * `aliases`: 別名列表 (例如 `["UBO", "beneficial owner", "controlling party"]`)
  * `source_clause_ids`: 條款級溯源 ID 列表

#### Scenario: Concept Model Validation
* **GIVEN** 合規概念的強型別 `Concept` 模型。
* **WHEN** 載入黃金數據的 Concept 數據，或手動建立符合 Pydantic 定義的 Concept 物件時。
* **THEN** Pydantic 校驗 **SHALL** 順利通過，且能正確序列化與反序列化。

---

### Requirement: Alias Deduplication Mapping
系統 **SHALL** 實作 `ConceptMapper` 元件，提供將各種變體別名統一映射至標稱概念 (Canonical Concept) 的能力。
* `ConceptMapper` **MUST** 支援不區分大小寫、去空格以及基本變體的正規表達式或精確比對。
* `ConceptMapper` **SHALL** 能夠將 "UBO", "beneficial owner", "controlling party" 等別名全部正確映射至 `ubo` 標稱概念。
* `ConceptMapper` **SHALL** 能夠將 "PEP", "politically exposed person", "PEP exposure" 等別名正確映射至 `pep` 標稱概念。

#### Scenario: Alias Mapping Resolution
* **GIVEN** 已載入並配置的 `ConceptMapper`，其中 `ubo` 對應別名 `["UBO", "beneficial owner", "controlling party"]`。
* **WHEN** 輸入包含別名 `"controlling party"` 或 `"beneficial owner"` 的條文文字或詞組時。
* **THEN** `ConceptMapper` **SHALL** 返回其對應的標稱概念 ID `ubo`。

---

### Requirement: Numerical Conflict Detection
系統 **SHALL** 實作 `ConflictDetector` 引擎，能夠自動分析載入的 `Obligation` 實體並檢測出數值型限制不一致的 `Numerical` 衝突。
* 系統 **MUST** 能自動比對不同 Obligation 間對於同一 object 或條件的數值門檻差異，例如：
  * MAS Notice 626 的 `ob_identify_ubo_25_mas` 控制股權閾值為 `>25%`。
  * Global Bank Policy 的 `ob_identify_ubo_10_gb` 控制股權閾值為 `>=10%`。
  * FATF Rec 10 的 `ob_cdd_on_relationship` 偶發交易閾值為 `USD/EUR 15,000`。
  * MAS Notice 626 的 `ob_cdd_on_relationship_mas` 偶發交易閾值為 `SGD 20,000`。
* `ConflictDetector` **SHALL** 針對這些數值不一致自動產出符合 `Conflict` 資料合約的實體，包含完整的 `conflict_id`、`conflict_type="Numerical"`、`source_clause_ids` 以及 `description`。

#### Scenario: Auto Detect Numerical Conflicts
* **GIVEN** 包含 MAS `ob_identify_ubo_25_mas` 與 Global Bank `ob_identify_ubo_10_gb` 的 `Obligation` 列表。
* **WHEN** 呼叫 `ConflictDetector.detect_conflicts(obligations)` 時。
* **THEN** 系統 **SHALL** 自動識別並生成 `conf_ubo_threshold` 衝突，其類型為 `Numerical`，且 `source_clause_ids` 包含這兩個 Obligation 的源條款。

---

### Requirement: Policy Reversal Conflict Detection
系統 **SHALL** 在 `ConflictDetector` 引擎中實作政策禁止/反轉衝突檢測能力。
* 當一個法規 Obligation 許可某項高風險行為 (例如：MAS Notice 626 的 `ob_pep_edd_mas` 允許在 Senior Management 審批與 EDD 的情況下 onboard PEP)；但另一個內部政策 Obligation 嚴格禁止該行為的特定子集 (例如：Global Bank Policy 的 `ob_pep_prohibitions_gb` 嚴格禁止 onboarding 來自高風險地區的 PEP) 時，系統 **SHALL** 能識別此類政策衝突。
* 偵測引擎 **SHALL** 自動產出對應的 `Conflict` 實體，設定 `conflict_type="PolicyReversal"`，並填寫正確的溯源關聯。

#### Scenario: Auto Detect Policy Reversal Conflicts
* **GIVEN** 包含 MAS PEP EDD 與 Global Bank 高風險地區 PEP 禁止 Onboard 的 `Obligation` 列表。
* **WHEN** 執行 `ConflictDetector.detect_conflicts(obligations)` 時。
* **THEN** 系統 **SHALL** 自動識別並生成 `conf_pep_jurisdiction` 衝突，其類型為 `PolicyReversal`。
