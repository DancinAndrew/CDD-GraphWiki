# create-obligation-extractor-prototype Specification

## Purpose
TBD - created by archiving change create-obligation-extractor-prototype. Update Purpose after archive.
## Requirements
### Requirement: Structuring Compliance Obligations

系統 **SHALL** 能夠讀取 `Clause` 條款，透過規則匹配抽取並編譯為結構化的 `Obligation` 實體，且該實體 **MUST** 100% 契合系統 `Obligation` Pydantic 強型別合約與 JSON Schema 契約。

#### Scenario: Successfully Extracting CDD Requirements
* **GIVEN**: 一個包含 `establishing business relationships` 關鍵字且來源為 `mas_notice_626` 的 CDD 一般條款。
* **WHEN**: 執行 `RuleBasedObligationExtractor` 進行規則匹配與結構化抽取時。
* **THEN**: 系統 **SHALL** 成功產出一個 `Obligation` 實體，其中包含 `actor` 為 `bank`、`action` 為 `perform_cdd`、`object` 為 `customer`、以及 `jurisdiction` 為 `Singapore`。且該實體能順利通過 `Obligation.model_validate` 驗證。

---

### Requirement: Compliance Extraction Failure Classification

當條款沒有被任何規則判定為義務類型時，系統 **SHALL** 拒絕隨意合成不實數據，而是將其進行精準的失敗原因分類，並將其導出至人工審查報告隊列（`low_confidence_review_queue.yaml`，檔名沿用舊版）中。失敗原因只有兩種：
- `MISSING_CORE_ELEMENTS`：條文含有義務用語（例如 `shall`、`must`），但規則判斷不出完整的義務（例如沒有可辨識的動作或對象）。
- `NON_OBLIGATION_TEXT`：條文不含義務用語，例如標題或背景敘述。

信心值**不得 (MUST NOT)** 決定條文能不能被抽取，也沒有信心門檻：規則義務的 `confidence` 是該規則類型在未見過的保留文本上實測的精確率，附 `confidence_basis` 說明樣本與計數、`confidence_kind` 為 `measured_on_heldout`；保留文本上沒有量測到的類型 `confidence` 為空、`confidence_kind` 為空（見 compliance-data-contracts「信心值必須有可重算的依據」）。

#### Scenario: Confidence does not gate extraction
* **GIVEN**: 一條被規則判定為某義務類型、但該類型在保留文本上沒有量測（`confidence` 為空）的條款。
* **WHEN**: 執行抽取引擎進行義務提取時。
* **THEN**: 系統 **SHALL** 照常產出義務，`confidence` 為空，`confidence_basis` 說明沒有量測，且不會因此被送進人工審查隊列。

#### Scenario: Classifying Non-Obligation Background Text
* **GIVEN**: 一個純文件標題或純背景敘述條款（例如 `fatf_rec10_introduction`）。
* **WHEN**: 執行抽取引擎進行義務提取時。
* **THEN**: 系統 **SHALL** 將其正確判定為抽取失敗，且失敗原因分類 **MUST** 標記為 `NON_OBLIGATION_TEXT`。

---

### Requirement: Compliance Obligation Golden Dataset Evaluation

系統 **SHALL** 具備自動化評鑑機制，能夠讀取自動抽取的義務數據集與手動標記的黃金數據集 (`data/gold/obligations.yaml`) 進行欄位級比對，計算並輸出包含 `Precision`、`Recall` 與 `F1-Score` 的比對評估報告。

#### Scenario: Running Evaluation Against Ground Truth
* **GIVEN**: 自動抽取產出的 obligations 與手動金標 obligations 數據庫。
* **WHEN**: 呼叫評估器比對 `obligation_id`、`source_clause_ids` 等外鍵關聯時。
* **THEN**: 系統 **SHALL** 順利計算出比對指標，且在無結構變更下，比對指標的計算結果 **MUST** 保持恆定與正確。

