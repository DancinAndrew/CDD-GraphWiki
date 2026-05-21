## Why (為什麼要做)

為了解決 CDD-GraphWiki 專案在啟動自動化抽取與合規推理（Phase 2/3）之前所需的強類型契約問題。通過實作本階段的「資料合約」，能確保所有衍生對象（如 `Obligation`, `Conflict`）皆包含完整的來源追溯與審核狀態，並在客戶情境（`CustomerContext`）中實行強健的結構化約束，避免規格漂移與低置信度資料的傳播。

## What Changes (變更內容)

- **核心元模型實作**：在 `src/contracts/` 下實作 6 個核心 Python Dataclasses (`SourceDocument`, `Clause`, `Obligation`, `CustomerContext`, `Conflict`, `CDDChecklist`)，以其作為系統資料合約的「單一事實來源」。
- **自動化編譯指令碼**：實作 `scripts/compile_schemas.py`，能自動將上述 Python Dataclasses 動態編譯並導出為標準 JSON Schema 格式至 `schemas/*.schema.json`。
- **合規實例數據**：在 `schemas/examples/` 下建立與 JSON Schema 完全契合的有效/無效實例數據（支援 JSON 與 YAML），作為後續測試與實作參考。
- **自動化契約驗證**：在 `tests/test_schemas.py` 中撰寫 Schema 驗證與欄位完整性單元測試，確保邊界校驗機制 100% 正確。

## Capabilities (能力描述)

### New Capabilities

- `compliance-data-contracts-implementation`: 提供 6 個核心合規對象的強類型 Python Dataclass 定義，以及自動生成的標準 JSON Schema 檔案，並在編譯器層面保證元數據、來源追溯 (Provenance) 與審核狀態 (Review Status) 等關鍵欄位的強制性。

### Modified Capabilities

- 無。本變更是將先前 bootstrap 確立的 `compliance-data-contracts` 規格正式落實至代碼中。

## Impact (影響範圍)

- **專案結構**：在 `src/` 中新增代碼結構，建立專屬的合約與編譯層。
- **相依套件**：不引入繁重的第三方框架。使用 Python 內建的 `dataclasses` 以及標準 `json` 與簡單的輔助 schema 庫，若需第三方 schema 校驗庫將先徵求同意。
- **相容性**：此為專案的第一階段代碼實作，不存在任何舊版代碼的遷移或破壞性影響。
