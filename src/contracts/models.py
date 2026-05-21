from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


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


