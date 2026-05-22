from typing import List, Dict, Any, Optional
from datetime import datetime
from src.contracts.models import ReviewCase, CDDChecklist
from src.audit.logger import AuditLogger

class ReviewCaseManager:
    """
    人機協同管理引擎 ReviewCaseManager。
    負責審查案件 (ReviewCase) 的建立、流轉與合規官人工最終決策覆寫邏輯，
    並於案件變更時同步將變更軌跡織入 AuditLogger 防篡改審計鏈中。
    """
    def __init__(self, logger: AuditLogger):
        """
        初始化案件管理器。
        :param logger: 關聯的 AuditLogger 實例，用以實時記錄人工審批軌跡。
        """
        self.logger = logger
        self.cases: Dict[str, ReviewCase] = {}

    def create_case(
        self,
        customer_id: str,
        checklist_id: str,
        review_reason: List[str]
    ) -> ReviewCase:
        """
        為觸發人工審核條件的客戶建立 ReviewCase 審查案件。
        
        :param customer_id: 客戶唯一 ID
        :param checklist_id: 關聯的機器決策 CDDChecklist ID
        :param review_reason: 觸發人工介入的具體原因列表
        :return: 建立的 ReviewCase 實例
        """
        case_id = f"rev_{customer_id.replace('cust_', '')}"
        
        case = ReviewCase(
            case_id=case_id,
            customer_id=customer_id,
            checklist_id=checklist_id,
            review_reason=review_reason,
            approval_status="pending_review",
            reviewer_decision=None,
            reviewer_notes=None,
            reviewed_by=None,
            timestamp=datetime.utcnow()
        )
        
        self.cases[case_id] = case
        
        # 將案件建立事件記錄到 AuditLogger 中
        self.logger.log_event(
            event_type="case_created",
            operator="system_reasoning_engine",
            customer_id=customer_id,
            payload={
                "case_id": case_id,
                "checklist_id": checklist_id,
                "review_reason": review_reason
            }
        )
        
        return case

    def apply_review_decision(
        self,
        case_id: str,
        approval_status: str,
        reviewer_decision: Optional[str],
        notes: str,
        reviewer_id: str,
        checklists: Dict[str, CDDChecklist]
    ) -> ReviewCase:
        """
        合規官審批操作，更新案件狀態。若審批通過 (approved)，則會人工覆寫關聯 CDDChecklist 決策，
        將其 human_review_required 重置為 False，並於日誌中留下永久痕跡。
        
        :param case_id: 審查案件 ID
        :param approval_status: 審批狀態，"approved" / "rejected" / "needs_evidence"
        :param reviewer_decision: 人工最終決策等級，"simplified_cdd" / "standard_cdd" / "enhanced_due_diligence"
        :param notes: 審批意見說明
        :param reviewer_id: 審批人 ID 或簽名
        :param checklists: 系統當前的 Checklist 字典對照表，用以即時更新對應 Checklist
        :return: 更新後的 ReviewCase 實例
        """
        if case_id not in self.cases:
            raise KeyError(f"Review case '{case_id}' not found.")
            
        case = self.cases[case_id]
        
        # 1. 更新案件資料
        case.approval_status = approval_status
        case.reviewer_decision = reviewer_decision
        case.reviewer_notes = notes
        case.reviewed_by = reviewer_id
        case.timestamp = datetime.utcnow()
        
        # 2. 若為 approved 且提供了 reviewer_decision，則進行決策覆寫
        previous_decision = None
        if approval_status == "approved" and reviewer_decision:
            chk_id = case.checklist_id
            if chk_id in checklists:
                checklist = checklists[chk_id]
                previous_decision = checklist.decision
                
                # 執行覆寫
                checklist.decision = reviewer_decision
                checklist.human_review_required = False
                
                # 追加人工覆寫 Citation 溯源痕跡，保障 provenance 鏈條完整
                override_citation = f"Human Decision Override by {reviewer_id} at {case.timestamp.isoformat()}: {reviewer_decision}"
                if override_citation not in checklist.citations:
                    checklist.citations.append(override_citation)
        
        # 3. 記錄到 AuditLogger 中
        self.logger.log_event(
            event_type="case_reviewed",
            operator=reviewer_id,
            customer_id=case.customer_id,
            payload={
                "case_id": case_id,
                "approval_status": approval_status,
                "previous_decision": previous_decision,
                "new_decision": reviewer_decision,
                "notes": notes,
                "reviewer_id": reviewer_id
            }
        )
        
        return case
