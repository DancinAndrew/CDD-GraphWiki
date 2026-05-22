# 系統使用教學手冊頁面新增任務清單 (User Guide Page Tasks)

## 1. Design & Plan Alignment
- [x] 1.1 建立並備齊 OpenSpec 變更計畫的所有文件。
- [x] 1.2 主動建議使用者觸發 `/grill-me` 深度面試，並就設計細節與使用者達成共識。
- [x] 1.3 將 `/grill-me` 共識決策歸檔更新至 `design.md`。
- [x] 1.4 獲得使用者明確的「審查批准」或指示「開始實作」以解除實作阻斷。

## 2. Frontend Implementation
- [x] 2.1 建立全新的 React 使用手冊組件 `frontend/src/components/UserGuide.tsx`，使用原生 React 狀態實現互動式 Accordion 摺疊面板，對齊暗色霓虹美學，用繁體中文撰寫所有介紹。
- [x] 2.2 修改 `frontend/src/components/Sidebar.tsx`，引入 `BookOpen` 圖標，並在導航選單的「法規自主導入」下方新增手冊選項。
- [x] 2.3 修改 `frontend/src/App.tsx`，引入 `UserGuide` 組件，並在主路由分發 `renderContent` 中新增 `guide` 分支。

## 3. Verification & CI Check
- [x] 3.1 啟動並執行後端 `pytest`，確保系統核心單元測試（Inflow Ingestion Pipeline 等）100% 綠燈通過。
- [x] 3.2 驗證前端編譯是否通過，且沒有任何語法、型別或 style 衝突警告。
- [x] 3.3 執行 `openspec validate user-guide-page --strict --no-interactive`，驗證 OpenSpec change 計畫之正確性。

## 4. Archive & Commit
- [ ] 4.1 執行 `openspec archive user-guide-page --yes` 將變更合併至 Baseline 並封存。
- [ ] 4.2 撰寫 Conventional Commit 格式的 Git commit 訊息並提交代碼。
- [ ] 4.3 更新並撰寫 `walkthrough.md` 以呈現變更成果。
