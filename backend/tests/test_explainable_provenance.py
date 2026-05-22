import os
import yaml
from typing import List, Dict, Any
from src.contracts.models import (
    CustomerContext,
    Obligation,
    Clause,
    SourceDocument,
    CDDChecklist,
    ProvenanceNode,
    ExplanationPath
)
from src.decision.provenance import ProvenanceEngine

# 定義目錄路徑
GOLD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/gold"))



def load_yaml(filename: str, dir_path: str = GOLD_DIR) -> List[Dict[str, Any]]:
    """
    載入指定 YAML 檔案並返回結構化列表。
    """
    file_path = os.path.join(dir_path, filename)
    assert os.path.exists(file_path), f"YAML 檔案不存在: {file_path}"
    with open(file_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert isinstance(data, list), f"YAML 檔案格式不符合列表規範: {filename}"
    return data


def test_provenance_node_and_explanation_path_validation():
    """
    驗證 ProvenanceNode 與 ExplanationPath 模型的強型別校驗與序列化。
    """
    # 測試 ProvenanceNode 實例化
    fact_node = ProvenanceNode(
        node_id="fact_pep",
        node_type="customer_fact",
        label="客戶特徵：政要曝險 (pep_exposure = True)",
        properties={"pep_exposure": True}
    )
    assert fact_node.node_id == "fact_pep"
    assert fact_node.node_type == "customer_fact"
    assert fact_node.properties["pep_exposure"] is True

    # 測試 ExplanationPath 實例化
    path = ExplanationPath(
        target_item="Senior Management Approval Form",
        path_nodes=[
            fact_node,
            ProvenanceNode(
                node_id="ob_pep_edd_mas",
                node_type="obligation",
                label="合規義務：ob_pep_edd_mas",
                properties={}
            )
        ],
        description="合規論述摘要測試"
    )
    assert path.target_item == "Senior Management Approval Form"
    assert len(path.path_nodes) == 2
    assert path.description == "合規論述摘要測試"


def test_explain_pep_senior_management_approval():
    """
    驗證普通政要個人情境下，解釋 "Senior Management Approval Form" 的路徑與法源明文引述是否精確。
    """
    # 載入金標資料
    raw_customers = load_yaml("customer_contexts.yaml")
    raw_obligations = load_yaml("obligations.yaml")
    raw_clauses = load_yaml("clauses.yaml")
    raw_documents = load_yaml("source_documents.yaml")
    raw_checklists = load_yaml("checklists.yaml")

    customers = [CustomerContext(**item) for item in raw_customers]
    obligations = [Obligation(**item) for item in raw_obligations]
    clauses = [Clause(**item) for item in raw_clauses]
    documents = [SourceDocument(**item) for item in raw_documents]
    checklists = [CDDChecklist(**item) for item in raw_checklists]

    # 取出普通政要個人
    cust_pep = next(c for c in customers if c.customer_id == "cust_individual_pep")
    chk_pep = next(k for k in checklists if k.customer_id == "cust_individual_pep")

    engine = ProvenanceEngine()
    
    # 進行回溯解釋
    path = engine.explain_item(
        checklist=chk_pep,
        target_item="Senior Management Approval Form",
        customer=cust_pep,
        obligations=obligations,
        clauses=clauses,
        documents=documents
    )

    assert isinstance(path, ExplanationPath)
    assert path.target_item == "Senior Management Approval Form"
    
    # 驗證首個事實節點
    fact_node = path.path_nodes[0]
    assert fact_node.node_type == "customer_fact"
    assert fact_node.properties["pep_exposure"] is True
    
    # 驗證包含義務 ob_pep_edd_mas 節點
    ob_node = next(n for n in path.path_nodes if n.node_type == "obligation")
    assert ob_node.node_id == "ob_pep_edd_mas"
    
    # 驗證包含條款 mas626_clause_04 節點並引述正確的明文
    clause_node = next(n for n in path.path_nodes if n.node_type == "clause")
    assert clause_node.node_id == "mas626_clause_04"
    assert "determine whether a customer or any beneficial owner is a politically exposed person" in clause_node.properties["raw_text"]

    
    # 驗證包含源文件 mas_notice_626
    doc_node = path.path_nodes[-1]
    assert doc_node.node_type == "document"
    assert doc_node.node_id == "mas_notice_626"
    assert doc_node.properties["issuer"] == "MAS"
    
    # 驗證 description 繁體中文論述
    assert "反洗錢政要曝險特徵" in path.description
    assert "新加坡金融管理局" in path.description


def test_explain_high_risk_pep_rejection():
    """
    驗證高風險政要禁止開戶情境下，解釋 "Rejected Onboarding Notification" 的有向路徑與義務。
    """
    raw_customers = load_yaml("customer_contexts.yaml")
    raw_obligations = load_yaml("obligations.yaml")
    raw_clauses = load_yaml("clauses.yaml")
    raw_documents = load_yaml("source_documents.yaml")
    raw_checklists = load_yaml("checklists.yaml")

    customers = [CustomerContext(**item) for item in raw_customers]
    obligations = [Obligation(**item) for item in raw_obligations]
    clauses = [Clause(**item) for item in raw_clauses]
    documents = [SourceDocument(**item) for item in raw_documents]
    checklists = [CDDChecklist(**item) for item in raw_checklists]

    cust_hr_pep = next(c for c in customers if c.customer_id == "cust_individual_high_risk_pep")
    chk_hr_pep = next(k for k in checklists if k.customer_id == "cust_individual_high_risk_pep")

    engine = ProvenanceEngine()
    
    path = engine.explain_item(
        checklist=chk_hr_pep,
        target_item="Rejected Onboarding Notification",
        customer=cust_hr_pep,
        obligations=obligations,
        clauses=clauses,
        documents=documents
    )

    assert isinstance(path, ExplanationPath)
    assert path.target_item == "Rejected Onboarding Notification"
    
    # 驗證包含 high-risk 國家與政要事實
    fact_ids = [n.node_id for n in path.path_nodes if n.node_type == "customer_fact"]
    assert "fact_pep_exposure" in fact_ids
    
    # 驗證包含義務 ob_pep_prohibitions_gb
    ob_node = next(n for n in path.path_nodes if n.node_type == "obligation")
    assert ob_node.node_id == "ob_pep_prohibitions_gb"
    
    # 驗證包含條款 mock_policy_clause_02
    clause_node = next(n for n in path.path_nodes if n.node_type == "clause")
    assert clause_node.node_id == "mock_policy_clause_02"
    
    # 驗證 description 繁體中文內部政策論述
    assert "嚴禁為來自高風險管轄區" in path.description


def test_generate_audit_report():
    """
    驗證導出的 Markdown 審計軌跡報告格式正確。
    """
    raw_customers = load_yaml("customer_contexts.yaml")
    raw_obligations = load_yaml("obligations.yaml")
    raw_clauses = load_yaml("clauses.yaml")
    raw_documents = load_yaml("source_documents.yaml")
    raw_checklists = load_yaml("checklists.yaml")

    customers = [CustomerContext(**item) for item in raw_customers]
    obligations = [Obligation(**item) for item in raw_obligations]
    clauses = [Clause(**item) for item in raw_clauses]
    documents = [SourceDocument(**item) for item in raw_documents]
    checklists = [CDDChecklist(**item) for item in raw_checklists]

    cust_pep = next(c for c in customers if c.customer_id == "cust_individual_pep")
    chk_pep = next(k for k in checklists if k.customer_id == "cust_individual_pep")

    engine = ProvenanceEngine()
    
    path = engine.explain_item(
        checklist=chk_pep,
        target_item="Senior Management Approval Form",
        customer=cust_pep,
        obligations=obligations,
        clauses=clauses,
        documents=documents
    )

    # 產出報告
    report = engine.generate_audit_report([path])
    
    assert isinstance(report, str)
    assert "# CDD 合規決策審計軌跡報告" in report
    assert "### 🔍 檢核項目：Senior Management Approval Form" in report
    assert "➔" in report
    assert "> **發行機構與文件**" in report
    assert "> **原始明文引述**" in report
