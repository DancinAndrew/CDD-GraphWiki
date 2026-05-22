# 提案：對接 NVIDIA NIM 平台模型與多模型任務配置 (nvidia-nim-integration)

這個提案旨在將 CDD-GraphWiki 的法規導入管線 (Inflow Ingestion Pipeline) 正式接入 NVIDIA NIM 平台的大語言模型。透過在 `.env` 中安全配置憑證與環境變數，並針對不同子任務（樹狀層級切片與強型別合規義務抽取）配置最佳的模型，提升合規知識抽取的精準度與穩定性，同時保留完善的離線 Mock Fallback 機制。

## 1. 動機 (Why)

目前 CDD-GraphWiki 的法規導入模組雖然具備了 `LLMHierarchicalChunker` (智慧切片) 與 `LLMStructuredExtractor` (義務抽取) 的二階段 Pipeline，但在 API 連接上主要為 Google GenAI 且缺乏對其他高效能合規模型（例如在 NVIDIA NIM 平台上運行的 Llama 3.3 或 DeepSeek 系列等）的整合與配置。
為了在大規模、高複雜度的 AML/CDD 條約上取得最佳的結構化抽取效果，我們 need：
1. **安全憑證管理**：將使用者提供的 NVIDIA NIM API key 寫入 `.env` 環境檔案中，避免程式碼硬編碼。
2. **多任務模型適配**：不同的 LLM 在智慧切片（需要強大長文本理解）與結構化義務提取（需要高精度 Schema 遵循能力）上有不同的表現，需要實現針對不同子任務的模型動態配置。
3. **高可用性 API 連接**：在 `LLMClient` 中基於專案現有的 `httpx` 工具，對接 NVIDIA NIM 平台標準的 OpenAI-compatible 協定，實現高效的 JSON 結構化回傳，並具備優雅的錯誤重試與離線 Mock 降級機制。

## 2. 變更範圍 (What Changes)

- **環境配置**：
  - 建立或更新 `.env` 檔案，安全寫入 `NVIDIA_API_KEY`、以及兩個子任務的專屬模型配置：`NIM_CHUNKER_MODEL` 與 `NIM_EXTRACTOR_MODEL`。
  - 修改 `.gitignore` 確保 `.env` 不會被提交。
- **LLM 客戶端 (`src/extraction/llm_client.py`)**：
  - 擴展 `LLMClient`，使其能檢測並讀取 NVIDIA NIM 環境變數。
  - 當檢測到 `NVIDIA_API_KEY` 時，使用 `httpx` 直接呼叫 NVIDIA NIM 平台。
  - 支援 `generate_structured` 方法與強型別 Pydantic 結構解析（使用 NVIDIA NIM 的 JSON 模式或原生 Schema 約束）。
  - 保留對 Gemini API 的支援與 Mock Fallback 機制。
- **測試與驗證腳本 (`scripts/test_nim_connection.py`)**：
  - 建立一組獨立的測試連通性腳本，驗證 API key 與兩個 NIM 模型的呼叫是否正常（回傳正確的 JSON 格式）。
- **演示與流程實作 (`demo_ingestion_nim.py`)**：
  - 提供一個簡潔的端到端 CLI 使用流程，讓使用者能夠親自跑一次使用真實 NVIDIA NIM LLM 導入法規文件的完整二階段 Ingestion 流程並生成圖譜與 Checklist。
- **文件撰寫**：
  - 完成所有相關 OpenSpec 文件並通過驗證。

## 3. 系統能力 (Capabilities)

本提案將新增以下 OpenSpec 能力：
- **`nvidia-nim-integration`**：支援對接 NVIDIA NIM 平台，透過環境變數動態適配 `LLMHierarchicalChunker` 與 `LLMStructuredExtractor` 任務的模型，並具備 100% 的 Schema 遵循精度與 Clause-level Provenance。

## 4. 影響範圍 (Impact)

- **API 呼叫層**：`LLMClient` 將新增 NVIDIA NIM 的調用路徑，無縫替換底層 API 呼叫，而不需要修改業務邏輯層（如 `LLMHierarchicalChunker` 與 `LLMStructuredExtractor` 呼叫端代碼）。
- **架構安全性**：憑證完全隔離在 `.env`，符合 `/security-review` 的 Secrets Management 規範。
- **測試覆蓋**：新增 NIM 客戶端的單元測試，確保在 Mock 或真實 API 下均能保持介面合約一致。
