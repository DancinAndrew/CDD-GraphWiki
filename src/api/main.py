import os
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field
from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware

from src.contracts.models import (
    CustomerContext,
    CDDChecklist,
    ReviewCase,
    AuditLogEntry,
    GraphNode,
    GraphEdge
)
from src.api.dependencies import (
    get_engine,
    get_logger,
    get_manager,
    load_knowledge_base
)
from src.graph.builder import GraphBuilder

app = FastAPI(
    title="CDD-GraphWiki Compliance Hub API",
    description="AML/CDD 推理決策與防篡改審計工作台 API 服務",
    version="1.0.0"
)

# 啟用 CORS 跨來源共享，允許前端 Docker / 本地服務調用
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 在 API 記憶體中維護當前的 Checklist 狀態，支持人工審查熱更新
_checklists: Dict[str, CDDChecklist] = {}


class ReviewDecisionRequest(BaseModel):
    """
    合規官審核案件的 Pydantic 輸入合約（強型別白名單校驗）
    """
    approval_status: Literal["approved", "rejected", "needs_evidence"] = Field(
        ..., description="核准狀態"
    )
    reviewer_decision: Literal["simplified_cdd", "standard_cdd", "enhanced_due_diligence"] = Field(
        ..., description="人工最終覆寫之 CDD 等級"
    )
    notes: str = Field(..., min_length=5, max_length=1000, description="審批意見筆記")
    reviewer_id: str = Field(..., min_length=2, description="合規官 ID")


@app.on_event("startup")
def startup_event():
    """
    API 啟動時的自動初始化：
    1. 加載金標法規知識數據
    2. 自動觸發全部客戶的決策推理
    3. 若 Checklist 需要人工介入且 ReviewCase 未建立，自動建立 'pending_review' 案件
    """
    global _checklists
    print("=" * 80)
    print("🚀  CDD-GraphWiki compliance API is initializing  🚀")
    print("=" * 80)

    # 1. 載入法規知識
    kb = load_knowledge_base()
    customers = kb["customers"]
    obligations = kb["obligations"]
    conflicts = kb["conflicts"]

    engine = get_engine()
    logger = get_logger()
    manager = get_manager()

    # 2. 自動執行初審推理並加入隊列
    for cust in customers:
        checklist = engine.generate_checklist(cust, obligations, conflicts)
        _checklists[checklist.checklist_id] = checklist
        
        # 寫入日誌 (若日誌已存在，不會重複寫入重複項，但在此處保證有初始記錄)
        logger.log_reasoning(
            operator="CDD_Reasoning_Engine",
            customer_id=cust.customer_id,
            checklist_id=checklist.checklist_id,
            decision=checklist.decision,
            ingestion_hash="hash_ingest_pep_mas626",
            graph_version="g_v1.0.0",
            rule_version="r_v2.1.0"
        )

        # 3. 觸發人機協同：如果需要人工介入且 ReviewCase 還不存在，則自動創建審批案件
        if checklist.human_review_required:
            case_id = f"rev_{cust.customer_id.replace('cust_', '')}"
            # 檢查案件是否已經在 manager 中 (若 manager 已在本地 log 加載歷史日誌，案件可能已存在)
            existing_case = manager.cases.get(case_id)
            if not existing_case:
                # 判斷觸發理由
                reasons = []
                if cust.pep_exposure:
                    reasons.append("pep_exposure_detected")
                if cust.ubo_status == "unclear":
                    reasons.append("unclear_ubo_layers")
                if cust.ownership_layers > 2:
                    reasons.append("excessive_ownership_layers")
                if not reasons:
                    reasons.append("manual_routing_required")
                
                manager.create_case(
                    customer_id=cust.customer_id,
                    checklist_id=checklist.checklist_id,
                    review_reason=reasons
                )
                print(f"  [Auto-Route] 建立待人工審查案件: {case_id} ➔ 客戶: {cust.customer_id}")

    print("✓ CDD-GraphWiki API 初始化與案件自動路由完成！")
    print("=" * 80)


# ==========================================
# 1. 客戶與決策推理 APIs
# ==========================================

@app.get("/api/v1/customers", response_model=List[CustomerContext])
def list_customers():
    """
    獲取所有典型客戶情境列表。
    """
    kb = load_knowledge_base()
    return kb["customers"]


@app.get("/api/v1/customers/{customer_id}/checklist", response_model=CDDChecklist)
def get_customer_checklist(customer_id: str):
    """
    獲取指定客戶的 CDD Checklist 推理決策。
    """
    # 查找 checklist
    chk_id = f"chk_{customer_id.replace('cust_', '')}"
    if chk_id not in _checklists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checklist not found for customer: {customer_id}"
        )
    return _checklists[chk_id]


# ==========================================
# 2. 人機協同審批工作台 APIs
# ==========================================

@app.get("/api/v1/cases", response_model=List[ReviewCase])
def list_cases(status_filter: Optional[str] = Query(None, alias="status")):
    """
    獲取所有人工審查案件列表。
    可選參數：status (pending_review, approved, rejected, needs_evidence)
    """
    manager = get_manager()
    cases = list(manager.cases.values())
    if status_filter:
        cases = [c for c in cases if c.approval_status == status_filter]
    # 排序：pending_review 排前面，最新變更排前面
    cases.sort(key=lambda x: (x.approval_status != "pending_review", x.timestamp), reverse=True)
    return cases


@app.post("/api/v1/cases/{case_id}/review", response_model=ReviewCase)
def review_case(case_id: str, request: ReviewDecisionRequest):
    """
    合規官審核案件並覆寫決策（具有 Pydantic 強型別防禦與 Hash Chain 織入）。
    """
    manager = get_manager()
    case = manager.cases.get(case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ReviewCase not found: {case_id}"
        )
    
    if case.approval_status != "pending_review":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Case is already reviewed. Current status: {case.approval_status}"
        )

    try:
        updated_case = manager.apply_review_decision(
            case_id=case_id,
            approval_status=request.approval_status,
            reviewer_decision=request.reviewer_decision,
            notes=request.notes,
            reviewer_id=request.reviewer_id,
            checklists=_checklists
        )
        return updated_case
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Review decision failed to apply: {str(e)}"
        )


# ==========================================
# 3. 鏈式防篡改日誌 APIs
# ==========================================

@app.get("/api/v1/audit/logs", response_model=List[AuditLogEntry])
def list_audit_logs():
    """
    獲取防篡改鏈式日誌完整時間線。
    """
    logger = get_logger()
    return logger.entries


@app.get("/api/v1/audit/verify")
def verify_audit_integrity():
    """
    執行鏈式 SHA-256 雜湊自檢校驗。
    """
    logger = get_logger()
    is_intact, tampered_idx = logger.verify_integrity(return_index=True)
    return {
        "is_intact": is_intact,
        "total_entries": len(logger.entries),
        "tampered_index": tampered_idx,
        "error_message": None if is_intact else f"Hash Chain is broken at log entry #{tampered_idx}"
    }


# ==========================================
# 4. 知識圖譜 APIs (D3.js 點邊相容)
# ==========================================

@app.get("/api/v1/graph")
def get_regulatory_graph():
    """
    導出 D3.js 力導向圖譜期待的點邊 JSON 結構。
    """
    kb = load_knowledge_base()
    
    # 圖譜構建：將當前熱更新後的 Checklists 狀態傳入，實現前端實時連動展示
    regulatory_graph = GraphBuilder.build_regulatory_graph(
        documents=kb["documents"],
        clauses=kb["clauses"],
        obligations=kb["obligations"],
        concepts=[],
        conflicts=kb["conflicts"],
        customers=kb["customers"],
        checklists=list(_checklists.values())
    )

    d3_nodes = []
    for nid, node in regulatory_graph.nodes.items():
        d3_nodes.append({
            "node_id": node.node_id,
            "node_type": node.node_type,
            "label": node.label,
            "properties": node.properties
        })

    d3_links = []
    for edge in regulatory_graph.edges:
        d3_links.append({
            "edge_id": edge.edge_id,
            "source": edge.source_id,
            "target": edge.target_id,
            "edge_type": edge.edge_type,
            "label": edge.label,
            "properties": edge.properties
        })

    return {
        "nodes": d3_nodes,
        "links": d3_links
    }
