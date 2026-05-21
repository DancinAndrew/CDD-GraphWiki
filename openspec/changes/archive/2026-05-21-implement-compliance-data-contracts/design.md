## Context (背景脈絡)

本專案是一個合規知識編譯與推理系統，對資料的嚴謹性與可追溯性要求極高。
根據 [ADR-0004 (Schema Representation and Python Dataclass Strategy)](file:///Users/andrew-ideaslab/Documents/CDD-GraphWiki/docs/adr/0004-schema-representation-and-python-dataclass-strategy.md)，我們決定採用 **混合元模型策略 (Hybrid Metamodel Strategy)**：
- **Python Dataclasses** 作為單一事實來源 (Single Source of Truth, SSOT)，用於定義資料合約的語意欄位與型態。
- 自動化編譯指令碼 `scripts/compile_schemas.py` 負責將 Dataclasses 動態翻譯為標準的 **JSON Schema (`schemas/*.schema.json`)**，以供外部系統或跨語言校驗使用。
- 實作應包含對 YAML 和 JSON 的雙重支援，且必須嚴格落實法規來源追溯（Provenance）與審核狀態（Review Status）。

## Technical Approach (技術方案)

### 1. 元模型類別設計 (src/contracts/)
我們將定義以下 6 個強類型的 Dataclasses：
- `SourceDocument`：表示原始監管文件或政策（如 MAS Notice 626）。
- `Clause`：表示從文件中分割出的最小獨立條款，必須包含追溯至源文件的 ID。
- `Obligation`：表示從條款中抽取的合規義務，必須包含 actor, action, object 等要素，以及 `source_clause_ids` 的追溯關係與 `review_status`。
- `CustomerContext`：結構化客戶情境，包含管轄區、股權架構層級、UBO 狀態與國家風險等。
- `Conflict`：表示政策或法規之間的衝突，必須記錄衝突類型與來源條款。
- `CDDChecklist`：最終生成的合規檢核表，包含具體決策、所需文件、適用的條款義務與未決衝突。

### 2. 自動化 Schema 編譯器 (scripts/compile_schemas.py)
我們將實作一個輕量級的 Python 編譯指令碼，利用 Python 的反射機制或第三方庫（如 pydantic 或自製簡單反射器）來生成 JSON Schema。
> [!NOTE]
> 為了保持 codebase 最小相依性，我們將評估是使用 Python 內建的自製反射編譯，還是引入 `pydantic` 或 `jsonschema` 等非常成熟的標準庫。根據專案規範，若需要新增依賴，我們將於 tasks 中安排詢問步驟或使用最簡單的無依賴實現（或在 `pyproject.toml` 中確認已有套件）。

### 3. 目錄結構佈局
本變更將建立以下實體目錄：
- `src/contracts/`：存放 Python Dataclasses 代碼。
- `scripts/`：存放自動化編譯指令碼。
- `schemas/`：存放編譯生成的 JSON Schema 檔案。
- `schemas/examples/`：存放合規與非合規的 YAML/JSON 實例。
- `tests/`：存放 Schema 與 Dataclasses 的單元測試。

## Architecture Decisions (架構決策關聯)

- **關聯 ADR-0004**：本實作完全落實了 ADR-0004 所確立的混合元模型策略，藉由 Python Dataclasses 確保 Python 代碼內部的強類型提示，再藉由編譯出的 JSON Schema 確保宣告式驗證的跨平台一致性。
- **欄位強制性約束**：所有衍生對象必須包含追溯（`source_clause_ids`）與審核欄位（`review_status`），這是為了解決 LLM 抽取的不確定性，強迫系統內部的任何資料都必須帶有明確的稽核軌跡。

## File Changes (檔案變更列表)

### [NEW]
- `src/contracts/__init__.py`
- `src/contracts/models.py`
- `scripts/compile_schemas.py`
- `schemas/examples/source_document_valid.yaml`
- `schemas/examples/clause_valid.yaml`
- `schemas/examples/obligation_valid.yaml`
- `schemas/examples/customer_context_valid.yaml`
- `schemas/examples/conflict_valid.yaml`
- `schemas/examples/cdd_checklist_valid.yaml`
- `tests/test_schemas.py`

## Verification Plan (驗證計畫)

### 自動化測試 (Automated Tests)
我們將在 `tests/test_schemas.py` 中撰寫對應測試：
1. **Schema 編譯測試**：執行 `python scripts/compile_schemas.py`，驗證其是否成功生成 6 個 schema 檔案，且 exit code 為 0。
2. **Schema 校驗測試**：讀取 `schemas/examples/` 下的有效實例，使用 JSON/YAML 解析器與生成的 schema 進行校驗，確保校驗通過。
3. **強制欄位缺失測試**：故意構造缺失追溯或關鍵欄位的實例，驗證 schema 校驗是否能精確攔截並報錯。

### 手動驗證 (Manual Verification)
- 執行 `openspec validate implement-compliance-data-contracts --strict --no-interactive` 來驗證本變更的合規性。
