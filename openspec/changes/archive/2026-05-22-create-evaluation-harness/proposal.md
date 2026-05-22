# Proposal - Phase 9: Evaluation Harness

## 動機 (Why)

CDD-GraphWiki 的核心理念是建立一個比普通基於向量檢索的 RAG Chatbot 更可靠、可審計的「合規知識編譯與推理系統」。為了解密並量化證明我們基於強型別資料合約、法規圖譜、決策織入與條款級雙向溯源的設計優勢，我們需要建立一個專屬的 **評估框架 (Evaluation Harness)**。

該評估框架必須具備 retrieval tests、obligation extraction tests、conflict detection tests、checklist correctness tests 與 citation faithfulness checks，並支援將系統與普通的向量 RAG Chatbot 基準線 (Vector-RAG Baseline) 進行量化對比。同時，它應具備「解耦診斷」能力，將每次決策失敗精確歸因為 Retrieval、Extraction、Graph Modeling、Conflict Handling 或 Final Reasoning 的哪一個環節，完全告別傳統 LLM 系統中「黑盒子式」的調優困局。

## 變更範圍 (What Changes)

本變更旨在引入一套完整的合規評估與診斷引擎，包含以下範圍：
1. **強型別評估資料合約**：擴充資料合約模型，新增支援評估指標 (`EvaluationMetrics`)、解耦診斷報告 (`DiagnosticReport`) 與對比報告 (`ComparisonReport`)。
2. **評估測試核心**：實作 `EvaluationHarness` 引擎，負責載入金標黃金標準數據並針對檢索、義務提取、衝突檢測、檢核表正確性及引用忠實度（防止幻覺）等核心維度進行全自動量化評估。
3. **基準線比較模組**：實作一個典型的普通向量檢索 RAG 基準線模擬器 (`VectorRAGBaseline`)，提供對照組進行基準線對比評估。
4. **解耦式錯誤歸因診斷器**：當推理結果與金標不一致時，自動執行錯誤決策樹，精確歸咎錯誤至特定模組。
5. **整合測試與驗證**：撰寫評估框架的單元測試，確保評估結果與對比報告之準確性。

## 系統能力 (Capabilities)

本變更將為系統注入以下新能力：
* **Multi-dimensional Evaluation (多維度合規評估)**：能針對 Ingestion 檢索、義務提取、衝突識別、檢核表決策與引用忠實性自動輸出 Recall、Precision、Accuracy 等多維指標。
* **Decoupled Diagnostics (解耦式錯誤診斷歸因)**：為每一次不一致的決策自動分析並定位錯誤根源，給予開發者清晰的合規修復方向。
* **Baseline Benchmarking (基準線對比分析)**：支持一鍵執行與普通 Vector-RAG chatbot 的指標對比，導出對比報告。

## 影響範圍 (Impact)

* **程式庫結構**：將在 `src/` 下新增 `src/evaluation/` 模組，並在 `tests/` 下新增 `test_evaluation.py`。
* **現有核心**：對現有的 Ingestion、Extraction、Graph 與 Decision 核心邏輯無破壞性變更，本階段純屬新增評估設施與基準對照，確保系統的高穩定性。
