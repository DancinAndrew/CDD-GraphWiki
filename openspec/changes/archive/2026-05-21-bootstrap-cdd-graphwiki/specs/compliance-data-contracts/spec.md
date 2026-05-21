## ADDED Requirements

### Requirement: 定義核心合規對象 (Define Core Compliance Objects)
本專案在實作任何抽取或決策邏輯之前，**應 (SHALL)** 定義 `SourceDocument`、`Clause`、`Citation`、`Concept`、`Obligation`、`EvidenceRequirement`、`CustomerContext`、`Conflict`、`CDDChecklist` 和 `ReviewCase` 的第一階段資料合約。

#### Scenario: 首次實作啟動 (First implementation begins)
- **當 (WHEN)** 實作工作開始時
- **則 (THEN)** 每個核心合規對象都必須擁有明確的 JSON 或 YAML 範例，以及已記錄的必要欄位。

### Requirement: 在衍生對象上包含來源追溯 (Include Provenance On Derived Objects)
每個衍生對象**應 (SHALL)** 包含指向用於建立該對象之源條款 (source clauses) 或源文件 (source documents) 的引用關係。

#### Scenario: 義務引用來源條款 (Obligation references source)
- **當 (WHEN)** 從 MAS 條款中建立一個 `Obligation` 時
- **則 (THEN)** 該義務必須包含至少一個 `source_clause_id`，且可以追溯回原始法規文本。

### Requirement: 在高風險對象上包含審核狀態 (Include Review Status On Risky Objects)
凡是會影響法律解釋、監管閾值、衝突解決、所需證據或升級路由要求的合規對象，**應 (SHALL)** 包含審核狀態。

#### Scenario: 低置信度義務 (Low-confidence obligation)
- **當 (WHEN)** 抽取出的義務具有低置信度或模糊條件時
- **則 (THEN)** 該義務必須被標記為 `pending_human_review` (待人工審核)。

### Requirement: 保持客戶畫像情境結構化 (Keep Customer Context Structured)
客戶輸入**應 (SHALL)** 表示為結構化的 `CustomerContext` 對象，而非僅僅是自然語言提示詞。

#### Scenario: 評估企業客戶畫像 (Corporate customer profile is evaluated)
- **當 (WHEN)** 系統評估企業客戶時
- **則 (THEN)** 系統必須使用結構化欄位，例如客戶類型、註冊管轄區、股權層級、UBO 狀態、UBO 國家風險、PEP 曝露和證據可用性。

### Requirement: 架構元模型強制性欄位 (Schema Metamodel Mandatory Fields)
核心 Schemas **應 (SHALL)** 嚴格強制要求存在關鍵的元數據、來源追溯和結構欄位，以保證可審計性。每個契約在編譯生成的 Schema 中，**必須 (MUST)** 宣告以下欄位為必要 (mandatory)：
- `SourceDocument` **應 (SHALL)** 要求：`source_document_id`, `title`, `issuer`, `jurisdiction`, `version`, `retrieval_date`, `local_path`。
- `Clause` **應 (SHALL)** 要求：`clause_id`, `source_document_id`, `section_ref`, `raw_text`, `normalized_text`, `citations`。
- `Obligation` **應 (SHALL)** 要求：`obligation_id`, `source_clause_ids`, `jurisdiction`, `actor`, `action`, `object`, `confidence`, `review_status`。
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
