## 1. Implement Obligation Extraction Pipeline

- [x] 1.1 建立 `src/extraction/extractor.py` 主程式與基礎 CLI 結構
- [x] 1.2 實作特徵規則與關鍵字匹配抽取演算法，精確識別 Actor、Action、Object、Conditions 與 Required Evidence
- [x] 1.3 實作低信心度失敗分類機制，分類並導出低置信度或非義務條款至人工審查 Queue 報告
- [x] 1.4 實作黃金數據集比對評測工具，載入 `data/gold/obligations.yaml` 計算 Precision、Recall 與 F1-Score 並輸出評估報告

## 2. Implement Automated Test Suite

- [x] 2.1 建立 `tests/test_obligation_extractor.py` 測試檔案
- [x] 2.2 在測試中驗證自動抽取與生成的 Obligations 100% 符合 Pydantic 與 JSON Schema 合約
- [x] 2.3 在測試中驗證失敗原因分類機制（如 NON_OBLIGATION_TEXT 等）的精確性
- [x] 2.4 在測試中驗證黃金數據集比對評估計算的指標正確性

## 3. Run Pipeline and Generate Data

- [x] 3.1 執行 `PYTHONPATH=. .venv/bin/python -m src.extraction.extractor` 處理全部 42 個條款並輸出 `data/processed/obligations.yaml`
- [x] 3.2 驗證輸出數據無懸空的 `source_clause_ids` 參考，並在 `data/processed/` 下產生人工審查 Queue 報告

## 4. OpenSpec Validation, Archiving and Git Operations

- [x] 4.1 執行本地 `openspec validate create-obligation-extractor-prototype --strict` 校驗並通過
- [x] 4.2 執行 `PYTHONPATH=. .venv/bin/pytest tests/test_obligation_extractor.py` 確保 100% 通過
- [ ] 4.3 執行 `openspec archive create-obligation-extractor-prototype --yes` 進行變更封存與 baseline 合併
- [ ] 4.4 將所有代碼與文件變更進行 Git Commit 提交並 Push 至遠端 GitHub 倉庫
