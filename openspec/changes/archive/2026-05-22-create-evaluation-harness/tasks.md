# Tasks - Phase 9: Evaluation Harness

## 1. Schema and Contract Extensions
- [ ] 1.1 在 `src/contracts/models.py` 中新增 `EvaluationMetrics` 強型別資料模型
- [ ] 1.2 在 `src/contracts/models.py` 中新增 `DiagnosticReport` 強型別錯誤歸因診斷模型
- [ ] 1.3 在 `src/contracts/models.py` 中新增 `ComparisonReport` 系統與基準線對比報告模型
- [ ] 1.4 在 `src/contracts/__init__.py` 中導出這些評估相關資料模型
- [ ] 1.5 執行 `python scripts/compile_schemas.py` 編譯並驗證新產生的 JSON Schemas

## 2. Baseline Simulator Setup
- [ ] 2.1 建立 `src/evaluation/` 目錄並新增 `__init__.py` 接口導出
- [ ] 2.2 在 `src/evaluation/baseline.py` 中實作 `VectorRAGBaseline` 類別，模擬普通的向量切片檢索 RAG 流程
- [ ] 2.3 在 Baseline 中實作提示詞推理，並讓其產生非結構化或易出錯的 Mock Checklist 決策，作為合適的對照組

## 3. Evaluation Harness Implementation
- [ ] 3.1 在 `src/evaluation/harness.py` 中實作 `EvaluationHarness` 類別
- [ ] 3.2 實作 `evaluate_retrieval` 評估檢索 Recall 與 Precision
- [ ] 3.3 實作 `evaluate_extraction` 評估義務屬性提取精確度
- [ ] 3.4 實作 `evaluate_conflict_detection` 評估政策衝突識別率
- [ ] 3.5 實作 `evaluate_checklist_correctness` 評估檢核表決策、佐證、風險標記的準確度 (Accuracy / F1)
- [ ] 3.6 實作 `check_citation_faithfulness` 引用忠實度與幻覺檢測機制，遍歷 Citation 驗證圖譜/法規庫真實性
- [ ] 3.7 在 `EvaluationHarness` 中實作對比分析並導出 Comparison Report

## 4. Decoupled Diagnostic Tree
- [ ] 4.1 在 `src/evaluation/harness.py` 中實作解耦錯誤診斷樹 `run_diagnostic_tree`
- [ ] 4.2 實作 Step-by-step 的錯誤根源自動歸因邏輯 (Retrieval, Extraction, Graph Modeling, Conflict Handling, Reasoning)

## 5. Automation Testing and Verification
- [ ] 5.1 在 `tests/test_evaluation.py` 中撰寫完整的自動化單元測試，覆蓋指標計算、幻覺引用檢測、錯誤歸因診斷與對比報告生成
- [ ] 5.2 執行本地 pytest 測試套件，確保所有單元測試 100% 成功通過
- [ ] 5.3 執行 `openspec validate create-evaluation-harness --strict --no-interactive` 校驗 OpenSpec 變更
- [ ] 5.4 執行 `openspec archive create-evaluation-harness --yes` 封存變更
- [ ] 5.5 將所有變更常規提交並推送至 GitHub 遠端倉庫
