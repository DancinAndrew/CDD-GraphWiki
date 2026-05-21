# Proposal: Create Obligation Extractor Prototype (建立合規義務抽取原型)

## 1. 動機 (Why)
在 Phase 3 中，我們已成功實作了法規源 Ingestion Pipeline，將原始法規 Markdown 文獻精準且穩定地切分為 42 個條款 (`Clause`)。然而，這些條款仍是自然的法律語言，機器無法直接對其進行合規風險比對或決策推理。

為了實現 Spec 中規定的 CDD 自動化檢核表推理，我們必須建立一個將非結構化條款 (`Clause`) 編譯為結構化、可執行的合規義務 (`Obligation`) 的抽取器原型 (`Obligation Extractor Prototype`)。此原型將作為知識編譯管線 (Knowledge Compilation Pipeline) 的核心，為後續的法規圖譜 (Phase 6) 與決策引擎 (Phase 8) 提供強型別、可追溯的合規規則。

## 2. 變更範圍 (What Changes)
- **新增抽取引擎**：建立 `src/extraction/extractor.py`，實作規則驅動與關鍵特徵比對的混合同步抽取管線 (`ObligationExtractionPipeline`)。
- **支援信心度與人工審查**：對於語意特徵不明顯的條款進行失敗原因分類，並自動歸入低信心度人工審查隊列 (`Low-Confidence Human Review Queue`)。
- **與黃金數據集評估比對**：建立評估評測模組，將自動抽取的 Obligations 與手動標記的黃金數據集 (`data/gold/obligations.yaml`) 進行欄位級精準度對比，並輸出比對結果報告。
- **輸出數據集**：將自動抽取的 obligations 序列化輸出至 `data/processed/obligations.yaml`。
- **自動化測試套件**：建立單元測試 `tests/test_obligation_extractor.py`，驗證合約校驗、評估指標與錯誤分類正確性。

## 3. 系統能力 (Capabilities)
- **結構化合規義務抽取**：從條款中提取出 `actor`、`action`、`object`、`conditions`、`exceptions`、`required_evidence` 與 `review_flags`。
- **錯誤分類與容錯 (Failure Classification)**：區分「非義務條款 (Non-Obligation Clause)」、「無明確主體/動作 (Missing Actor/Action)」、「低置信度 (Low Confidence)」等失敗類型。
- **金標對齊度評估 (Gold Dataset Evaluation)**：自動計算 Precision、Recall 和 F1-Score 指標。

## 4. 影響範圍 (Impact)
- **無外部依賴引入**：維持極簡原則，100% 基於 Python 標準庫與專案已有的 Pydantic/PyYAML 套件。
- **保障數據流完整性**：輸出檔案 `data/processed/obligations.yaml` 將作為下一階段法規圖譜 (Phase 6) 的權威輸入。
- **不破壞現有功能**：保證現有 21 個測試全部繼續通過。
