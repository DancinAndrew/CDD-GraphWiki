# 變更提案：合規官工作台全棧 Dashboard (create-compliance-dashboard)

本提案旨在為 CDD-GraphWiki 專案開發一個產品級、高美學質感的合規官工作台 (Compliance Dashboard)。將合規推理決策鏈、待審核案件處理、以及鏈式防篡改日誌稽核功能，完美整合成一個具備現代感、暗黑磨砂玻璃視覺風格的全棧 Web 應用程式。

## 1. 動機與背景 (Motivation & Background)
在此之前，本系統的合規推理與決策軌跡主要是透過本地 Python 腳本 (`demo.py`) 執行，並產出靜態的 HTML 圖譜與審計報告。
為了將其轉化為真正產品級的合規系統，我們需要提供一個**動態、即時且可交互**的全棧工作台。這能讓合規人員 (Compliance Officers) 和審計人員 (Auditors) 能夠：
1. 實時查看所有待審查 (Pending Review) 的客戶合規案件。
2. 進行人機協同的決策覆寫操作，並實時觀測決策結果與 Checklist 狀態重置。
3. 交互式地穿透法規知識圖譜，溯源每一個 CDD 要求背後的法規條款。
4. 一鍵發起審計鏈的完整性驗證，提供防篡改的安全信任感。

---

## 2. 變更範圍 (Scope of Changes)
本變更是全棧性的，涵蓋後端 API 構建與前端 Single Page Application (SPA) 開發：
* **後端 (Python FastAPI)**：
  - 構建 `src/api/` 目錄，提供合規推理、案件審查、圖譜導出與日誌完整性驗證的核心 REST APIs。
  - 引入 `fastapi` 與 `uvicorn` 作為輕量 Web 框架。
* **前端 (Vite + React + TypeScript + Vanilla CSS)**：
  - 於根目錄下建立 `frontend/` 目錄，採用 Vite 初始化 React TypeScript 專案。
  - 使用純 CSS 打造暗黑磨砂玻璃美學 (Dark Glassmorphism) 設計，包含流體發光背景與現代微動畫。
  - 使用 D3.js (或 React 封裝的 D3 庫) 實作交互式力導向法規知識圖譜。
* **系統集成與一鍵運行**：
  - 提供整合的啟動配置，讓使用者能夠簡單一鍵在本地拉起全棧服務。

---

## 3. 系統能力 (Capabilities)
本變更將為 CDD-GraphWiki 注入以下能力 (Capabilities)：
* **`compliance-dashboard`**：
  - 提供即時合規總覽、人機協同審核面板、D3.js 互動式法規圖譜決策鏈、以及鏈式防篡改日誌的時間線展示與實時自我校驗。

---

## 4. 影響範圍 (Impact)
* **資料流向**：前端 SPA 將透過 HTTP REST API 向 Python 後端 Fetch 數據，決策引擎與審計日誌仍將嚴格遵循 Phase 10 的強型別合約寫入本地檔案，維持條款級溯源與 SHA-256 鏈式雜湊安全性。
* **依賴變化**：
  - 後端新增 `fastapi`, `uvicorn` 依賴。
  - 前端引入 `react`, `react-dom`, `d3`, `lucide-react`（圖標庫）等輕量依賴。
