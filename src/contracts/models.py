from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class SourceDocument(BaseModel):
    """
    原始法規或內部政策文件的元數據記錄。
    """
    source_document_id: str = Field(..., description="Primary identifier")
    title: str = Field(..., description="Document title")
    issuer: str = Field(..., description="Regulatory body, e.g., 'MAS'")
    jurisdiction: str = Field(..., description="Jurisdiction region, e.g., 'Singapore'")
    version: str = Field(..., description="Document version")
    effective_date: Optional[str] = Field(None, description="ISO date (YYYY-MM-DD)")
    retrieval_date: str = Field(..., description="ISO date (YYYY-MM-DD)")
    source_url: Optional[str] = Field(None, description="Web source path")
    local_path: str = Field(..., description="Path to cached source document")
    content_hash: Optional[str] = Field(None, description="Integrity verification")


class Clause(BaseModel):
    """
    從源文件中分割出的最小獨立條款。
    """
    clause_id: str = Field(..., description="e.g., mas626_cdd_001")
    source_document_id: str = Field(..., description="Foreign key to SourceDocument")
    section_ref: str = Field(..., description="Human-readable section citation")
    parent_clause_id: Optional[str] = Field(None, description="Allows multi-layer nested tree representation")
    raw_text: str = Field(..., description="Exact original text")
    normalized_text: str = Field(..., description="Cleaned text for embedding")
    citations: List[str] = Field(..., description="List of stable provenance citations")


class Obligation(BaseModel):
    """
    從條款中抽取的機器可讀合規義務規則。
    """
    obligation_id: str = Field(..., description="e.g., identify_beneficial_owner")
    source_clause_ids: List[str] = Field(..., min_length=1, description="List of clause IDs, ensuring clause-level provenance")
    jurisdiction: str = Field(..., description="Jurisdiction of the obligation")
    actor: str = Field(..., description="e.g., financial_institution")
    action: str = Field(..., description="e.g., identify_and_verify")
    object: str = Field(..., description="e.g., beneficial_owner")
    applies_to: Dict[str, Any] = Field(default_factory=dict, description="Entity constraints")
    conditions: List[str] = Field(default_factory=list, description="Factual triggers")
    exceptions: List[str] = Field(default_factory=list, description="Exemptions")
    required_evidence: List[str] = Field(default_factory=list, description="Required evidence")
    review_flags: List[str] = Field(default_factory=list, description="Triggers for human review")
    confidence: float = Field(..., description="Extraction confidence score")
    review_status: Literal["pending_human_review", "approved"] = Field(
        default="pending_human_review", 
        description="Verification state"
    )


class CustomerContext(BaseModel):
    """
    結構化客戶情境，用於進行 CDD 風險畫像比對。
    """
    customer_id: str = Field(...)
    customer_type: Literal["individual", "corporate"] = Field(..., description="Customer classification")
    registration_jurisdiction: str = Field(...)
    ownership_layers: int = Field(...)
    ubo_status: Literal["identified", "unclear"] = Field(..., description="Ultimate Beneficial Owner status")
    ubo_country_risk: Literal["low", "medium", "high"] = Field(..., description="Country-associated risk level")
    pep_exposure: bool = Field(...)
    source_of_funds_available: bool = Field(...)
    source_of_wealth_available: bool = Field(...)
    custom_attributes: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Dynamic data payload for 'schema-light' flexibility"
    )


class Conflict(BaseModel):
    """
    用於追溯多條法規或政策之間時間性、特異性或權威性衝突的動態記錄。
    """
    conflict_id: str = Field(...)
    conflict_type: Literal["Temporal", "Numerical", "Specificity", "PolicyReversal", "Authority", "Process"] = Field(
        ..., description="Categorized conflict type"
    )
    source_clause_ids: List[str] = Field(..., min_length=1, description="Pairwise or multiple conflict sources")
    verifiability: Literal["retrieval-verifiable", "retrieval-resistant"] = Field(
        ..., description="Verification approach suitability"
    )
    description: str = Field(..., description="Human-readable conflict narrative")
    reconciliation_rule: Optional[str] = Field(None, description="Reconciliation logic if decidable")
    adjudication_status: Literal["pending_human_review", "resolved"] = Field(
        ..., description="Reconciliation workflow status"
    )
    resolved_by: Optional[str] = Field(None)


class CDDChecklist(BaseModel):
    """
    最終生成的客戶合規檢核表決策與所需行動輸出。
    """
    checklist_id: str = Field(...)
    customer_id: str = Field(..., description="Foreign key to CustomerContext")
    decision: Literal["simplified_cdd", "standard_cdd", "enhanced_due_diligence"] = Field(
        ..., description="CDD Tier Decision"
    )
    required_documents: List[str] = Field(..., description="Auditable checklists")
    risk_triggers: List[str] = Field(..., description="Factual triggers activated")
    applicable_obligations: List[str] = Field(..., description="Foreign keys to active Obligations")
    unresolved_conflicts: List[str] = Field(..., description="Foreign keys to unresolved Conflicts")
    human_review_required: bool = Field(..., description="Routing flag to human queue")
    citations: List[str] = Field(..., description="Provenance citations back to clauses")


class Concept(BaseModel):
    """
    合規概念的強型別模型，用於支持別名同名化與條款級溯源。
    """
    concept_id: str = Field(..., description="Canonical ID, e.g., 'ubo'")
    name: str = Field(..., description="Display name of the concept")
    description: str = Field(..., description="Brief Chinese description")
    aliases: List[str] = Field(default_factory=list, description="Synonym aliases")
    source_clause_ids: List[str] = Field(default_factory=list, description="Clause-level provenance IDs")


class ProvenanceNode(BaseModel):
    """
    溯源路徑中的單一實體或事實節點。
    """
    node_id: str = Field(..., description="Unique node identifier")
    node_type: Literal["customer_fact", "obligation", "clause", "document"] = Field(
        ..., description="Node classification"
    )
    label: str = Field(..., description="Display label")
    properties: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Factual metadata payload, e.g., raw_text, values"
    )


class ExplanationPath(BaseModel):
    """
    表達某一特定檢核清單要求（如 Senior Management Approval Form）的完整有向合規解釋鏈。
    """
    target_item: str = Field(..., description="The checklist item being explained")
    path_nodes: List[ProvenanceNode] = Field(..., min_length=2, description="Lineage path from fact to document")
    description: str = Field(..., description="Human-readable synthesis explanation")


class GraphNode(BaseModel):
    """
    圖譜中的單一合規知識或事實節點。
    """
    node_id: str = Field(..., description="Unique node ID, e.g. 'mas626_clause_04'")
    node_type: Literal[
        "SourceDocument", 
        "Clause", 
        "Concept", 
        "Obligation", 
        "CustomerContext", 
        "Conflict", 
        "CDDChecklist",
        "EvidenceRequirement",
        "RiskTrigger",
        "ReviewCase"
    ] = Field(..., description="Node classification type")
    label: str = Field(..., description="Human-readable node title/label")
    properties: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Factual metadata payload, e.g., raw_text, version, attributes"
    )


class GraphEdge(BaseModel):
    """
    圖譜中節點與節點之間的有向關係邊。
    """
    edge_id: str = Field(..., description="Unique edge identifier, e.g. 'nodeA_to_nodeB_requires'")
    source_id: str = Field(..., description="Source node ID")
    target_id: str = Field(..., description="Target node ID")
    edge_type: Literal[
        "defines",              # Concept defines Concept, Document defines Clause
        "requires",             # Obligation requires Evidence
        "applies_to",           # Obligation applies to CustomerType/CustomerContext
        "conditioned_on",       # Obligation conditioned on facts
        "except_when",          # Exception relation
        "requires_evidence",    # Obligation requires EvidenceRequirement
        "references_clause",    # Obligation references Clause, Conflict references Clause
        "same_as",              # Concept alias mapping
        "stricter_than",        # Conflict/Rule comparison
        "supersedes",           # Version superseding
        "conflicts_with",       # Conflict/Rule collision
        "derived_from",         # Provenance lineage relation
        "decision_path"         # Highlighted active decision path
    ] = Field(..., description="Relationship semantic type")
    label: str = Field(..., description="Human-readable edge label")
    properties: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Edge metadata payload, e.g., weight, reasoning_logic"
    )


class RegulatoryGraph(BaseModel):
    """
    大一統法規合規知識圖譜資料結構。
    """
    nodes: Dict[str, GraphNode] = Field(default_factory=dict, description="Fast access map of node ID to Node")
    edges: List[GraphEdge] = Field(default_factory=list, description="Collection of all relationship edges")


class EvaluationMetrics(BaseModel):
    """
    記錄單項評估維度的量化指標。
    """
    precision: float = Field(..., description="Precision score")
    recall: float = Field(..., description="Recall score")
    f1_score: float = Field(..., description="F1-score")
    accuracy: float = Field(..., description="Accuracy score")


class DiagnosticReport(BaseModel):
    """
    描述決策錯誤的根源診斷結果。
    """
    checklist_id: str = Field(..., description="The ID of the generated checklist being evaluated")
    has_error: bool = Field(..., description="True if there is a mismatch with the gold checklist")
    error_source: Optional[Literal["retrieval", "extraction", "graph_modeling", "conflict_handling", "reasoning"]] = Field(
        None, description="Pinpointed root cause of the error"
    )
    diagnostic_details: str = Field(..., description="Detailed diagnostic reasoning narrative")


class ComparisonReport(BaseModel):
    """
    匯總系統與 Baseline 評估對比結果。
    """
    cdd_wiki_metrics: Dict[str, EvaluationMetrics] = Field(..., description="Metrics for CDD-GraphWiki")
    baseline_metrics: Dict[str, EvaluationMetrics] = Field(..., description="Metrics for Vector-RAG Baseline")
    diagnostics: List[DiagnosticReport] = Field(default_factory=list, description="Detailed diagnostic tree reports")


class ReviewCase(BaseModel):
    """
    人工合規審查案件。
    用於管理需要人工介入審核的合規案件生命週期。
    """
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


class AuditLogEntry(BaseModel):
    """
    合規決策與審查之鏈式防篡改審計日誌項目。
    每一條日誌項目都包含了 previous_hash 和 current_hash，構建防篡改的鏈式結構。
    """
    log_id: str = Field(..., description="日誌唯一 ID，格式為 log_xxx")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="日誌時間戳")
    event_type: Literal[
        "reasoning_triggered", 
        "conflict_detected", 
        "case_created", 
        "case_reviewed", 
        "tamper_check_failed"
    ] = Field(..., description="事件類型")
    operator: str = Field(..., description="執行操作的系統模組或人工 ID")
    customer_id: str = Field(..., description="關聯的客戶 ID")
    payload: Dict[str, Any] = Field(..., description="事件關聯的關鍵資料負載")
    previous_hash: str = Field(..., description="上一條審計日誌的雜湊值，用於構建 Hash Chain")
    current_hash: str = Field(..., description="當前日誌項的 SHA-256 鏈式雜湊值，保障防篡改特性")





