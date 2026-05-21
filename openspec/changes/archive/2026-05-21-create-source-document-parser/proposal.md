## Why

在金融合規與客戶盡職調查 (AML/CDD) 的知識編譯系統中，法規源解析與條款切分 (Ingestion and Clause Segmentation) 是整個推理管線 (Reasoning Pipeline) 的物理起點。

傳統 RAG (檢索增強生成) 系統通常使用固定 token 長度或字元重疊的「暴力切分 (Naive Chunking)」，這會徹底破壞法規法律條文的嚴密層級關係（如「章 > 節 > 條 > 款 > 項」），導致「例外條款 (Exception)」與「適用前提 (Condition)」與主體脫節，從而在推理階段引發嚴重的幻覺與錯漏。

為了建立具備「條款級可追溯性 (Clause-level Provenance)」的合規圖譜，我們必須將原始合規文獻 (Markdown 格式) 進行結構化的**語意層級切分 (Semantic Hierarchical Segmentation)**。在解析過程中：
1. 精準保留法規的父子樹狀層級關係（透過 `parent_clause_id` 連結）。
2. 設計在 rerun 後穩定不漂移的 `clause_id` 生成機制，確保系統狀態的可重複性與合規審計的確定性。
3. 自動將解析結果導出為符合 `Clause` 與 `SourceDocument` 資料合約的結構化實體。

## What Changes

*   **引入真實法規源數據**：在 `data/sources/` 目錄下存放三份真實/模擬 Markdown 格式的原始法規與政策文件：
    *   `fatf_rec10.md`：FATF 關於客戶盡職調查的第 10 號建議書 (Customer Due Diligence) 真實條款。
    *   `mas_notice_626.md`：新加坡金融管理局 (MAS) Notice 626 關於 CDD/EDD 的真實條款片段。
    *   `mock_internal_policy.md`：模擬的內部銀行 AML/KYC 政策條款。
*   **實作 Ingestion Pipeline 解析器**：
    *   在 `src/ingestion/parser.py` 中實現一個**基於 Markdown 標題層級與編號列表的語意切分器 (Semantic Hierarchical Clause Segmenter)**。
    *   實作**穩定 ID 生成演算法**（利用文件 ID 與路徑標識符哈希，保證 rerun 後 IDs 絕不飄移）。
    *   支援將解析出的實體自動序列化為 `data/processed/clauses.yaml` 與 `data/processed/source_documents.yaml`。
*   **建立自動化驗證與測試**：
    *   在 `tests/test_source_parser.py` 中實作 Parser 單元測試。
    *   校驗切分後 Clause 物件 100% 符合 Pydantic 合約、外鍵參照完整性（每個 `parent_clause_id` 必須確實存在），以及 Parser 在重複運行時的冪等性與 ID 穩定性。

## Capabilities

### New Capabilities
- `source-document-parser`: 提供自動化讀取 Markdown 合規文獻、建立層級樹狀條款（`Clause`）並實現穩定 ID 生成的法規源解析能力。

### Modified Capabilities
<!-- 本階段沒有修改現有的 spec 需求行為 -->

## Impact

*   **對現有代碼無破壞性影響**：本變更為新增功能，完全符合 Phase 2 完成的資料合約。
*   **為後續推理打下地基**：本階段產出的結構化 `Clause` 與 `SourceDocument` 資料庫，將直接解鎖 Phase 4 (Obligation Extraction 義務抽取) 與 Phase 6 (Regulatory Graph 法規圖譜建構) 的自動化導入。
