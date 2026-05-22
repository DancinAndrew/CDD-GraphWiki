# Design - Human-in-the-Loop & Audit Logging (人機協同與合規審計日誌)

本設計方案詳細說明了 CDD-GraphWiki 專案在 **Phase 10: Human-in-the-Loop & Audit Logging (人機協同與合規審計日誌)** 中的具體技術實作架構，符合專案的 spec-first 及防禦性編程規範。

---

## 1. 數據合約設計 (Data Contracts)

我們將在 `src/contracts/models.py` 中擴充兩個全新的 Pydantic 強型別資料模型：

### 1.1 `ReviewCase`
用於管理需要人工介入審核的合規案件生命週期。

```python
from datetime import datetime
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field

class ReviewCase(BaseModel):
    case_id: str = Field(..., description="人工審查案件唯一 ID，格式為 rev_cust_xxx")
    customer_id: str = Field(..., description="關聯的客戶 ID")
    checklist_id: str = Field(..., description="關聯的推理 CDDChecklist ID")
    review_reason: List[str] = Field(..., description="觸發人工審查的具體原因列表")
    approval_status: Literal["pending_review", "approved", "rejected", "needs_evidence"] = Field(
        "pending_review", description="案件的合規審批狀態"
    )
    reviewer_decision: Optional[Literal["simplified_cdd", "standard_cdd", "enhanced_due_diligence"]] = Field(
        None, description="人工最終決策等級，若已批准則會覆寫原機器決策"
    )
    reviewer_notes: Optional[str] = Field(None, description="合規審批筆記與說明")
    reviewed_by: Optional[str] = Field(None, description="合規審批人 ID 或簽名")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="案件建立或變更時間")
```

### 1.2 `AuditLogEntry`
用於記錄系統推理與人工決策生命週期中的不可篡改審計日誌項目。

```python
class AuditLogEntry(BaseModel):
    log_id: str = Field(..., description="日誌唯一 ID，格式為 log_xxx")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="日誌時間戳")
    event_type: Literal["reasoning_triggered", "conflict_detected", "case_created", "case_reviewed", "tamper_check_failed"] = Field(
        ..., description="事件類型"
    )
    operator: str = Field(..., description="執行操作的系統模組或人工 ID")
    customer_id: str = Field(..., description="關聯的客戶 ID")
    payload: Dict[str, Any] = Field(..., description="事件關聯的關鍵資料負載")
    previous_hash: str = Field(..., description="上一條審計日誌的雜湊值，用於構建 Hash Chain")
    current_hash: str = Field(..., description="當前日誌項的 SHA-256 鏈式雜湊值，保障防篡改特性")
```

---

## 2. 鏈式防篡改日誌引擎 (`AuditLogger`)

### 2.1 鏈式雜湊傳導機制 (Hash Chain)
為了在不依賴重型區塊鏈或資料庫的情況下保障審計軌跡的「不可篡改性」，我們實作一個 Hash Chain 鏈式日誌傳遞。
當寫入一條新的日誌 $i$ 時，其 `current_hash` 的計算公式如下：
$$Hash_i = SHA256(Payload_i + Timestamp_i + PreviousHash_{i-1})$$

如果攻擊者篡改了歷史日誌中的任何一個字元，該節點的 $Hash_k$ 將會改變，進而導致後續所有日誌節點的 `previous_hash` 不匹配，日誌防篡改校驗程序將會立刻發出 `tamper_check_failed` 警報。

### 2.2 防篡改校驗演算法 (`verify_integrity`)
```python
def verify_integrity(self) -> bool:
    """
    遍歷審計日誌鏈，驗證雜湊鏈是否完整、未遭篡改。
    """
    for i in range(1, len(self.logs)):
        prev_log = self.logs[i-1]
        curr_log = self.logs[i]
        
        # 1. 校驗上一條的哈希是否與當前記錄的 previous_hash 一致
        if curr_log.previous_hash != prev_log.current_hash:
            return False
            
        # 2. 重新計算當前哈希並比對
        recalculated_hash = self._calculate_hash(curr_log)
        if curr_log.current_hash != recalculated_hash:
            return False
    return True
```

---

## 3. 人機協同控制引擎 (`ReviewCaseManager`)

* **案件生成自動觸發**：當 `CDDChecklist.human_review_required == True` 時，自動創建 `ReviewCase`，初始狀態為 `pending_review`。
* **決策覆寫織入**：合規官審閱案件，並填寫 `reviewer_decision` (例如：將機器推理的 `standard_cdd` 改為 `enhanced_due_diligence`)。
* 當調用 `apply_review_decision(case_id, decision, notes, reviewer)` 時：
  1. 更新 `ReviewCase` 的狀態為 `approved` 或 `rejected`。
  2. 自動定位關聯的 `CDDChecklist`，將其 `decision` 覆寫為人工決策值，並將 `human_review_required` 標記改為 `False` (代表已完成人工介入審查)。
  3. 自動向 `AuditLogger` 寫入 `case_reviewed` 事件，記錄完整的覆寫軌跡。

---

## 4. 監管合規審計報告生成器 (`AuditReportGenerator`)

* 實作 `AuditReportGenerator`，提供 `generate_audit_report(customer_id)` 方法。
* **輸出格式**：
  * **Markdown 審計報告**：便於終端顯示與歸檔。
  * **HTML 視覺報告**：採用專案標誌性的 **Vanilla CSS 暗黑磨砂玻璃美學 (Dark Glassmorphic UI)**，並配以流暢微動效。
* **報告包含內容**：
  * **客戶原始上下文 (Customer Context)**。
  * **最終合規決策狀態 (Final CDD Checklist)**：標明原始機器決策、人工審批覆寫軌跡。
  * **法理溯源地圖 (Provenance & Citations)**：展示關聯的 FATF/MAS 原始條款與 Ingestion 哈希。
  * **防篡改審計鏈完整日誌 (Tamper-evident Audit Trail)**。

---

## 5. 測試策略 (Test Strategy)

在 `tests/test_human_in_the_loop_audit.py` 中撰寫嚴格的自動化測試：
1. **`test_review_case_lifecycle`**：測試當生成一個需要審查的 Checklist 時，自動創建 `ReviewCase`，並驗證人工決策覆寫的有效性（Checklist 的決策成功被人工覆寫，且審查標誌成功被解除）。
2. **`test_audit_logger_tamper_evidence`**：
   * 寫入多條日誌，驗證 `verify_integrity()` 回傳 `True`。
   * 手動修改其中一條日誌的 `payload` 內容，斷言 `verify_integrity()` 回傳 `False`，驗證防篡改鏈的敏感度。
3. **`test_audit_report_generation`**：驗證 HTML 和 Markdown 報告成功生成，且包含 PII 脫敏處理。
