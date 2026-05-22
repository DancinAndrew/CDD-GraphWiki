# 技術設計方案：合規官工作台全棧 Dashboard (create-compliance-dashboard)

本設計方案遵循 [ADR-0004](file:///Users/andrew-ideaslab/Documents/CDD-GraphWiki/docs/adr/0004-schema-representation-and-python-dataclass-strategy.md) 的混合元模型策略與強型別合約設計，並嚴格落實 Everything Claude Code (ECC) 的最小化依賴與條款級溯源規範。

---

## 1. 系統架構 (System Architecture)

採用 **FastAPI (後端) + Vite + React (前端)** 的前後端分離架構，保障 Python 推理邏輯的優勢與前端現代 UI 的靈活互動：

```mermaid
graph TD
    subgraph Frontend (React SPA in Browser)
        Dashboard[合規 Dashboard 總覽] --> CaseBoard[人工審批工作台]
        Dashboard --> GraphPage[D3 互動式法規圖譜]
        Dashboard --> AuditLogPage[防篡改日誌時間線與校驗]
    end

    subgraph Backend (FastAPI in Python)
        API[FastAPI 路由器] --> Engine[CDDChecklistEngine]
        API --> AuditMgr[ReviewCaseManager]
        API --> GraphBld[GraphBuilder]
        API --> AuditLgr[AuditLogger]
    end

    subgraph Data Store (Local Filesystem)
        Gold[data/gold YAMLs] --> Engine
        AuditLgr --> LogsJSON[data/processed/audit_log.json]
    end

    CaseBoard -- "POST /api/v1/cases/:id/review" --> API
    GraphPage -- "GET /api/v1/graph" --> API
    AuditLogPage -- "GET /api/v1/audit/verify" --> API
```

---

## 2. 後端 API 設計 (Backend API Design)

為了遵循系統合規技能與 RESTful 規範，API 節點命名全部使用小寫與 `kebab-case`：

### 2.1 客戶與決策推理 (Customer & Reasoning)
* **`GET /api/v1/customers`**
  - **描述**：獲取所有客戶畫像情境。
  - **回應**：`List[CustomerContext]`

* **`GET /api/v1/customers/{customer_id}/checklist`**
  - **描述**：獲取或實時生成該客戶的 CDD Checklist 推理結果（含溯源 Citation）。
  - **回應**：`CDDChecklist`

### 2.2 人機協同審核 (Human-in-the-Loop)
* **`GET /api/v1/cases`**
  - **描述**：獲取所有人工審查案件列表（支持分頁與狀態過濾 `pending_review`）。
  - **回應**：`List[ReviewCase]`

* **`POST /api/v1/cases/{case_id}/review`**
  - **描述**：合規官審核案件並覆寫決策。
  - **請求 Payload**：
    ```json
    {
      "approval_status": "approved",
      "reviewer_decision": "enhanced_due_diligence",
      "notes": "合規官 Alice 已確認高風險關聯 UBO。",
      "reviewer_id": "Compliance_Officer_Alice"
    }
    ```
  - **回應**：`ReviewCase`（已更新狀態，且對應的 Checklist 已在後端重置其 `human_review_required`）

### 2.3 知識圖譜導出 (Knowledge Graph)
* **`GET /api/v1/graph`**
  - **描述**：獲取可用於 D3.js 力導向圖渲染的點邊 JSON。
  - **回應**：
    ```json
    {
      "nodes": [
        { "id": "mas626_cdd_001", "type": "Clause", "label": "MAS 626 Clause...", "properties": {} }
      ],
      "links": [
        { "source": "mas626_cdd_001", "target": "obligation_01", "type": "derived_from", "label": "Derived From" }
      ]
    }
    ```

### 2.4 審計日誌與防篡改自我檢驗 (Audit Verification)
* **`GET /api/v1/audit/logs`**
  - **描述**：獲取完整的防篡改審計鏈日誌時間線。
  - **回應**：`List[AuditLogEntry]`

* **`GET /api/v1/audit/verify`**
  - **描述**：執行日誌鏈的完整性驗證。
  - **回應**：
    ```json
    {
      "is_intact": true,
      "total_entries": 12,
      "error_message": null,
      "tampered_index": -1
    }
    ```

---

## 3. 前端 UI 設計 (Frontend UI Design)

設計秉持「暗黑磨砂玻璃美學 (Dark Glassmorphic UI)」以 WOW 使用者：
* **色彩與字體**：
  - 主色調：暗黑背景（`#0a0f1d`）搭配霓虹發光元件（紫色 `#8b5cf6`、藍色 `#3b82f6` 與翠綠色 `#10b981`）。
  - 字體：使用 `Outfit` 或 `Inter` 提供清爽、高級的現代無襯線排版。
* **背景特效**：
  - 使用 CSS `backdrop-filter: blur(16px)`。
  - 精緻的邊框漸變發光。
* **互動體驗**：
  - **合規工作台 (Audit Inbox)**：以卡片形式展示待審理案件。按鈕帶有細微 Hover 發光縮放。
  - **D3.js 力導向知識圖譜**：
    - 全螢幕 React D3 元件，支持 Zoom / Pan。
    - 滑鼠 Hover 節點時，顯示精緻浮動 Tooltip（包含法規 Clause 文字與 Citations）。
    - 點選客戶節點時，高亮其合規決策鏈與溯源路徑（Active Path）。
  - **審計驗證儀表板**：
    - 展示一具霓虹綠色發光的「Integrity Guard」盾牌。
    - 點擊「一鍵校驗系統誠信度」，盾牌發出呼吸發光動畫，並在完成 SHA-256 完整性校驗後顯示綠色安全提示。

---

## 4. 預計變更的檔案列表 (Expected File Changes)

* **後端 (Python FastAPI)**:
  - `[NEW] src/api/main.py`: FastAPI 主要路由與 API 接口實作。
  - `[NEW] src/api/dependencies.py`: 獲取後端單例 Service（決策引擎、審計管理器、日誌器）的依賴注入。
  - `[MODIFY] requirements.txt`: 加入 `fastapi>=0.110.0` 與 `uvicorn>=0.28.0`。
* **前端 (Vite + React)**:
  - `[NEW] frontend/package.json`: 前端 NPM 依賴包配置。
  - `[NEW] frontend/index.html`: Web 入口。
  - `[NEW] frontend/src/main.tsx`: React 主要掛載。
  - `[NEW] frontend/src/App.tsx`: 主頁面佈局與路由。
  - `[NEW] frontend/src/components/Sidebar.tsx`: 側導航欄。
  - `[NEW] frontend/src/components/TamperShield.tsx`: 防篡改盾牌校驗元件。
  - `[NEW] frontend/src/components/InteractiveGraph.tsx`: D3.js 法規圖譜渲染元件。
  - `[NEW] frontend/src/pages/DashboardHome.tsx`: 合規儀表板首頁。
  - `[NEW] frontend/src/pages/ReviewQueue.tsx`: 人工審批工作台。
  - `[NEW] frontend/src/pages/AuditTimeline.tsx`: 審計日誌軌跡時間線。
  - `[NEW] frontend/src/index.css`: 暗黑磨砂玻璃美學的主題樣式。

---

## 5. 測試策略 (Test Strategy)

* **後端 API 測試**：
  - 在 `tests/` 下新增 `test_api.py`，使用 FastAPI 的 `TestClient` 對各個 API 節點進行全量單元與集成測試。
  - 確保當調用 `POST /api/v1/cases/{case_id}/review` 時，關聯的 Checklist 與日誌確實被正確寫入且防篡改鏈校驗接口 `GET /api/v1/audit/verify` 依然保持 Valid。
* **前端驗證**：
  - 自動化檢查 Vite 的打包編譯狀態 (`npm run build`)，確保 TypeScript 零編譯錯誤。
