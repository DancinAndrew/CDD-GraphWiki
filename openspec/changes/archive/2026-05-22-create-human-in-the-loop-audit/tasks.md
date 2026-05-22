# Phase 10: Human-in-the-Loop & Audit Logging 任務清單

## 1. Schema and Contract Extensions
- [ ] 1.1 在 `src/contracts/models.py` 中新增 `ReviewCase` 強型別資料模型
- [ ] 1.2 在 `src/contracts/models.py` 中新增 `AuditLogEntry` 強型別資料模型
- [ ] 1.3 在 `src/contracts/__init__.py` 中導出這些新模型
- [ ] 1.4 執行 `python scripts/compile_schemas.py` 編譯並驗證新產生的 JSON Schemas

## 2. Audit Trail Logger Implementation
- [ ] 2.1 實作 `AuditLogger` 類別，提供鏈式雜湊 (Hash Chain) 級聯寫入，保障防篡改特性
- [ ] 2.2 實作推理決策生命週期自動記錄，包含 Ingestion Hash、Graph Version 與 Rule Version

## 3. Human-in-the-Loop Case Manager
- [ ] 3.1 實作 `ReviewCaseManager` 類別，管理審查案件的生命週期
- [ ] 3.2 實作決策覆寫邏輯：當審查狀態為 `approved` 時，更新 Checklist 的決策與 human_review_required 標記，並保存審批軌跡

## 4. Compliance Audit Report Generator
- [ ] 4.1 實作 `AuditReportGenerator` 類別
- [ ] 4.2 一鍵生成包含 Citation 溯源、圖譜遍歷路徑、衝突對比與人工審查詳情的美觀審計報告 (HTML 支援磨砂玻璃暗黑風格與 PII 脫敏)

## 5. Automation Testing and Verification
- [ ] 5.1 在 `tests/test_human_in_the_loop_audit.py` 中撰寫完整的自動化單元測試，覆蓋合約、鏈式雜湊防篡改、人工覆寫與審計報告導出
- [ ] 5.2 執行本地 pytest 測試套件，確保所有單元測試 100% 成功通過
- [ ] 5.3 執行 `openspec validate create-human-in-the-loop-audit --strict --no-interactive` 校驗 OpenSpec 變更
- [ ] 5.4 執行 `openspec archive create-human-in-the-loop-audit --yes` 封存變更
- [ ] 5.5 將所有變更常規提交並推送至 GitHub 遠端倉庫
