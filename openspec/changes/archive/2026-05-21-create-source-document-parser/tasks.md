## 1. Directory and Environment Setup

- [x] 1.1 建立原始法規存放目錄 `data/sources/` 與解析後輸出目錄 `data/processed/`
- [x] 1.2 在 `data/sources/` 下編寫真實的法規源文件：
    - `fatf_rec10.md`（FATF Rec 10 客戶盡職調查）
    - `mas_notice_626.md`（新加坡 MAS Notice 626 CDD/EDD 條款片段）
    - `mock_internal_policy.md`（模擬內部銀行合規政策條款）

## 2. Implement Semantic Parser and Stable ID Generator

- [x] 2.1 建立 `src/ingestion/parser.py` 解析器腳本，並定義基本 CLI 參數與執行結構
- [x] 2.2 實作 Markdown 層級標題與列表樹狀切分邏輯，動態追蹤 `parent_clause_id`
- [x] 2.3 實作基於路徑的 `clause_id` 穩定生成演算法，消除 rerun 漂移風險
- [x] 2.4 實作 Pydantic `Clause` 與 `SourceDocument` 物件的序列化與導出邏輯（輸出至 `data/processed/` 檔案）

## 3. Implement Automated Tests and Verification

- [x] 3.1 建立單元測試 `tests/test_source_parser.py`
- [x] 3.2 在測試中驗證解析產出的 `Clause` 與 `SourceDocument` 100% 符合 Pydantic 資料合約
- [x] 3.3 在測試中驗證層級樹狀參照完整性（每個 `parent_clause_id` 指向的實體必須在全局存在，且不可有懸空引用）
- [x] 3.4 在測試中驗證 Parser 運行的冪等性與 ID 穩定性（rerun 相同內容產生的 ID 必須 100% 恆定）

## 4. Run Validation, Archiving and Git Operations

- [ ] 4.1 執行本地 `openspec validate create-source-document-parser --strict` 校驗
- [x] 4.2 執行 `pytest tests/test_source_parser.py` 以 100% 通過所有測試
- [ ] 4.3 執行 `openspec archive create-source-document-parser --yes` 進行變更封存與 baseline 合併
- [ ] 4.4 將所有變更透過 Git 提交並 Push 至遠端 GitHub 倉庫
