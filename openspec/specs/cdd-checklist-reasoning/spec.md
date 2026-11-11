# cdd-checklist-reasoning Specification

## Purpose
TBD - created by archiving change create-cdd-checklist-reasoning-engine. Update Purpose after archive.
## Requirements
### Requirement: CDD Tier Decision and Classification
決策引擎 **MUST** 根據客戶背景、地理、股權層級與 PEP 曝險特徵，對客戶進行精準的盡職調查分級判定。
* 分級決策 `decision` **SHALL** 為以下三者之一：`simplified_cdd`、`standard_cdd`、`enhanced_due_diligence` (EDD)。
* 對於普通低風險個人客戶，分級 **SHALL** 判定為 `standard_cdd`。
* 對於政要曝險 (PEP) 或高風險 UBO 情境的客戶，分級 **MUST** 被安全地提升至 `enhanced_due_diligence`。

#### Scenario: Low Risk Individual Classification
* **GIVEN** 一個低風險個人客戶情境 (`customer_type="individual"`, `pep_exposure=False`, `ubo_country_risk="low"`)。
* **WHEN** 引擎對該情境進行合規推理時。
* **THEN** 決策引擎產出的 `decision` **SHALL** 為 `standard_cdd`。

#### Scenario: PEP Exposure Triggers EDD
* **GIVEN** 一個包含 PEP 曝險的個人客戶情境 (`pep_exposure=True`)。
* **WHEN** 引擎對該情境進行合規推理時。
* **THEN** 決策引擎產出的 `decision` **SHALL** 為 `enhanced_due_diligence`。

---

### Requirement: Risk Trigger Identification and Policy Control
決策引擎 **SHALL** 自動識別客戶情境中潛在的政策紅線與合規風險，並啟用正確的風險觸發標記 (`risk_triggers`)。
* 每個風險標記 **MUST** 宣告依據的義務與寫出條件的出處條文；沒有義務要求的條件 **MUST NOT** 成為風險標記。
* 風險標記 **MUST** 只在條件對這位客戶成立時列出：條件的屬性都在決策路徑上被檢驗時，走到該分支即成立；否則由標記自己的條件檢查。
* 當企業客戶的持股比例大於等於 10% 且小於等於 25% 時，**MUST** 觸發內部政策股權審查紅線 `internal_ubo_threshold_triggered_10_percent`。
* 當 PEP 客戶來自高風險管轄區 (例如緬甸) 時，**MUST** 同時觸發高風險 PEP 曝險 `pep_from_high_risk_jurisdiction` 與禁止開戶條款 `onboarding_prohibited_by_policy`。
* 當企業客戶 UBO 未明時，**MUST** 觸發 `unclear_ubo_status`，並依 MAS Notice 626 第 6.35 段拒絕開戶、評估申報可疑交易。註冊地本身 **MUST NOT** 被視為無法完成 CDD。
* 當企業客戶有 3 層以上中間控股公司時（銀行政策 1.2(b)），**MUST** 觸發 `complex_ownership_3_layers`；UBO 已識別時 `decision` **MUST** 為 `enhanced_due_diligence`（1.2(b)(i) 列為高風險），並要求經合規主管簽核的完整持股架構圖（1.2(b)(ii)）。
* 一般 PEP 客戶缺少資金來源或財富來源證明時，**MUST** 分別觸發 `missing_source_of_funds_evidence` 與 `missing_source_of_wealth_evidence`（MAS Notice 626 第 8.3(b) 段）。非 PEP 客戶 **MUST NOT** 觸發這兩個標記，因為知識庫中沒有義務對他們要求這兩項證明。

#### Scenario: Complex Ownership Raises Risk
* **GIVEN** 一個 UBO 已識別、有 3 層中間控股公司的企業客戶情境 (`ownership_layers=3`)。
* **WHEN** 引擎對該情境進行合規推理時。
* **THEN** `decision` **SHALL** 為 `enhanced_due_diligence`，`risk_triggers` **MUST** 包含 `complex_ownership_3_layers`，`required_documents` **MUST** 包含 `Full Ownership Chart Signed Off by Compliance Officer`；同一客戶只有 2 層時兩者都不出現。

#### Scenario: Internal UBO Threshold Triggers GB Policy
* **GIVEN** 一個企業客戶情境，其單一主要股東持股為 15% (`major_shareholder_pct=15`)。
* **WHEN** 引擎對該情境進行合規推理時。
* **THEN** 產出的 `risk_triggers` 列表中 **MUST** 包含 `internal_ubo_threshold_triggered_10_percent`。

---

### Requirement: Auditable Evidence Compilation and Clause Provenance
決策引擎 **SHALL** 根據決策分級與風險觸發點，編譯出必備合規佐證文件清單 (`required_documents`)，並自動關聯條款級溯源引用 (`citations`)。
* 對於普通低風險個人客戶，佐證文件 **SHALL** 至少配備身分證件與地址證明。
* 對於政策禁止開戶或 UBO 未明的客戶，佐證文件 **MUST** 自動變更為拒絕開戶通知及 STR 評估申報等防禦性合規記錄文件。
* 輸出的 `citations` **MUST** 是適用義務的錨點條文 ID（`source_clause_ids` 第一條），可在條文庫與圖譜中解析回原文；來源可以是法規（MAS Notice 626、FATF）或銀行內部政策。

#### Scenario: Prohibited PEP Onboarding Documentation
* **GIVEN** 一個緬甸籍且有 PEP 曝險的高風險客戶情境。
* **WHEN** 引擎執行推理判定時。
* **THEN** 產出的 `required_documents` **SHALL** 精確包含 `["Rejected Onboarding Notification"]`，且其 `citations` 為 `["mock_internal_policy_s_1_customer_onboarding_standards_1_4_politically_exposed_persons"]`（Global Bank Policy 1.4）。

