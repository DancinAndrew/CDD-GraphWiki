# compliance_dashboard Specification

## Purpose
TBD - created by archiving change create-compliance-dashboard. Update Purpose after archive.
## Requirements
### Requirement: compliance_dashboard_api_contracts
後端服務 MUST 提供一組 REST APIs，用以向前端 Dashboard 傳遞符合強型別合約的數據，包含客戶情境、人工審批案件、鏈式防篡改日誌、以及可用於圖譜展示的點邊網絡結構。
* API 節點命名必須 (SHALL) 遵循 `kebab-case`（例如 `/api/v1/audit/verify`）。
* 對於所有輸入數據，API 必須 (SHALL) 採用 Pydantic 強型別合約進行白名單白盒校驗，若遇到異常輸入，必須 (SHALL) 返回標準的 422 錯誤回應以確保安全防禦性。

#### Scenario: verify_tamper_evident_logs_via_api
* **GIVEN**：後端系統已載入 5 個客戶的情境，並執行了初審推理，產生了包含 5 條 Reasoning 事件的鏈式防篡改日誌軌跡。
* **WHEN**：合規官前端點選「一鍵校驗誠信度」，觸發發送 `GET /api/v1/audit/verify` 請求。
* **THEN**：後端必須 (SHALL) 調用 `AuditLogger.verify_integrity()`，並返回一個 JSON 回應。若日誌鏈未被篡改，則 JSON 回應中的 `is_intact` 必須為 `True`，且 `tampered_index` 為 `-1`。

---

### Requirement: human_in_the_loop_approval_workflow
系統必須 (SHALL) 支持合規官在前端 Dashboard 對需要人工介入的客戶案件（如政要人物 PEP）執行審查與決策覆寫，並將覆寫後的決策寫入防篡改日誌中。
* 點擊提交時，前端 Dashboard 會向 `/api/v1/cases/{case_id}/review` 發送 POST 請求。
* 後端接收到覆寫請求後，必須 (SHALL) 將該案件關聯的 `CDDChecklist` 的 `human_review_required` 重置為 `False`，並將人工覆寫事件作為新日誌織入 SHA-256 鏈式防篡改日誌中。

#### Scenario: overwrite_pep_case_decision_via_dashboard
* **GIVEN**：客戶 `cust_individual_pep` 被機器初審判定為 `enhanced_due_diligence`，且 `human_review_required` 為 `True`，並已在後端建立案件 `rev_individual_pep`。
* **WHEN**：合規官 Alice 在前端 Dashboard 打開 `rev_individual_pep` 案件卡片，輸入審核筆記並點擊「核准（Approved）決策」，觸發 `POST /api/v1/cases/rev_individual_pep/review`。
* **THEN**：該案件的狀態必須 (SHALL) 更新為 `approved`，對應 Checklist 的 `human_review_required` 必須 (SHALL) 重置為 `False`，且防篡改日誌中必須 (SHALL) 級聯寫入一筆 `case_reviewed` 類型的日誌，重新計算 Hash Chain 保證防篡改鏈條未斷裂。

---

### Requirement: interactive_regulatory_graph_visualization
前端 Dashboard 必須 (SHALL) 構建一個全螢幕的 D3.js 互動式法規圖譜，將從 `GET /api/v1/graph` 獲取的點邊結構轉換為力導向圖。
* 節點類型必須包含：`SourceDocument`、`Clause`、`Obligation`、`CustomerContext` 與 `CDDChecklist`。
* 圖譜必須支持滑鼠滾輪縮放 (Zoom)、拖曳節點 (Drag)、以及滑鼠懸停 (Hover) 顯示含有法規條文與 Citation 的浮動 Tooltip 視窗。

#### Scenario: hover_regulatory_clause_node
* **GIVEN**：前端法規圖譜中渲染了代表 `mas626_clause_02` 的法規條款節點。
* **WHEN**：合規官將滑鼠游標懸停在該節點上方。
* **THEN**：前端必須 (SHALL) 彈出一個懸浮 Tooltip 卡片，動態展示該 `Clause` 節點屬性中的 `raw_text` 與其所關聯的 `citations`。

