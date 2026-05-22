# Task Checklist: Real Regulatory PDF Ingest & LLM Extraction Pipeline

本文件為 **Inflow Ingestion Pipeline (法規導入管線)** 實作進度的追蹤清單，將作為 OpenSpec Parser 自動追蹤與勾選的依據。

---

## 1. Environment & Dependency Setup
- [ ] 1.1 於 `requirements.txt` 中引入 `pypdf>=4.0.0` 套件，並更新虛擬環境。
- [ ] 1.2 設計並建立 `src/extraction/llm_client.py` 以封裝對大模型 API 的連線，包含對 `MockLLMClient` 的抽象層支援。

## 2. Ingestion Core Development (Backend)
- [ ] 2.1 實作 `src/ingestion/pdf_parser.py` 的 `PDFTextParser`，完成文字提取、分頁字元清洗、多餘頁尾與重複頁首的過濾。
- [ ] 2.2 實作 `src/extraction/llm_extractor.py` 的智能段落切分功能，使用 LLM 動態提取 `Clause` 節點樹狀階層與 citations。
- [ ] 2.3 實作強型別合規義務抽取功能，使用 LLM Structured Outputs (JSON Schema Mode) 將 Clause 條文點石成金抽取為 Pydantic `Obligation` 欄位。
- [ ] 2.4 將 Ingestion 的輸出串接回 `RegulatoryGraph` 的記憶體圖譜結構中，確保新生產的節點與定義邊（如 `defines` 與 `references_clause`）能正確插入。

## 3. FastAPI Async Ingestion Endpoints (API)
- [ ] 3.1 於 `src/api/v1/endpoints.py` 中新增 `POST /api/v1/ingest/pdf` 異步背景上傳 API，處理 `Multipart/Form-Data` 檔案上傳。
- [ ] 3.2 實作非同步背景任務 (FastAPI `BackgroundTasks`) 管理，維護任務進度狀態（如 `pending`, `parsing_pdf`, `extracting_clauses`, `extracting_obligations`, `completed`, `failed`）。
- [ ] 3.3 新增任務狀態輪詢 API：`GET /api/v1/ingest/task/{task_id}`，回傳進度與執行日誌。

## 4. Frontend Ingestion Workbench & UI Integration (Frontend)
- [ ] 4.1 新增 React Ingestion 控制面板 `frontend/src/components/IngestionConsole.tsx`，支持 Drag & Drop PDF 上傳、元數據輸入與輪詢日誌動態滾動。
- [ ] 4.2 於 `frontend/src/App.tsx` 中整合 Ingestion 控制面板為新分頁卡片，並確保在導入成功時，能重新向 `/api/v1/graph` 發起請求以動態追加載入力導向關係圖。
- [ ] 4.3 調整前端 D3 圖譜，在點擊新導入的節點時，右側條款級溯源卡片能即時精準展示該節點的所有 Metadata 載荷與引用的原始條文。

## 5. Verification & Automated Testing
- [ ] 5.1 撰寫 `tests/test_pdf_parser.py` 測試，驗證 mock PDF 文字提取正確性與清洗效果。
- [ ] 5.2 撰寫 `tests/test_llm_extractor.py` 測試，使用 Mock 數據對 LLM 結構化輸出進行強型別校驗，確保符合 `Clause` 與 `Obligation` 契約。
- [ ] 5.3 執行整合測試，執行 `openspec validate inflow-ingestion-pipeline --strict --no-interactive` 校驗變更規格為 valid。
