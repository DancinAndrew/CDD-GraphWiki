# compliance-data-contracts Specification

## Purpose
TBD - created by archiving change bootstrap-cdd-graphwiki. Update Purpose after archive.
## Requirements
### Requirement: 定義核心合規對象 (Define Core Compliance Objects)
本專案在實作任何抽取或決策邏輯之前，**應 (SHALL)** 定義 `SourceDocument`、`Clause`、`Citation`、`Concept`、`Obligation`、`EvidenceRequirement`、`CustomerContext`、`Conflict`、`CDDChecklist` 和 `ReviewCase` 的第一階段資料合約。

#### Scenario: 首次實作啟動 (First implementation begins)
- **給定 (GIVEN)** 啟動資料合約實作
- **當 (WHEN)** 核心模型被載入時
- **則 (THEN)** 每個模型都必須定義強類型的欄位，並支持動態序列化與反序列化。

### Requirement: 在衍生對象上包含來源追溯 (Include Provenance On Derived Objects)
每個衍生對象**應 (SHALL)** 包含指向用於建立該對象之源條款 (source clauses) 或源文件 (source documents) 的引用關係。

#### Scenario: 義務引用來源條款 (Obligation references source)
- **當 (WHEN)** 從 MAS 條款中建立一個 `Obligation` 時
- **則 (THEN)** 該義務必須包含至少一個 `source_clause_id`，且可以追溯回原始法規文本。

### Requirement: 在高風險對象上包含審核狀態 (Include Review Status On Risky Objects)
凡是會影響法律解釋、監管閾值、衝突解決、所需證據或升級路由要求的合規對象，**應 (SHALL)** 包含審核狀態。

#### Scenario: 大模型匯入的義務 (LLM-imported obligation)
- **當 (WHEN)** 義務由大模型從 PDF 匯入時
- **則 (THEN)** 不論模型自評的 `confidence` 多高，該義務都必須被標記為 `pending_human_review` (待人工審核)。

#### Scenario: 信心值不決定審核狀態 (Confidence does not set review status)
- **當 (WHEN)** 規則式抽取器產生義務時
- **則 (THEN)** `review_status` 不由 `confidence` 決定；`confidence` 只說明該規則類型在保留文本上的實測精確率。

### Requirement: 信心值必須有可重算的依據 (Confidence Must Have A Reproducible Basis)
`Obligation.confidence` 是選填欄位，**不得 (MUST NOT)** 是人工設定的常數。有值時，`confidence_basis` **應 (SHALL)** 用一句話說明數字從哪裡來、在什麼樣本上量到：
- 規則式抽取的義務：`confidence` 是該規則類型在未見過的保留文本上量到的精確率（目前是規則 v2 在英國 2017 年洗錢防制條例第 3 部分、規則凍結後才標註的段落上的結果，段落層級，由管線執行時以程式重算）；`confidence_basis` 寫出樣本與「k of n 個被標上此類型的段落是對的」；`confidence_kind` 為 `measured_on_heldout`。保留文本上從未被標上的類型，`confidence` 與 `confidence_kind` 為空，`confidence_basis` 說明沒有量測。
- 大模型匯入（PDF 匯入）的義務：`confidence` 保留模型自評的分數，`confidence_basis` 說明它是自評且未經校準，`confidence_kind` 為 `self_reported`；模型沒給分數時三者皆為空。大模型匯入的義務不帶規則理由（`explanations` 為空）。
- 人工金標義務不帶 `confidence`。

`confidence_kind` 是區分實測與自評的唯一依據；使用者介面與下游程式**不得 (MUST NOT)** 靠解析 `confidence_basis` 的文字來判斷。

#### Scenario: 規則義務的信心值來自保留文本 (Rule obligation confidence comes from held-out text)
- **當 (WHEN)** 管線以規則式抽取器產生義務時
- **則 (THEN)** 每個義務的 `confidence` 等於其類型在保留文本上的段落層級精確率（四捨五入到小數兩位，未量測為空），`confidence_basis` 說明樣本與計數，有量測值時 `confidence_kind` 為 `measured_on_heldout`、否則為空。

### Requirement: 保持客戶畫像情境結構化 (Keep Customer Context Structured)
客戶輸入**應 (SHALL)** 表示為結構化的 `CustomerContext` 對象，而非僅僅是自然語言提示詞。

#### Scenario: 評估企業客戶畫像 (Corporate customer profile is evaluated)
- **當 (WHEN)** 系統評估企業客戶時
- **則 (THEN)** 系統必須使用結構化欄位，例如客戶類型、註冊管轄區、股權層級、UBO 狀態、UBO 國家風險、PEP 曝露和證據可用性。

### Requirement: 架構元模型強制性欄位 (Schema Metamodel Mandatory Fields)
核心 Schemas **應 (SHALL)** 嚴格強制要求存在關鍵的元數據、來源追溯和結構欄位，以保證可審計性。每個契約在編譯生成的 Schema 中，**必須 (MUST)** 宣告以下欄位為必要 (mandatory)：
- `SourceDocument` **應 (SHALL)** 要求：`source_document_id`, `title`, `issuer`, `jurisdiction`, `version`, `retrieval_date`, `local_path`。
- `Clause` **應 (SHALL)** 要求：`clause_id`, `source_document_id`, `section_ref`, `raw_text`, `normalized_text`, `citations`。
- `Obligation` **應 (SHALL)** 要求：`obligation_id`, `source_clause_ids`, `jurisdiction`, `actor`, `action`, `object`, `review_status`。`confidence`、`confidence_basis` 與 `confidence_kind` 是選填欄位（見「信心值必須有可重算的依據」）。
- `CustomerContext` **應 (SHALL)** 要求：`customer_id`, `customer_type`, `registration_jurisdiction`, `ownership_layers`, `ubo_status`, `ubo_country_risk`, `pep_exposure`, `source_of_funds_available`, `source_of_wealth_available`。
- `Conflict` **應 (SHALL)** 要求：`conflict_id`, `conflict_type`, `source_clause_ids`, `verifiability`, `description`, `adjudication_status`。
- `CDDChecklist` **應 (SHALL)** 要求：`checklist_id`, `customer_id`, `decision`, `required_documents`, `risk_triggers`, `applicable_obligations`, `unresolved_conflicts`, `human_review_required`, `citations`。

#### Scenario: 驗證缺失必要欄位的合規對象 (Validate a minimal compliance object)
- **給定 (GIVEN)** 已編譯生成的 `SourceDocument` Schema
- **當 (WHEN)** 驗證一個缺失 `source_document_id` 的實例時
- **則 (THEN)** Schema 驗證流程**應 (SHALL)** 失敗並拋出欄位缺失錯誤。

### Requirement: 單一事實來源的 Schema 生成與代碼一致性 (Single-Source Schema Generation and Code Coherence)
為防止運行時程式碼模型與宣告式校驗契約之間發生規格漂移，系統**應 (SHALL)** 以程式化方式從 Python dataclass 元模型自動生成 `schemas/*.schema.json`。生成之 Schemas **必須 (MUST)** 能夠嚴格校驗有效的 JSON 與 YAML 實例。

#### Scenario: 將 Dataclasses 編譯為 JSON Schema (Compiling dataclasses to JSON Schema)
- **給定 (GIVEN)** 自定義的自動生成指令碼 `scripts/compile_schemas.py`
- **當 (WHEN)** 執行該指令碼時
- **則 (THEN)** 該指令碼**應 (SHALL)** 在 `schemas/` 目錄下精確導出 6 個語意合規的 JSON Schema 檔案，並以退出碼 0 (exit code 0) 結束。

