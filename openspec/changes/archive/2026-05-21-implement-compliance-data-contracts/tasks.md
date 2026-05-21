## 1. 核心元模型實作 (Python Dataclasses)

- [x] 1.1 在 `src/contracts/` 底下建立 `models.py`，定義 6 個核心 Dataclasses (`SourceDocument`, `Clause`, `Obligation`, `CustomerContext`, `Conflict`, `CDDChecklist`)。
- [x] 1.2 確保每個模型包含指定的必要欄位（如 Provenance 與 Review Status 等關鍵屬性），並加上靜態型態標註。

## 2. 自動化 Schema 編譯器開發

- [x] 2.1 確認專案現有的 Python 依賴狀況（如 pytest 等），並評估是否需要安裝第三方 Schema 生成/驗證庫（如 `pydantic` 或 `jsonschema`）。**若需要新增依賴，必須先向使用者提出請求。**
- [x] 2.2 在 `scripts/compile_schemas.py` 實作動態編譯邏輯，將 Python Dataclasses 動態翻譯為符合標準的 JSON Schema。
- [x] 2.3 執行編譯指令碼，將 6 個 schema 導出至 `schemas/*.schema.json`。

## 3. 實例檔案建立 (Examples)

- [x] 3.1 在 `schemas/examples/` 底下為 6 個核心合規對象分別建立有效的 YAML/JSON 實例檔案，展現實際的資料結構。
- [x] 3.2 建立故意缺失必要欄位（如缺失 `source_document_id` 或 `source_clause_ids`）的無效實例檔，用於負向測試。

## 4. 自動化測試與校驗 (TDD Workflow)

- [x] 4.1 在 `tests/test_schemas.py` 中實作單元測試，載入生成的 JSON Schema，並校驗 `schemas/examples/` 下的所有有效實例。
- [x] 4.2 在單元測試中驗證負向測試，確保缺失必要欄位時校驗能精確攔截並拋出錯誤。
- [x] 4.3 執行 pytest 單元測試，確保測試 100% 通過。

## 5. OpenSpec 驗證與準備封存

- [ ] 5.1 執行 `openspec validate implement-compliance-data-contracts --strict --no-interactive`，驗證本變更的合規性與結構完整性。
- [ ] 5.2 撰寫 Walkthrough 說明文件，準備向使用者展示 Phase 1 的實作成果，並等待最後審查。
