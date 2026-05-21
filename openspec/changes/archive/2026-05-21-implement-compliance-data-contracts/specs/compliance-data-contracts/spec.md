## MODIFIED Requirements

### Requirement: 定義核心合規對象 (Define Core Compliance Objects)
本專案在實作任何抽取或決策邏輯之前，**應 (SHALL)** 定義 `SourceDocument`、`Clause`、`Citation`、`Concept`、`Obligation`、`EvidenceRequirement`、`CustomerContext`、`Conflict`、`CDDChecklist` 和 `ReviewCase` 的第一階段資料合約。

#### Scenario: 首次實作啟動 (First implementation begins)
- **給定 (GIVEN)** 啟動資料合約實作
- **當 (WHEN)** 核心模型被載入時
- **則 (THEN)** 每個模型都必須定義強類型的欄位，並支持動態序列化與反序列化。

### Requirement: 單一事實來源的 Schema 生成與代碼一致性 (Single-Source Schema Generation and Code Coherence)
為防止運行時程式碼模型與宣告式校驗契約之間發生規格漂移，系統**應 (SHALL)** 以程式化方式從 Python dataclass 元模型自動生成 `schemas/*.schema.json`。生成之 Schemas **必須 (MUST)** 能夠嚴格校驗有效的 JSON 與 YAML 實例。

#### Scenario: 將 Dataclasses 編譯為 JSON Schema (Compiling dataclasses to JSON Schema)
- **給定 (GIVEN)** 自定義的自動生成指令碼 `scripts/compile_schemas.py`
- **當 (WHEN)** 執行該指令碼時
- **則 (THEN)** 該指令碼**應 (SHALL)** 在 `schemas/` 目錄下精確導出 6 個語意合規的 JSON Schema 檔案，並以退出碼 0 (exit code 0) 結束。
