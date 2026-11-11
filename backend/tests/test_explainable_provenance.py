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
    
    # 事實節點就是決策路徑讀到的屬性（每個屬性一個），附讀到的值
    fact_nodes = {n.node_id: n for n in path.path_nodes if n.node_type == "customer_fact"}
    assert list(fact_nodes) == [
        "fact_customer_type", "fact_pep_exposure", "fact_ubo_country_risk", "fact_registration_jurisdiction"
    ]
    assert path.path_nodes[0].node_type == "customer_fact"
    assert fact_nodes["fact_pep_exposure"].properties["pep_exposure"] is True
    assert fact_nodes["fact_ubo_country_risk"].properties["ubo_country_risk"] == "low"
    
    # 驗證包含義務 ob_pep_edd_mas 節點
    ob_node = next(n for n in path.path_nodes if n.node_type == "obligation")
    assert ob_node.node_id == "ob_pep_edd_mas"
    
    # 驗證包含 MAS Notice 626 第 8.3 段節點，並逐字引述官方原文
    clause_node = next(n for n in path.path_nodes if n.node_type == "clause")
    assert clause_node.node_id == "mas_notice_626_8_enhanced_cdd_8_3"
    assert "perform at least the following enhanced CDD measures where a customer or any beneficial owner" in clause_node.properties["raw_text"]

    
    # 驗證包含源文件 mas_notice_626
    doc_node = path.path_nodes[-1]
    assert doc_node.node_type == "document"
    assert doc_node.node_id == "mas_notice_626"
    assert doc_node.properties["issuer"] == "MAS"
    
    # description 由路徑、葉節點、義務與條文產生：必須含有這些事實
    assert "pep_exposure = True" in path.description
    assert "ubo_country_risk = low" in path.description
    assert "individual_pep" in path.description
    assert "ob_pep_edd_mas" in path.description
    assert "8.3" in path.description
    assert doc_node.properties["title"] in path.description


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
    
    # 驗證包含銀行政策 1.4（禁止高風險國家 PEP）條文
    clause_node = next(n for n in path.path_nodes if n.node_type == "clause")
    assert clause_node.node_id == "mock_internal_policy_s_1_customer_onboarding_standards_1_4_politically_exposed_persons"
    assert "strictly prohibits" in clause_node.properties["raw_text"]
    
    fact_nodes = {n.node_id: n for n in path.path_nodes if n.node_type == "customer_fact"}
    assert fact_nodes["fact_registration_jurisdiction"].properties["registration_jurisdiction"] == "Myanmar"
    assert fact_nodes["fact_ubo_country_risk"].properties["ubo_country_risk"] == "high"

    # description 含有路徑上的事實、分支、義務與條文
    assert "ubo_country_risk = high" in path.description
    assert "registration_jurisdiction = Myanmar" in path.description
    assert "individual_pep_high_risk" in path.description
    assert "ob_pep_prohibitions_gb" in path.description
    assert "1.4 Politically Exposed Persons" in path.description


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


def test_explain_unclear_ubo_rejection_uses_mas_6_35():
    """
    UBO 不明的開曼企業：拒絕開戶通知要追溯到 MAS Notice 626 第 6.35 段
    （無法完成 CDD 時不得建立業務關係並考慮申報 STR），而不是舊版誤植的「MAS 25%」條文。
    """
    customers = [CustomerContext(**item) for item in load_yaml("customer_contexts.yaml")]
    obligations = [Obligation(**item) for item in load_yaml("obligations.yaml")]
    clauses = [Clause(**item) for item in load_yaml("clauses.yaml")]
    documents = [SourceDocument(**item) for item in load_yaml("source_documents.yaml")]
    checklists = [CDDChecklist(**item) for item in load_yaml("checklists.yaml")]

    cust = next(c for c in customers if c.customer_id == "cust_corp_unclear_ubo")
    chk = next(k for k in checklists if k.customer_id == "cust_corp_unclear_ubo")
    path = ProvenanceEngine().explain_item(
        checklist=chk, target_item="Account Opening Rejection Notice", customer=cust,
        obligations=obligations, clauses=clauses, documents=documents)

    ob_node = next(n for n in path.path_nodes if n.node_type == "obligation")
    clause_node = next(n for n in path.path_nodes if n.node_type == "clause")
    assert ob_node.node_id == "ob_cdd_incomplete_mas"
    assert clause_node.node_id == "mas_notice_626_6_cdd_6_35"
    assert "shall not commence or continue business relations" in clause_node.properties["raw_text"]
    assert "ubo_status = unclear" in path.description
    # 註冊地不再是「CDD 無法完成」的條件：路徑只因 UBO 不明而拒絕
    assert "registration_jurisdiction" not in path.description
    assert "corporate_cdd_incomplete" in path.description
    assert "6.35" in path.description
    assert path.path_nodes[-1].node_id == "mas_notice_626"


def _gold_inputs(customer_id: str):
    customers = [CustomerContext(**item) for item in load_yaml("customer_contexts.yaml")]
    checklists = [CDDChecklist(**item) for item in load_yaml("checklists.yaml")]
    return (
        next(c for c in customers if c.customer_id == customer_id),
        next(k for k in checklists if k.customer_id == customer_id),
        [Obligation(**item) for item in load_yaml("obligations.yaml")],
        [Clause(**item) for item in load_yaml("clauses.yaml")],
        [SourceDocument(**item) for item in load_yaml("source_documents.yaml")],
    )


def test_every_item_maps_to_the_obligation_its_branch_declares():
    """每個文件都對應葉節點宣告的義務；同一義務的不同文件指向同一錨點條文。"""
    from src.decision.engine import route
    for customer_id in ["cust_individual_low_risk", "cust_corp_standard", "cust_individual_pep",
                        "cust_individual_high_risk_pep", "cust_corp_unclear_ubo"]:
        cust, chk, obligations, clauses, documents = _gold_inputs(customer_id)
        leaf, _ = route(cust)
        ob_dict = {ob.obligation_id: ob for ob in obligations}
        for document, ob_id in leaf.items:
            path = ProvenanceEngine().explain_item(chk, document, cust, obligations, clauses, documents)
            ob_node = next(n for n in path.path_nodes if n.node_type == "obligation")
            clause_node = next(n for n in path.path_nodes if n.node_type == "clause")
            assert ob_node.node_id == ob_id
            assert clause_node.node_id == ob_dict[ob_id].source_clause_ids[0]


def _with_pct(cust, chk, obligations, clauses, documents, target_item):
    """企業標準客戶加上 15% 主要股東：落在內部 10% 門檻分支。"""
    from src.decision.engine import CDDChecklistEngine
    corp = cust.model_copy(update={"ubo_status": "identified", "registration_jurisdiction": "Singapore",
                                   "custom_attributes": {"major_shareholder_pct": 15}})
    checklist = CDDChecklistEngine().generate_checklist(corp, obligations, [])
    assert target_item in checklist.risk_triggers
    return checklist, target_item, corp, obligations, clauses, documents


def test_risk_trigger_reports_how_it_was_checked():
    """complex_ownership_3_layers 斷言的是 ownership_layers；UBO 不明的路徑沒有讀它，由標記自己的條件檢查，
    description 要說出條件與讀到的值，並為這個屬性加上事實節點。"""
    cust, chk, obligations, clauses, documents = _gold_inputs("cust_corp_unclear_ubo")
    path = ProvenanceEngine().explain_item(chk, "complex_ownership_3_layers", cust, obligations, clauses, documents)
    assert "決策路徑沒有讀 ownership_layers，由標記自己的條件 ownership_layers >= 3 檢查（ownership_layers = 5）" in path.description
    fact = next(n for n in path.path_nodes if n.node_id == "fact_ownership_layers")
    assert fact.properties["ownership_layers"] == 5 and fact.properties["trigger_condition"] == "ownership_layers >= 3"
    # 標記宣告的義務：銀行政策 1.2(b) 的多層持股條件；條文節點是寫出條件的 1.2(b)，不是義務的錨點 1.2
    assert next(n for n in path.path_nodes if n.node_type == "obligation").node_id == "ob_identify_ubo_10_gb"
    clause_node = next(n for n in path.path_nodes if n.node_type == "clause")
    assert clause_node.node_id.endswith("_1_2_beneficial_ownership_verification_b")
    assert "three or more layers of intermediary holding companies" in clause_node.properties["raw_text"]
    assert "寫出這個條件的條文為" in path.description and "1.2 Beneficial Ownership Verification > (b)" in path.description

    path = ProvenanceEngine().explain_item(
        *_with_pct(cust, chk, obligations, clauses, documents, "internal_ubo_threshold_triggered_10_percent"))
    clause_node = next(n for n in path.path_nodes if n.node_type == "clause")
    assert clause_node.node_id.endswith("_1_2_beneficial_ownership_verification_a")
    assert "ownership threshold of 10% or more" in clause_node.properties["raw_text"]


def test_risk_trigger_uses_the_obligation_it_declares():
    """風險標記追溯到 TriggerSpec 宣告的義務，而不是分支裡第一份非基本文件的義務。"""
    cust, chk, obligations, clauses, documents = _gold_inputs("cust_corp_unclear_ubo")
    path = ProvenanceEngine().explain_item(chk, "unclear_ubo_status", cust, obligations, clauses, documents)
    ob_node = next(n for n in path.path_nodes if n.node_type == "obligation")
    clause_node = next(n for n in path.path_nodes if n.node_type == "clause")
    assert ob_node.node_id == "ob_cdd_incomplete_mas"
    assert clause_node.node_id == "mas_notice_626_6_cdd_6_35"
    assert "葉節點宣告它依據義務 ob_cdd_incomplete_mas" in path.description
    assert "已在決策路徑上檢驗" in path.description

    cust, chk, obligations, clauses, documents = _gold_inputs("cust_individual_pep")
    path = ProvenanceEngine().explain_item(chk, "pep_exposure_detected", cust, obligations, clauses, documents)
    assert next(n for n in path.path_nodes if n.node_type == "obligation").node_id == "ob_pep_edd_mas"


def test_risk_trigger_that_does_not_hold_is_rejected():
    """清單和客戶資料對不上（舊清單列了多層持股，但客戶只有 2 層）：不替不成立的標記編造解釋。"""
    import pytest
    cust, chk, obligations, clauses, documents = _gold_inputs("cust_corp_unclear_ubo")
    assert "complex_ownership_3_layers" in chk.risk_triggers
    two_layers = cust.model_copy(update={"ownership_layers": 2})
    with pytest.raises(ValueError, match="does not hold"):
        ProvenanceEngine().explain_item(chk, "complex_ownership_3_layers", two_layers, obligations, clauses, documents)


def test_pep_missing_source_of_funds_traces_to_mas_8_3_b():
    """PEP 缺少資金來源證明：標記追溯到 MAS 8.3(b)，事實節點是 source_of_funds_available。"""
    from src.decision.engine import CDDChecklistEngine
    cust, _, obligations, clauses, documents = _gold_inputs("cust_individual_pep")
    cust = cust.model_copy(update={"source_of_funds_available": False})
    chk = CDDChecklistEngine().generate_checklist(cust, obligations, [])
    assert chk.risk_triggers == ["pep_exposure_detected", "missing_source_of_funds_evidence"]
    path = ProvenanceEngine().explain_item(chk, "missing_source_of_funds_evidence", cust, obligations, clauses, documents)
    assert next(n for n in path.path_nodes if n.node_type == "obligation").node_id == "ob_pep_edd_mas"
    clause_node = next(n for n in path.path_nodes if n.node_type == "clause")
    assert clause_node.node_id == "mas_notice_626_8_enhanced_cdd_8_3_b"
    assert "source of wealth and source of funds" in clause_node.properties["raw_text"]
    assert "fact_source_of_funds_available" in [n.node_id for n in path.path_nodes]


def test_item_not_in_checklist_is_rejected():
    import pytest
    cust, chk, obligations, clauses, documents = _gold_inputs("cust_individual_low_risk")
    with pytest.raises(ValueError):
        ProvenanceEngine().explain_item(chk, "Senior Management Approval Form", cust, obligations, clauses, documents)
