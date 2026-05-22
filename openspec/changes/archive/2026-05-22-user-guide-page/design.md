# 系統使用教學手冊頁面設計方案 (User Guide Page Design Document)

## 1. 關聯架構決策與設計原則 (Architecture Decisions & Design Principles)
本設計遵循以下 CDD-GraphWiki 專案的頂層設計哲學：
- **防範通用 RAG 化 (Anti-Generic-RAG)**：手冊中應特別向使用者強調並詳述本系統的「法規編譯與推理」本質，展示系統如何將合規條款轉換為圖譜與可推理對象，而非僅僅是「上傳 PDF 與機器人聊天」的簡單 RAG，幫助合規官理解編譯型合規的先進之處。
- **條款級溯源 (Clause-level Provenance)**：在「案件審查隊列」與「法規自主導入」介紹中，重點展示系統如何將每一項合規 Checklist 項目精確追溯至 FATF Recommendation 10、MAS Notice 626 等條款的具體編號。
- **極致暗色霓虹美學 (Rich Aesthetics)**：手冊頁面必須完全對齊專案的 Vanilla CSS 變數，使用磨砂玻璃面板（`backdropFilter: 'blur(20px)'`）、霓虹青色（`var(--primary)`）細線條、精緻的漸變背景、以及流暢的展開動畫。
- **組件最小依賴 (Minimal Dependencies)**：`UserGuide` 組件完全使用 React 原生狀態（`useState`）實現交互（如 Accordion 切換），圖標使用已引入的 `lucide-react`，不額外安裝第三方富文本或 UI 框架。

## 2. 深度面試對齊之核心決策設計 (/grill-me 共識)
本變更已於 2026-05-22 與使用者達成 100% 共識，並正式歸檔如下：
1. **手冊版面互動設計**：完全採用**方案 A（高級暗色霓虹磨砂玻璃 Accordion 摺疊卡片）**。透過 React 的原生狀態管理每個模組卡片的展開與收合，並附帶優雅的過渡與霓虹青色發光邊框，確保在視覺上展現極致奢華的動態效果。
2. **技術簡述與 Mermaid 架構圖**：手冊內建完整的 Mermaid 數據流流程圖，生動展示「PDF 拖曳導入 -> Llama 3.3 樹狀分片 -> DeepSeek V4 Pro 雙層結構化抽取與條款級溯源 -> Neo4j 圖譜編譯與 Pydantic 人工確認 -> 防篡改日誌鏈」的編譯型合規核心運作機制。
3. **導航按鈕配置**：選單項目 ID 命名為 `guide`，顯示名稱為「系統使用手冊」，使用 `BookOpen` 圖標（來自 `lucide-react`），並精確安插在左側導航選單中「法規自主導入」的下方。

## 3. 預計變更的檔案列表 (Files to Change)
- **`[NEW]` [UserGuide.tsx](file:///Users/andrew-ideaslab/Documents/CDD-GraphWiki/frontend/src/components/UserGuide.tsx)**：
  - 新增系統手冊核心組件。
  - 採用高級磨砂玻璃外觀與細微的邊框霓虹漸變。
  - 包含系統五大分頁的極致中文介紹，並畫出 Mermaid 流程圖。
- **`[MODIFY]` [Sidebar.tsx](file:///Users/andrew-ideaslab/Documents/CDD-GraphWiki/frontend/src/components/Sidebar.tsx)**：
  - 引入 `BookOpen` 圖標。
  - 在 `menuItems` 中新增 `guide` 頁面按鈕，並對齊點擊態及選中樣式。
- **`[MODIFY]` [App.tsx](file:///Users/andrew-ideaslab/Documents/CDD-GraphWiki/frontend/src/App.tsx)**：
  - 引入 `UserGuide` 組件。
  - 在 `renderContent` 路由分發中，新增 `case 'guide'`，當選中此頁面時渲染該組件。

## 4. 技術實作細節與 UI 美學設計 (Implementation Details)
- **手冊內容矩陣（繁體中文精確技術對照）**：
  1. **工作台總覽 (Dashboard Home)**：
     - **功能簡介**：全局合規概覽、大盤統計，以及當前防篡改日誌鏈的健康狀態徽章。
     - **使用指引**：檢視目前待審查案件與防篡改警報，點擊特定圖表以快速下鑽。
     - **底層技術**：FastAPI 異步後端輪詢，結合數據庫統計接口提供即時動態反饋。
  2. **案件審查隊列 (Review Queue)**：
     - **功能簡介**：將系統自動識別的 Obligation（合規義務項目）呈現給合規官進行最終「確認」或「否決」。
     - **使用指引**：在此頁面逐項審查 AI 抽取的合規項目，查看其對應之法規條款，做出合規決策。
     - **底層技術**：RESTful API 白名單強型別校驗（Pydantic），並設計了人工審查（Human-in-the-Loop）接口，確保合規判定邊界的安全。
  3. **防篡改稽核 (Audit Timeline)**：
     - **功能簡介**：合規日誌的密碼學防篡改驗證，展示完整的稽核時間線。
     - **使用指引**：點擊「驗證日誌鏈」按鈕，系統會啟動密碼學自檢，如有任何篡改會發出紅色霓虹視覺警報。
     - **底層技術**：Python 密碼學哈希鏈（SHA-256 哈希鏈），每條日誌包含前一條的雜湊值，提供不可篡改與可追溯性。
  4. **法規可視化圖譜 (Regulatory Graph)**：
     - **功能簡介**：交互式合規實體關係圖譜，視覺化展示法規條款、內部政策與實體間的鏈結。
     - **使用指引**：可點擊節點展開關係，使用搜尋過濾特定條款，拖曳節點進行力導向圖交互。
     - **底層技術**：Neo4j 圖資料庫（NoSQL 屬性圖模型）、Cypher 查詢語言優化、D3.js 力導向渲染與 React 包裝。
  5. **法規自主導入 (Ingestion Console)**：
     - **功能簡介**：拖曳導入 PDF 法規文件，自動編譯為圖譜實體與條款。
     - **使用指引**：拖放法規 PDF（如 MAS 626），在右側的霓虹終端視窗中實時觀看 AI 處理日誌，完成後一鍵編譯進圖譜。
     - **底層技術**：PyPDF 跨行拼寫平滑重組、NVIDIA NIM 平台大語言模型（Llama 3.3 做樹狀切片，DeepSeek V4 Pro 進行高嚴謹雙層結構化抽取），完美實現條款級溯源（FATF Rec 10, MAS 626）。

## 5. 測試與驗證策略 (Testing Strategy)
- **前端編譯驗證**：在前端目錄下執行 `npm run build`，確保無語法、型別或導入錯誤。
- **功能性測試**：
  - 啟動前端開發伺服器，手動點擊左側「系統使用手冊」按鈕，確認是否能正確載入手冊頁面。
  - 測試手冊頁面的互動式 Accordion 摺疊面板，確認展開/收合時動畫與文字無重疊。
  - 確認選中狀態在側邊欄上有正確的霓虹左邊框（`borderLeft` 樣式）與青色發光效果。
- **自動化 OpenSpec 驗證**：
  - 執行 `openspec validate user-guide-page --strict --no-interactive`，確保規格檔案 100% 通過。
