## Context

在 Phase 1 與 Phase 2 中，我們建立並校驗了強型別 Pydantic 資料合約與高品質的人工黃金數據集。
為了實現自動化法規知識編譯，我們需要在 Phase 3 實作 Ingestion 管線，將原始法規 Markdown 文件（FATF Rec 10, MAS Notice 626, Mock Internal Policy）自動解析並切分為具備完整層級上下文、在 rerun 後穩定不漂移的 `Clause` 實體，並 100% 契合 `src/contracts/models.py` 的資料合約。

---

## Goals / Non-Goals

**Goals:**
*   在 `data/sources/` 下建立三個真實/模擬的 Markdown 原始文件，作為 Ingestion 的輸入。
*   在 `src/ingestion/parser.py` 中實作一個高度穩健的語意層級 Markdown 解析器。
*   設計並實現一個 Section-Path-Based 穩定 ID 生成機制，杜絕 counter/sequence ID 漂移問題。
*   自動產生 `data/processed/clauses.yaml` 與 `data/processed/source_documents.yaml`。
*   在 `tests/test_source_parser.py` 中實現針對 Parser 輸出合約、層級關係完整性、以及 ID 穩定性與冪等性的自動化測試。

**Non-Goals:**
*   實作自動化 LLM 義務抽取（這是 Phase 4 的工作）。
*   實作圖引擎與關係推理（這是 Phase 6 的工作）。
*   解析除了 Markdown 以外的其他格式（如 PDF/Word），本系統統一將 Markdown 作為 Ingestion 層的規範化輸入格式。

---

## Decisions

### Decision: 基於標題與列表樹狀結構的語意切分 (Semantic Hierarchical Clause Segmenter)
*   **理由**：法規條文有強烈的樹狀層級關係（章 > 節 > 條 > 款 > 項）。如果採用單純按字元數或 Token 長度切片，會將例外條款與其約束的主體條款割裂，導致模型在檢索和推理時產生幻覺。
    我們的切分器將逐行掃描 Markdown，當遇到不同數量的 `#`（標題層級）以及列表前綴（如 `(a)`, `(b)`, `(i)`, `(ii)`）時，動態構建一棵樹。每個樹節點都對應一個 `Clause` 實體，並且其 `parent_clause_id` 指向其父節點。這樣做能保證條款的完整上下文在推理時可以透過遞迴上溯輕鬆還原。
*   **替代方案**：基於 Token 長度的暴力切片（無法保留樹狀層級，不符合合規高嚴謹度要求）。

### Decision: Section-Path-Based 穩定 ID 生成演算法
*   **理由**：在自動化 Ingestion 系統中，如果使用遞增計數器（如 `clause_001`, `clause_002`），一旦法規文件在前端被插入了一小段話，後續所有條款的 ID 都會發生移位（漂移）。這會導致已經建立好的 obligations 圖譜、Wiki 頁面或 checklist 對照關係徹底失效。
    我們採用基於「文件 ID + 層級路徑 (Section Path)」生成可讀且穩定的標識符。例如：
    *   源文件：`fatf_rec10`
    *   標題層級：`Customer due diligence` -> `Paragraph 4` -> `Sub-paragraph a`
    *   ID 生成：`fatf10_cdd_p4_a`
    *   如果路徑中含有無規則的長文本，則將路徑經過清洗或取 MD5 部分哈希字串作為後綴，保證只要該條款在文獻樹中的物理位置和內容不變，其 ID 就 100% 保持恆定。
*   **替代方案**：使用 UUID 或隨機哈希（不可讀，不便調試與人工稽核）或遞增計數器（極易移位漂移）。

### Decision: 導出格式為 YAML，且支援 CLI 觸發
*   **理由**：
    *   YAML 對於多行文本（`raw_text`, `normalized_text`）的儲存與展示非常友善，且方便人類開發者審查 Parser 的切分成果。
    *   我們將在 `src/ingestion/parser.py` 中暴露一個簡單的 CLI 入口（例如 `python -m src.ingestion.parser --src data/sources/ --out data/processed/`），便於在建置、部署或 CI 中自動執行。
*   **替代方案**：直接導出成 JSON（可讀性差，難以直觀審查多行條文）。

---

## Risks / Trade-offs

*   **[Risk] Markdown 格式不規範導致解析失敗** $\to$ [Mitigation] 我們將在 `data/sources/` 下建立高度結構化且符合 Markdown 規範的真實法規文件。在 Parser 實作中，對於無法識別的行或未定義的標題，會進行妥善處理，並在 `tests/test_source_parser.py` 中加入格式異常邊界測試。
*   **[Risk] Rerun 時 ID 漂移風險** $\to$ [Mitigation] 在測試中加入「穩定性校驗」：複製一份原始 Markdown 檔案，隨機在不改變層級結構的地方增刪一些空格或內文，再次運行 Parser，驗證條款 ID 依然保持一致。
