import os
import yaml
from typing import List, Dict, Any
from src.contracts.models import CustomerContext, Obligation, Conflict, CDDChecklist
from src.decision.engine import CDDChecklistEngine, ChecklistEvaluator

# 定義黃金數據集與產出數據集目錄路徑
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


def test_cdd_checklist_engine_perfect_alignment():
    """
    驗證 CDDChecklistEngine 產出的 5 大經典客戶情境檢核表能與黃金 Expected Checklists 100% 完美對齊 (F1-score = 1.00)。
    並且驗證 ChecklistEvaluator 的評估指標計算正確。
    """
    # 1. 載入輸入與預期數據
    raw_customers = load_yaml("customer_contexts.yaml")
    raw_obligations = load_yaml("obligations.yaml")
    raw_conflicts = load_yaml("conflicts.yaml")
    expected_checklists = load_yaml("checklists.yaml")

    # 2. 實例化強型別模型
    customers = [CustomerContext(**item) for item in raw_customers]
    obligations = [Obligation(**item) for item in raw_obligations]
    conflicts = [Conflict(**item) for item in raw_conflicts]

    # 3. 執行決策推理引擎
    engine = CDDChecklistEngine()
    generated_checklists: List[CDDChecklist] = []

    for cust in customers:
        checklist = engine.generate_checklist(cust, obligations, conflicts)
        generated_checklists.append(checklist)
        
        # 驗證輸出物件是強型別
        assert isinstance(checklist, CDDChecklist)
        assert checklist.customer_id == cust.customer_id

    # 4. 驗證 5 大典型情境的細部精確匹配 (Exact Match)
    gen_dict = {chk.customer_id: chk for chk in generated_checklists}
    exp_dict = {exp["customer_id"]: exp for exp in expected_checklists}

    # 驗證客戶低風險個人情境 (chk_low_risk)
    chk_low = gen_dict["cust_individual_low_risk"]
    exp_low = exp_dict["cust_individual_low_risk"]
    assert chk_low.decision == exp_low["decision"]
    assert sorted(chk_low.required_documents) == sorted(exp_low["required_documents"])
    assert chk_low.risk_triggers == exp_low["risk_triggers"]
    assert sorted(chk_low.applicable_obligations) == sorted(exp_low["applicable_obligations"])
    assert chk_low.human_review_required == exp_low["human_review_required"]
    assert sorted(chk_low.citations) == sorted(exp_low["citations"])

    # 驗證企業標準情境 (chk_corp_standard)
    chk_corp = gen_dict["cust_corp_standard"]
    exp_corp = exp_dict["cust_corp_standard"]
    assert chk_corp.decision == exp_corp["decision"]
    assert sorted(chk_corp.required_documents) == sorted(exp_corp["required_documents"])
    assert chk_corp.risk_triggers == exp_corp["risk_triggers"]
    assert sorted(chk_corp.applicable_obligations) == sorted(exp_corp["applicable_obligations"])
    assert chk_corp.human_review_required == exp_corp["human_review_required"]
    assert sorted(chk_corp.citations) == sorted(exp_corp["citations"])

    # 驗證普通政要情境 (chk_individual_pep)
    chk_pep = gen_dict["cust_individual_pep"]
    exp_pep = exp_dict["cust_individual_pep"]
    assert chk_pep.decision == exp_pep["decision"]
    assert sorted(chk_pep.required_documents) == sorted(exp_pep["required_documents"])
    assert chk_pep.risk_triggers == exp_pep["risk_triggers"]
    assert sorted(chk_pep.applicable_obligations) == sorted(exp_pep["applicable_obligations"])
    assert chk_pep.human_review_required == exp_pep["human_review_required"]
    assert sorted(chk_pep.citations) == sorted(exp_pep["citations"])

    # 驗證高風險政要禁止開戶情境 (chk_individual_high_risk_pep)
    chk_hr_pep = gen_dict["cust_individual_high_risk_pep"]
    exp_hr_pep = exp_dict["cust_individual_high_risk_pep"]
    assert chk_hr_pep.decision == exp_hr_pep["decision"]
    assert sorted(chk_hr_pep.required_documents) == sorted(exp_hr_pep["required_documents"])
    assert chk_hr_pep.risk_triggers == exp_hr_pep["risk_triggers"]
    assert sorted(chk_hr_pep.applicable_obligations) == sorted(exp_hr_pep["applicable_obligations"])
    assert chk_hr_pep.human_review_required == exp_hr_pep["human_review_required"]
    assert sorted(chk_hr_pep.citations) == sorted(exp_hr_pep["citations"])

    # 驗證開曼 UBO 未明情境 (chk_corp_unclear_ubo)
    chk_unclear = gen_dict["cust_corp_unclear_ubo"]
    exp_unclear = exp_dict["cust_corp_unclear_ubo"]
    assert chk_unclear.decision == exp_unclear["decision"]
    assert sorted(chk_unclear.required_documents) == sorted(exp_unclear["required_documents"])
    assert chk_unclear.risk_triggers == exp_unclear["risk_triggers"]
    assert sorted(chk_unclear.applicable_obligations) == sorted(exp_unclear["applicable_obligations"])
    assert chk_unclear.human_review_required == exp_unclear["human_review_required"]
    assert sorted(chk_unclear.citations) == sorted(exp_unclear["citations"])

    # 5. 評量對齊指標
    evaluator = ChecklistEvaluator()
    metrics = evaluator.evaluate_alignment(generated_checklists, expected_checklists)
    
    assert metrics["precision"] == 1.00
    assert metrics["recall"] == 1.00
    assert metrics["f1_score"] == 1.00
    assert metrics["total_evaluated_fields"] == 30.0
    assert metrics["aligned_fields"] == 30.0

    # 6. 每個引用都是適用義務的錨點條文，且能在金標條文中找到
    clause_ids = {c["clause_id"] for c in load_yaml("clauses.yaml")}
    ob_dict = {ob.obligation_id: ob for ob in obligations}
    for chk in generated_checklists:
        anchors = [ob_dict[ob_id].source_clause_ids[0] for ob_id in chk.applicable_obligations]
        assert chk.citations == list(dict.fromkeys(anchors))
        assert set(chk.citations) <= clause_ids


def test_unadjudicated_conflict_forces_human_review():
    """
    衝突若沒有人工裁決紀錄（pending_human_review），所有依賴相關義務的清單都要列出該衝突並送人工審查。
    """
    customers = {c["customer_id"]: CustomerContext(**c) for c in load_yaml("customer_contexts.yaml")}
    obligations = [Obligation(**item) for item in load_yaml("obligations.yaml")]
    conflicts = [Conflict(**item) for item in load_yaml("conflicts.yaml")]
    pending = [c.model_copy(update={"adjudication_status": "pending_human_review", "resolved_by": None})
               if c.conflict_id == "conf_occasional_threshold" else c for c in conflicts]

    engine = CDDChecklistEngine()
    low_risk = customers["cust_individual_low_risk"]

    resolved_chk = engine.generate_checklist(low_risk, obligations, conflicts)
    assert resolved_chk.unresolved_conflicts == []
    assert resolved_chk.human_review_required is False

    pending_chk = engine.generate_checklist(low_risk, obligations, pending)
    assert pending_chk.unresolved_conflicts == ["conf_occasional_threshold"]
    assert pending_chk.human_review_required is True
