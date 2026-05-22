# inflow-ingestion-pipeline Specification

## Purpose
TBD - created by archiving change inflow-ingestion-pipeline. Update Purpose after archive.
## Requirements
### Requirement: Real-time PDF Parser and Clean Text
後端系統 **SHALL** 提供一個 PDF 文字提取器，能夠讀取上傳的二進位 PDF 檔案，提取其純文字內容，並自動去除常見的 PDF 印表雜訊（如頁碼、分頁符號與重複出現的頁首頁尾標題）。

#### Scenario: Successfully Parse Regulatory PDF to Raw Text
* **GIVEN** 一個標準格式的法規 PDF 檔案（例如 *MAS Notice 626*）被上傳至後端 API。
* **WHEN** 系統呼叫 `PDFTextParser` 進行文字提取時。
* **THEN** 系統 **SHALL** 回傳一個乾淨、連續的字串，其中所有的分頁中斷被合理平滑化，且不包含明顯的頁碼與頁尾版權宣告等噪聲文字。

---

### Requirement: LLM-powered Hierarchical Chunking
系統 **SHALL** 使用 LLM 讀取法規純文字，並智能識別出其階層結構（例如 Section、Paragraph、子項列表等），進而將法規精準分割為多個 `Clause` 節點。

#### Scenario: Generate Tree of Clauses via LLM from Text
* **GIVEN** 清洗後的法規原文與其 `SourceDocument` 元數據。
* **WHEN** 系統將文字段落與層級目錄 Prompt 發送至強推理大模型（如 Gemini 3.5 Pro）。
* **THEN** 系統 **SHALL** 解析出一個完整的樹狀 `Clause` 陣列，其中每一個 `Clause` 節點都 **MUST** 包含穩定的 `clause_id`（由文件 ID 與層級路徑雜湊/底線組合而成）、精準的 `section_ref`（例如 `Section 6 > Paragraph 6.2(a) > (i)`），以及其 `parent_clause_id`。

---

### Requirement: LLM-powered Strong Typed Obligation Extraction
對於每一個切割出來的實質法規 `Clause` 節點，系統 **SHALL** 利用 LLM 進行**強型別結構化輸出 (Structured Outputs)**，精準抽取合規義務。

#### Scenario: Extract Compliant Obligation with Multi-field Schema
* **GIVEN** 一個包含實質合規規範的 `Clause` 節點。
* **WHEN** 系統呼叫 `LLMObligationExtractor` 且配置對應的 Pydantic Schema（即符合系統定義的 `Obligation` 類別結構）時。
* **THEN** 系統 **SHALL** 強制要求 LLM 回傳合規的 JSON 資料結構，其自動映射並滿足以下約束：
  1. `obligation_id` **MUST** 為基於合意內容生成的 kebab-case 標識符。
  2. `source_clause_ids` **MUST** 包含當前來源 Clause 的 ID，以確保 clause-level 溯源可追溯性。
  3. `actor` (如 `bank`, `financial_institution`)、`action` (如 `identify_and_verify`, `perform_edd`)、`object` (如 `beneficial_owner`, `pep`) **MUST** 從法規原文語意中精準抽取。
  4. `required_evidence` **SHALL** 條列出符合法規要求所需的審計憑證與表單清單。
  5. `confidence` **MUST** 記錄大模型自身輸出的置信分數。

---

### Requirement: Asynchronous Background Ingestion API
後端 FastAPI **SHALL** 提供一個非同步上傳 PDF 檔案的端點（`/api/v1/ingest/pdf`），該端點在接收檔案後 **SHALL** 立即返回任務 ID，並在背景（Background Task）執行 Ingest 與 Extraction Pipeline，以避免 LLM 呼叫造成的 API 超時。

#### Scenario: Upload PDF and Monitor Process Progress
* **GIVEN** 合規官在前端介面上傳一份法規 PDF，並提供 Document 元數據。
* **WHEN** 前端發送 `POST /api/v1/ingest/pdf` 請求時。
* **THEN** 後端 **SHALL** 回傳 `202 Accepted` 狀態碼，並提供 `{ "task_id": "task_ingest_xxx", "status": "processing" }`。
* **AND WHEN** 背景的 Ingest 與 Extraction Pipeline 執行完畢時。
* **THEN** 後端 **SHALL** 自動將新生產的 `SourceDocument`、`Clause` 與 `Obligation` 節點與對應的邊動態追加至當前的 `RegulatoryGraph` 中，且此變更在前端重新獲取圖譜 `/api/v1/graph` 時 **MUST** 即時體現。

