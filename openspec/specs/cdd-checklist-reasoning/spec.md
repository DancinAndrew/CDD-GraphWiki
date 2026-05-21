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
* 當企業客戶的持股比例大於等於 10% 且小於等於 25% 時，**MUST** 觸發內部政策股權審查紅線 `internal_ubo_threshold_triggered_10_percent`。
* 當 PEP 客戶來自高風險管轄區 (例如緬甸) 時，**MUST** 同時觸發高風險 PEP 曝險 `pep_from_high_risk_jurisdiction` 與禁止開戶條款 `onboarding_prohibited_by_policy`。
* 當企業客戶的股權層級高達 5 層且 UBO 未明時，**MUST** 觸發 UBO 未明 `unclear_ubo_status` 與過度嵌套 `excessive_layering_5`。

#### Scenario: Internal UBO Threshold Triggers GB Policy
* **GIVEN** 一個企業客戶情境，其單一主要股東持股為 15% (`major_shareholder_pct=15`)。
* **WHEN** 引擎對該情境進行合規推理時。
* **THEN** 產出的 `risk_triggers` 列表中 **MUST** 包含 `internal_ubo_threshold_triggered_10_percent`。

---

### Requirement: Auditable Evidence Compilation and Clause Provenance
決策引擎 **SHALL** 根據決策分級與風險觸發點，編譯出必備合規佐證文件清單 (`required_documents`)，並自動關聯條款級溯源引用 (`citations`)。
* 對於普通低風險個人客戶，佐證文件 **SHALL** 至少配備身分證件與地址證明。
* 對於政策禁止開戶或高風險 UBO 客戶，佐證文件 **MUST** 自動變更為拒絕開戶通知及 STR 評估申報等防禦性合規記錄文件。
* 輸出的 `citations` **MUST** 包含源法規 (如 MAS Notice 626 或 FATF) 的條款引用。

#### Scenario: Prohibited PEP Onboarding Documentation
* **GIVEN** 一個緬甸籍且有 PEP 曝險的高風險客戶情境。
* **WHEN** 引擎執行推理判定時。
* **THEN** 產出的 `required_documents` **SHALL** 精確包含 `["Rejected Onboarding Notification", "Suspicious Transaction Report (STR) Draft"]`，且其 `citations` 包含 `["Global Bank Policy Section 4.5.3"]`。

