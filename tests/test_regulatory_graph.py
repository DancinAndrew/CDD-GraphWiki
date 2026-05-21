import os
import yaml
import tempfile
from typing import List, Dict, Any
from src.contracts.models import (
    CustomerContext,
    Obligation,
    Clause,
    SourceDocument,
    CDDChecklist,
    ExplanationPath,
    GraphNode,
    GraphEdge,
    RegulatoryGraph
)
from src.decision.provenance import ProvenanceEngine
from src.graph.builder import GraphBuilder, GraphQuery
from src.graph.visualization import GraphExporter

# 定義目錄路徑
GOLD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/gold"))


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


def test_regulatory_graph_build_and_weave():
    """
    測試從金標數據構建圖譜，並將決策路徑 (Decision Weaving) 織入高亮標記的完整流程。
    """
    # 1. 載入金標資料
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

    # 取出普通政要個人，利用 ProvenanceEngine 產生 ExplanationPath
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

    # 2. 構建圖譜並將 ExplanationPath 織入
    graph = GraphBuilder.build_regulatory_graph(
        documents=documents,
        clauses=clauses,
        obligations=obligations,
        concepts=[],
        conflicts=[],
        customers=customers,
        checklists=checklists,
        paths=[path]
    )

    assert isinstance(graph, RegulatoryGraph)
    # 驗證節點存在性
    assert "mas_notice_626" in graph.nodes
    assert "mas626_clause_04" in graph.nodes
    assert "ob_pep_edd_mas" in graph.nodes
    assert "cust_individual_pep" in graph.nodes
    assert "chk_individual_pep" in graph.nodes

    # 驗證 EvidenceRequirement 和 RiskTrigger 節點被動態提取建立
    assert "senior_management_approval" in graph.nodes
    assert "pep_without_senior_mgmt_signoff" in graph.nodes
    assert graph.nodes["senior_management_approval"].node_type == "EvidenceRequirement"
    assert graph.nodes["pep_without_senior_mgmt_signoff"].node_type == "RiskTrigger"

    # 驗證邊關係連接正確
    derived_edge = next(e for e in graph.edges if e.source_id == "mas626_clause_04" and e.target_id == "mas_notice_626")
    assert derived_edge.edge_type == "derived_from"

    requires_edge = next(e for e in graph.edges if e.source_id == "ob_pep_edd_mas" and e.target_id == "senior_management_approval")
    assert requires_edge.edge_type == "requires_evidence"

    # 3. 驗證 Weaving 特效：對應決策路徑節點與邊的 decision_path 是否為 True
    assert graph.nodes["mas626_clause_04"].properties["decision_path"] is True
    assert graph.nodes["mas_notice_626"].properties["decision_path"] is True
    
    # 驗證決策標記邊
    active_edge = next(e for e in graph.edges if e.source_id == "ob_pep_edd_mas" and e.target_id == "mas626_clause_04")
    assert active_edge.properties["decision_path"] is True
    assert active_edge.properties["decision_target"] == "Senior Management Approval Form"


def test_regulatory_graph_multi_hop_query():
    """
    測試在合規圖譜上進行多步關係查詢 (Multi-hop Query) 與上下游追溯。
    """
    raw_customers = load_yaml("customer_contexts.yaml")
    raw_obligations = load_yaml("obligations.yaml")
    raw_clauses = load_yaml("clauses.yaml")
    raw_documents = load_yaml("source_documents.yaml")

    customers = [CustomerContext(**item) for item in raw_customers]
    obligations = [Obligation(**item) for item in raw_obligations]
    clauses = [Clause(**item) for item in raw_clauses]
    documents = [SourceDocument(**item) for item in raw_documents]

    graph = GraphBuilder.build_regulatory_graph(
        documents=documents,
        clauses=clauses,
        obligations=obligations,
        concepts=[],
        conflicts=[],
        customers=customers
    )

    # 1. 測試從特定的義務出發，進行 2 步多步遍歷
    paths_from_ob = GraphQuery.find_multi_hop_paths(
        graph=graph,
        start_node_id="ob_pep_edd_mas",
        max_depth=2,
        ignore_direction=True
    )

    # 必須能遍歷到 Clause 和 EvidenceRequirement 等鄰近節點
    assert len(paths_from_ob) > 0
    # 檢驗是否有包含 "Senior Management Approval Form" 的路徑
    has_evidence_path = False
    for p in paths_from_ob:
        node_ids = [n.node_id for n in p]
        if "senior_management_approval" in node_ids:
            has_evidence_path = True
    assert has_evidence_path is True

    # 2. 測試追溯上游與下游
    # 義務 ob_pep_edd_mas 的上游應該有條款 mas626_clause_04
    upstream = GraphQuery.get_upstream_sources(graph, "ob_pep_edd_mas")
    upstream_ids = [n.node_id for n in upstream]
    assert "mas626_clause_04" in upstream_ids

    # 條款 mas626_clause_04 的下游應該有義務 ob_pep_edd_mas
    downstream = GraphQuery.get_downstream_targets(graph, "mas626_clause_04")
    downstream_ids = [n.node_id for n in downstream]
    assert "ob_pep_edd_mas" in downstream_ids


def test_interactive_html_visualization_export():
    """
    測試可視化導出器能成功生成結構完整且包含 Vanilla CSS 暗黑玻璃美學設計的 HTML 檔案。
    """
    raw_customers = load_yaml("customer_contexts.yaml")
    raw_obligations = load_yaml("obligations.yaml")
    raw_clauses = load_yaml("clauses.yaml")
    raw_documents = load_yaml("source_documents.yaml")

    customers = [CustomerContext(**item) for item in raw_customers]
    obligations = [Obligation(**item) for item in raw_obligations]
    clauses = [Clause(**item) for item in raw_clauses]
    documents = [SourceDocument(**item) for item in raw_documents]

    graph = GraphBuilder.build_regulatory_graph(
        documents=documents,
        clauses=clauses,
        obligations=obligations,
        concepts=[],
        conflicts=[],
        customers=customers
    )

    # 在臨時目錄中生成測試 HTML
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_graph.html")
        GraphExporter.export_to_html(graph, output_path)

        assert os.path.exists(output_path)
        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 驗證 HTML 的關鍵要素與 Vanilla CSS 磨砂玻璃擬物屬性面板完整無缺
        assert "<!DOCTYPE html>" in content
        assert "d3.v7.min.js" in content
        assert "const graphData = {" in content
        assert "backdrop-filter: blur(16px)" in content
        assert "linear-gradient(135deg," in content
        assert "ob_pep_edd_mas" in content
        assert "arrow-normal" in content
