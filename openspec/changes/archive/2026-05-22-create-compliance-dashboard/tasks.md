# 實作任務清單：合規官工作台全棧 Dashboard (create-compliance-dashboard)

本任務清單詳細定義了本階段所有開發的具體 Checkbox 任務。

---

## 1. Backend API Implementation
- [x] 1.1 在 `requirements.txt` 中添加 `fastapi` 與 `uvicorn` 等必要後端依賴套件。
- [x] 1.2 創建後端依賴模組 `src/api/dependencies.py`，提供單例之 `CDDChecklistEngine`、`ReviewCaseManager` 與 `AuditLogger`。
- [x] 1.3 創建 FastAPI 主要服務程序 `src/api/main.py`，提供客戶數據、Checklist 生成、人工審核、D3 圖譜數據導出、防篡改日誌、以及鏈式完整性驗證的 APIs。
- [x] 1.4 對 API 節點進行防禦性校驗，確保所有輸入數據皆經由 Pydantic 強型別合約過濾，以預防安全漏洞。

## 2. Frontend Project Initialization
- [x] 2.1 在 `frontend/` 目錄下建立 Vite + React + TypeScript 前端專案。
- [x] 2.2 配置前端 `frontend/package.json` 中的依賴（包括 React、D3、Lucide React 與本地開發伺服器端口配置）。
- [x] 2.3 創建前端主要樣式 `frontend/src/index.css`，設計並實現符合 HSL 漸變流體背景、暗黑磨砂玻璃的現代設計語言。
- [x] 2.4 創建前端全局佈局與導航架構，包括 `frontend/src/App.tsx` 與側導航欄 `frontend/src/components/Sidebar.tsx`。

## 3. Dashboard Core Components
- [x] 3.1 實現首頁 `frontend/src/pages/DashboardHome.tsx`，展示合規指標卡片與全局統計（如待審核件數、日誌鏈健全狀態）。
- [x] 3.2 實現人工審查工作台 `frontend/src/pages/ReviewQueue.tsx`，以卡片流呈現 `pending_review` 案件，並提供審批覆寫表單與提交。
- [x] 3.3 實現防篡改日誌稽核 Timeline 頁面 `frontend/src/pages/AuditTimeline.tsx`，包含盾牌動態防篡改校驗元件 `frontend/src/components/TamperShield.tsx`。
- [x] 3.4 實現 D3.js 互動式法規圖譜 `frontend/src/components/InteractiveGraph.tsx`，支持 Zoom、Drag 節點，懸停 Tooltip 與高亮決策鏈。

## 4. Verification & Testing
- [x] 4.1 撰寫後端 API 單元測試 `tests/test_api.py`，使用 `FastAPI TestClient` 測試所有 API 節點的正確性與邊界錯誤防禦。
- [ ] 4.2 執行前端打包編譯測試 `npm run build`，確保 TypeScript 零錯誤且靜態資源成功產出。
- [ ] 4.3 執行 OpenSpec 變更驗證 `openspec validate create-compliance-dashboard --strict --no-interactive` 確保規格一致。
