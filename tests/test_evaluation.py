import os
import yaml
from typing import List, Dict, Any, Set
from src.contracts.models import (
    CustomerContext,
    CDDChecklist,
    Obligation,
    Conflict,
    EvaluationMetrics,
    DiagnosticReport,
    ComparisonReport,
    Clause
)
from src.decision.engine import CDDChecklistEngine
from src.evaluation.baseline import VectorRAGBaseline
from src.evaluation.harness import EvaluationHarness

GOLD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/gold"))
PROCESSED_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/processed"))


def load_yaml(filename: str, dir_path: str = GOLD_DIR) -> List[Dict[str, Any]]:
    file_path = os.path.join(dir_path, filename)
    assert os.path.exists(file_path), f"YAML 檔案不存在: {file_path}"
    with open(file_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert isinstance(data, list), f"YAML 檔案格式不符合列表規範: {filename}"
    return data


def test_evaluation_metrics_calculation():
    """
    測試 EvaluationHarness 中各種指標計算的正確性。
    """
    harness = EvaluationHarness()

    # 1. 測試 Retrieval 指標
    pred_cits = ["MAS Notice 626 Paragraph 6.2", "MAS Notice 626 Paragraph 6.66"]
    gold_cits = ["MAS Notice 626 Paragraph 6.2", "MAS Notice 626 Paragraph 6.6"]
    metrics_ret = harness.evaluate_retrieval(pred_cits, gold_cits)
    
    assert metrics_ret.precision == 0.50
    assert metrics_ret.recall == 0.50
    assert metrics_ret.f1_score == 0.50
    assert metrics_ret.accuracy == 0.3333

    # 2. 測試 Extraction 指標
    gold_ob = Obligation(
        obligation_id="ob1",
        source_clause_ids=["c1"],
        jurisdiction="Singapore",
        actor="bank",
        action="verify",
        object="customer",
        required_evidence=["NRIC"],
        confidence=1.0
    )
    pred_ob_correct = Obligation(
        obligation_id="ob1",
        source_clause_ids=["c1"],
        jurisdiction="Singapore",
        actor="bank",
        action="verify",
        object="customer",
        required_evidence=["NRIC"],
        confidence=1.0
    )
    # required_evidence 缺失，且 actor 不對
    pred_ob_incorrect = Obligation(
        obligation_id="ob1",
        source_clause_ids=["c1"],
        jurisdiction="Singapore",
        actor="customer",
        action="verify",
        object="customer",
        required_evidence=[],
        confidence=0.8
    )

    metrics_ext_perfect = harness.evaluate_extraction([pred_ob_correct], [gold_ob])
    assert metrics_ext_perfect.precision == 1.0
    assert metrics_ext_perfect.recall == 1.0
    assert metrics_ext_perfect.f1_score == 1.0

    metrics_ext_bad = harness.evaluate_extraction([pred_ob_incorrect], [gold_ob])
    # actor 錯, action 對, object 對, required_evidence 錯 ➔ 2/4 = 50%
    assert metrics_ext_bad.precision == 0.5
    assert metrics_ext_bad.recall == 0.5

    # 3. 測試 Conflict Detection 指標
    c1 = Conflict(conflict_id="c1", conflict_type="Temporal", source_clause_ids=["a"], verifiability="retrieval-verifiable", description="desc", adjudication_status="pending_human_review")
    metrics_conf = harness.evaluate_conflict_detection([c1], [c1])
    assert metrics_conf.precision == 1.0
    assert metrics_conf.recall == 1.0


def test_citation_faithfulness_and_hallucination():
    """
    測試引用忠實度與幻覺檢測機制。
    """
    harness = EvaluationHarness()

    valid_cits: Set[str] = {
        "MAS Notice 626 Paragraph 6.2",
        "MAS Notice 626 Paragraph 6.6",
        "MAS Notice 626 Paragraph 6.13",
        "MAS Notice 626 Paragraph 7.2",
        "Global Bank Policy Section 3.2.1",
        "Global Bank Policy Section 4.5.3",
        "FATF Recommendation 10, P3"
    }

    chk_faithful = CDDChecklist(
        checklist_id="chk1",
        customer_id="cust1",
        decision="standard_cdd",
        required_documents=["NRIC"],
        risk_triggers=[],
        applicable_obligations=[],
        unresolved_conflicts=[],
        human_review_required=False,
        citations=["MAS Notice 626 Paragraph 6.2"]
    )

    chk_hallucinated = CDDChecklist(
        checklist_id="chk2",
        customer_id="cust2",
        decision="standard_cdd",
        required_documents=["NRIC"],
        risk_triggers=[],
        applicable_obligations=[],
        unresolved_conflicts=[],
        human_review_required=False,
        citations=["MAS Notice 626 Paragraph 99.9"]  # Hallucinated!
    )

    faith_rate_perfect = harness.check_citation_faithfulness(valid_cits, [chk_faithful])
    assert faith_rate_perfect == 1.0

    faith_rate_bad = harness.check_citation_faithfulness(valid_cits, [chk_hallucinated])
    assert faith_rate_bad == 0.0

    faith_rate_mix = harness.check_citation_faithfulness(valid_cits, [chk_faithful, chk_hallucinated])
    assert faith_rate_mix == 0.5


def test_decoupled_diagnostic_tree():
    """
    驗證解耦式錯誤歸因診斷樹。針對各種漏條款、漏屬性、漏衝突與邏輯錯進行測試。
    """
    harness = EvaluationHarness()

    valid_cits: Set[str] = {"MAS Notice 626 Paragraph 6.2"}
    
    gold_chk = CDDChecklist(
        checklist_id="chk1",
        customer_id="cust1",
        decision="enhanced_due_diligence",
        required_documents=["Senior Management Approval Form", "NRIC"],
        risk_triggers=["pep_exposure_detected"],
        applicable_obligations=["ob_pep_edd_mas"],
        unresolved_conflicts=[],
        human_review_required=True,
        citations=["MAS Notice 626 Paragraph 6.2"]
    )

    # 1. 測試完美吻合
    report_ok = harness.run_diagnostic_tree(gold_chk, gold_chk, valid_cits, [], [])
    assert not report_ok.has_error
    assert report_ok.error_source is None

    # 2. 測試 Conflict Handling 錯誤
    pred_conflict = CDDChecklist(
        checklist_id="chk1",
        customer_id="cust1",
        decision="standard_cdd",
        required_documents=["NRIC"],
        risk_triggers=[],
        applicable_obligations=[],
        unresolved_conflicts=["conflict1"], # 不匹配
        human_review_required=False,
        citations=["MAS Notice 626 Paragraph 6.2"]
    )
    report_conf = harness.run_diagnostic_tree(pred_conflict, gold_chk, valid_cits, [], [])
    assert report_conf.has_error
    assert report_conf.error_source == "conflict_handling"

    # 3. 測試 Retrieval 錯誤
    pred_retrieval = CDDChecklist(
        checklist_id="chk1",
        customer_id="cust1",
        decision="standard_cdd",
        required_documents=["NRIC"],
        risk_triggers=[],
        applicable_obligations=[],
        unresolved_conflicts=[],
        human_review_required=False,
        citations=[]  # 漏了 MAS Notice 626 Paragraph 6.2
    )
    report_ret = harness.run_diagnostic_tree(pred_retrieval, gold_chk, valid_cits, [], [])
    assert report_ret.has_error
    assert report_ret.error_source == "retrieval"

    # 4. 測試 Extraction 錯誤
    pred_extraction_missing_ob = CDDChecklist(
        checklist_id="chk1",
        customer_id="cust1",
        decision="enhanced_due_diligence",
        required_documents=["NRIC"], # 漏了 Senior Management Approval Form
        risk_triggers=["pep_exposure_detected"],
        applicable_obligations=["ob_pep_edd_mas"],
        unresolved_conflicts=[],
        human_review_required=True,
        citations=["MAS Notice 626 Paragraph 6.2"]
    )
    # Extracted obligations 為空，漏了 ob_pep_edd_mas
    report_ext_missing = harness.run_diagnostic_tree(
        pred_extraction_missing_ob,
        gold_chk,
        valid_cits,
        [],  # 漏了 obligation
        []
    )
    assert report_ext_missing.has_error
    assert report_ext_missing.error_source == "extraction"

    # 測試 Extractor 屬性不足 (required_evidence 缺漏)
    ob_missing_evidence = Obligation(
        obligation_id="ob_pep_edd_mas",
        source_clause_ids=["c1"],
        jurisdiction="Singapore",
        actor="bank",
        action="verify",
        object="pep",
        required_evidence=[], # 漏了 evidence
        confidence=1.0
    )
    report_ext_attr = harness.run_diagnostic_tree(
        pred_extraction_missing_ob,
        gold_chk,
        valid_cits,
        [ob_missing_evidence],
        []
    )
    assert report_ext_attr.has_error
    assert report_ext_attr.error_source == "extraction"

    # 5. 測試 Graph Modeling 錯誤
    # 針對 corp standard，觸發內部持股 >=10% 閥值限制
    gold_corp = CDDChecklist(
        checklist_id="chk_corp",
        customer_id="cust_corp",
        decision="standard_cdd",
        required_documents=["ACRA Profile", "Shareholder NRIC"],
        risk_triggers=["internal_ubo_threshold_triggered_10_percent"],
        applicable_obligations=["ob_identify_ubo_10_gb"],
        unresolved_conflicts=[],
        human_review_required=True,
        citations=["MAS Notice 626 Paragraph 6.13"]
    )
    pred_corp_graph_err = CDDChecklist(
        checklist_id="chk_corp",
        customer_id="cust_corp",
        decision="standard_cdd",
        required_documents=["ACRA Profile"], # 漏了文件
        risk_triggers=[], # 漏了 risk trigger!
        applicable_obligations=["ob_identify_ubo_10_gb"],
        unresolved_conflicts=[],
        human_review_required=False,
        citations=["MAS Notice 626 Paragraph 6.13"]
    )
    report_graph = harness.run_diagnostic_tree(
        pred_corp_graph_err,
        gold_corp,
        {"MAS Notice 626 Paragraph 6.13"},
        [Obligation(obligation_id="ob_identify_ubo_10_gb", source_clause_ids=["c1"], jurisdiction="Singapore", actor="bank", action="verify", object="ubo", required_evidence=["Shareholder NRIC"], confidence=1.0)],
        []
    )
    assert report_graph.has_error
    assert report_graph.error_source == "graph_modeling"

    # 6. 測試 Reasoning 錯誤
    pred_reasoning = CDDChecklist(
        checklist_id="chk1",
        customer_id="cust1",
        decision="standard_cdd",  # 決策錯了，應為 enhanced_due_diligence
        required_documents=["Senior Management Approval Form", "NRIC"],
        risk_triggers=["pep_exposure_detected"],
        applicable_obligations=["ob_pep_edd_mas"],
        unresolved_conflicts=[],
        human_review_required=True,
        citations=["MAS Notice 626 Paragraph 6.2"]
    )
    report_reason = harness.run_diagnostic_tree(
        pred_reasoning,
        gold_chk,
        valid_cits,
        [Obligation(obligation_id="ob_pep_edd_mas", source_clause_ids=["c1"], jurisdiction="Singapore", actor="bank", action="verify", object="pep", required_evidence=["Senior Management Approval Form"], confidence=1.0)],
        []
    )
    assert report_reason.has_error
    assert report_reason.error_source == "reasoning"


def test_comparison_report_generation():
    """
    驗證一鍵生成系統與對照組的 Comparison Report。
    並且斷言 CDD-GraphWiki 在決策準確度與引用忠實性上都完勝 VectorRAGBaseline。
    """
    raw_customers = load_yaml("customer_contexts.yaml")
    raw_obligations = load_yaml("obligations.yaml")
    raw_conflicts = load_yaml("conflicts.yaml")
    raw_gold_checklists = load_yaml("checklists.yaml")
    raw_clauses = load_yaml("clauses.yaml")

    customers = [CustomerContext(**item) for item in raw_customers]
    obligations = [Obligation(**item) for item in raw_obligations]
    conflicts = [Conflict(**item) for item in raw_conflicts]
    gold_checklists = [CDDChecklist(**item) for item in raw_gold_checklists]

    # 收集 valid citations 集合
    valid_cits: Set[str] = set()
    for c in raw_clauses:
        valid_cits.add(c["section_ref"])
        if "citations" in c and c["citations"]:
            for cit in c["citations"]:
                valid_cits.add(cit)
    
    # 也加入 mock 內部政策引用
    valid_cits.add("Global Bank Policy Section 3.2.1")
    valid_cits.add("Global Bank Policy Section 4.5.3")

    # 1. 運行推理系統
    engine = CDDChecklistEngine()
    cdd_checklists = [engine.generate_checklist(c, obligations, conflicts) for c in customers]

    # 2. 運行對照組 (VectorRAGBaseline)
    baseline = VectorRAGBaseline()
    base_checklists = [baseline.generate_checklist(c) for c in customers]

    # 3. 實例化 Harness 並產出 Comparison Report
    harness = EvaluationHarness()
    report = harness.generate_comparison_report(
        cdd_checklists,
        base_checklists,
        gold_checklists,
        valid_cits,
        obligations,
        conflicts
    )

    assert isinstance(report, ComparisonReport)

    # 4. 斷言 CDD-GraphWiki 指標完勝 Baseline
    cdd_wiki_check_metrics = report.cdd_wiki_metrics["checklist"]
    base_check_metrics = report.baseline_metrics["checklist"]

    cdd_wiki_faith = report.cdd_wiki_metrics["citation_faithfulness"].accuracy
    base_faith = report.baseline_metrics["citation_faithfulness"].accuracy

    # 系統決策完美對齊（F1 = 1.0），而 Baseline 有嚴重錯誤（錯判 corporate 且漏判 UBO）
    assert cdd_wiki_check_metrics.f1_score == 1.0
    assert base_check_metrics.f1_score < 1.0

    # 系統 citations 100% 忠實無幻覺，而 Baseline 含有嚴重幻覺 citations！
    assert cdd_wiki_faith == 1.0
    assert base_faith < 1.0

    # 5. 輸出報告結果以進行 manual verification
    print("\n================ EVALUATION COMPARISON REPORT ================")
    print(f"CDD-GraphWiki Checklist Accuracy: {cdd_wiki_check_metrics.accuracy * 100:.2f}%")
    print(f"Vector-RAG Baseline Checklist Accuracy: {base_check_metrics.accuracy * 100:.2f}%")
    print(f"CDD-GraphWiki Citation Faithfulness (Anti-hallucination): {cdd_wiki_faith * 100:.2f}%")
    print(f"Vector-RAG Baseline Citation Faithfulness (Anti-hallucination): {base_faith * 100:.2f}%")
    print("==============================================================")
