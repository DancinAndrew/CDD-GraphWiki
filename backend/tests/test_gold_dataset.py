import os
import yaml
from typing import List, Dict, Any
from src.contracts.models import (
    SourceDocument,
    Clause,
    Obligation,
    CustomerContext,
    Conflict,
    CDDChecklist
)

# 定義黃金數據集目錄路徑
GOLD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/gold"))



def load_yaml(filename: str) -> List[Dict[str, Any]]:
    """
    載入指定 YAML 檔案並返回結構化列表。
    """
    file_path = os.path.join(GOLD_DIR, filename)
    assert os.path.exists(file_path), f"黃金數據檔案不存在: {file_path}"
    with open(file_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert isinstance(data, list), f"YAML 檔案格式不符合列表規範: {filename}"
    return data


def test_source_documents_contract():
    """
    驗證 source_documents.yaml 符合 SourceDocument Pydantic 資料合約。
    """
    raw_data = load_yaml("source_documents.yaml")
    assert len(raw_data) >= 3, "應包含至少 3 份源文件"
    for item in raw_data:
        # 使用 Pydantic 強型別解構，若校驗失敗會自動拋出 ValidationError
        doc = SourceDocument(**item)
        assert doc.source_document_id is not None
        assert doc.title != ""


def test_clauses_contract():
    """
    驗證 clauses.yaml 符合 Clause Pydantic 資料合約。
    """
    raw_data = load_yaml("clauses.yaml")
    assert len(raw_data) >= 10, "應包含至少 10 個核心法規條款"
    for item in raw_data:
        clause = Clause(**item)
        assert clause.clause_id is not None
        assert len(clause.citations) > 0


def test_obligations_contract():
    """
    驗證 obligations.yaml 符合 Obligation Pydantic 資料合約。
    """
    raw_data = load_yaml("obligations.yaml")
    assert len(raw_data) >= 10, "應包含至少 10 個核心合規義務"
    for item in raw_data:
        obligation = Obligation(**item)
        assert obligation.obligation_id is not None
        assert len(obligation.source_clause_ids) >= 1
        assert obligation.review_status in ["pending_human_review", "approved"]


def test_conflicts_contract():
    """
    驗證 conflicts.yaml 符合 Conflict Pydantic 資料合約。
    """
    raw_data = load_yaml("conflicts.yaml")
    assert len(raw_data) >= 3, "應包含至少 3 個法規與政策衝突"
    for item in raw_data:
        conflict = Conflict(**item)
        assert conflict.conflict_id is not None
        assert len(conflict.source_clause_ids) >= 1
        assert conflict.conflict_type in ["Temporal", "Numerical", "Specificity", "PolicyReversal", "Authority", "Process"]


def test_customer_contexts_contract():
    """
    驗證 customer_contexts.yaml 符合 CustomerContext Pydantic 資料合約。
    """
    raw_data = load_yaml("customer_contexts.yaml")
    assert len(raw_data) >= 5, "應包含至少 5 個測試客戶情境"
    for item in raw_data:
        context = CustomerContext(**item)
        assert context.customer_id is not None
        assert context.customer_type in ["individual", "corporate"]


def test_checklists_contract():
    """
    驗證 checklists.yaml 符合 CDDChecklist Pydantic 資料合約。
    """
    raw_data = load_yaml("checklists.yaml")
    assert len(raw_data) >= 5, "應包含至少 5 個預期檢核表決策"
    for item in raw_data:
        checklist = CDDChecklist(**item)
        assert checklist.checklist_id is not None
        assert checklist.decision in ["simplified_cdd", "standard_cdd", "enhanced_due_diligence"]


def test_semantic_relationship_integrity():
    """
    深度語意關係完整性檢查（外鍵約束、存在性與雙向溯源閉環）。
    """
    # 載入所有數據並做 Pydantic 實例化，以便進行對照
    docs = {item["source_document_id"]: SourceDocument(**item) for item in load_yaml("source_documents.yaml")}
    clauses = {item["clause_id"]: Clause(**item) for item in load_yaml("clauses.yaml")}
    obligations = {item["obligation_id"]: Obligation(**item) for item in load_yaml("obligations.yaml")}
    conflicts = {item["conflict_id"]: Conflict(**item) for item in load_yaml("conflicts.yaml")}
    customers = {item["customer_id"]: CustomerContext(**item) for item in load_yaml("customer_contexts.yaml")}
    checklists = {item["checklist_id"]: CDDChecklist(**item) for item in load_yaml("checklists.yaml")}

    # 1. 驗證 Clause 的外鍵關係
    for cid, clause in clauses.items():
        # 1.1 驗證 source_document_id 必須存在於 SourceDocument 列表中
        assert clause.source_document_id in docs, f"Clause {cid} 引用了不存在的 SourceDocument ID: {clause.source_document_id}"
        # 1.2 驗證 parent_clause_id（若存在）必須存在於 Clause 列表中
        if clause.parent_clause_id:
            assert clause.parent_clause_id in clauses, f"Clause {cid} 引用了不存在的父級 Clause ID: {clause.parent_clause_id}"

    # 2. 驗證 Obligation 的溯源關係
    for oid, obligation in obligations.items():
        for cid in obligation.source_clause_ids:
            # 2.1 驗證 source_clause_ids 內的所有 ID 必須存在於 Clause 列表中
            assert cid in clauses, f"Obligation {oid} 引用了不存在的 Clause ID: {cid}"

    # 3. 驗證 Conflict 的溯源關係
    for conf_id, conflict in conflicts.items():
        for cid in conflict.source_clause_ids:
            # 3.1 驗證 source_clause_ids 內的所有 ID 必須存在於 Clause 列表中
            assert cid in clauses, f"Conflict {conf_id} 引用了不存在的 Clause ID: {cid}"

    # 4. 驗證 CDDChecklist 的關聯關係
    for chk_id, checklist in checklists.items():
        # 4.1 驗證 customer_id 必須存在於 CustomerContext 列表中
        assert checklist.customer_id in customers, f"Checklist {chk_id} 引用了不存在的 Customer ID: {checklist.customer_id}"
        
        # 4.2 驗證 applicable_obligations 內的所有 ID 必須存在於 Obligation 列表中
        for oid in checklist.applicable_obligations:
            assert oid in obligations, f"Checklist {chk_id} 引用了不存在的 Obligation ID: {oid}"
            
        # 4.3 驗證 unresolved_conflicts 內的所有 ID 必須存在於 Conflict 列表中
        for conf_id in checklist.unresolved_conflicts:
            assert conf_id in conflicts, f"Checklist {chk_id} 引用了不存在的 Conflict ID: {conf_id}"
            
        # 4.4 驗證 3-way 條文溯源完整性 (Checklist -> Obligation -> Clause)
        for oid in checklist.applicable_obligations:
            obligation = obligations[oid]
            for cid in obligation.source_clause_ids:
                # 確保在 checklist 中引用了對應的條款，或能追溯回條款
                assert cid in clauses, f"Checklist {chk_id} 關聯的 Obligation {oid} 所引用的條款 {cid} 不存在"
