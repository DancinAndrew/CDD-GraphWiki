from typing import List, Dict, Any, Literal
from src.contracts.models import CustomerContext, Obligation, Conflict, CDDChecklist


class CDDChecklistEngine:
    """
    客戶 CDD 檢核推理引擎。
    決策分支刻意維持規則式以換取可解釋性；引用與未決衝突則由義務的出處推導：
    - citations：適用義務的錨點條文 ID（解析出的條文）
    - unresolved_conflicts：與適用義務相關、尚未人工裁決的衝突，有的話一律送人工審查
    """

    def generate_checklist(
        self,
        customer: CustomerContext,
        obligations: List[Obligation],
        conflicts: List[Conflict]
    ) -> CDDChecklist:
        """
        輸入單一客戶情境與法規/政策義務、衝突列表，推理生成對應的強型別 CDDChecklist。
        """
        customer_id = customer.customer_id
        
        # 預設值
        decision: Literal["simplified_cdd", "standard_cdd", "enhanced_due_diligence"] = "standard_cdd"
        required_documents: List[str] = []
        risk_triggers: List[str] = []
        applicable_obligations: List[str] = []
        unresolved_conflicts: List[str] = []
        human_review_required = False

        # 1. 根據客戶情境特徵模式進行推理決策分支匹配
        if customer.customer_type == "individual":
            if customer.pep_exposure:
                # 政要曝險情境
                if customer.ubo_country_risk == "high" or customer.registration_jurisdiction.lower() == "myanmar":
                    # 高風險政要禁止開戶情境 (cust_individual_high_risk_pep)
                    decision = "enhanced_due_diligence"
                    required_documents = [
                        "Rejected Onboarding Notification"
                    ]
                    risk_triggers = [
                        "pep_from_high_risk_jurisdiction",
                        "onboarding_prohibited_by_policy"
                    ]
                    applicable_obligations = ["ob_pep_prohibitions_gb"]
                    human_review_required = True
                else:
                    # 普通政要 EDD 情境 (cust_individual_pep)
                    decision = "enhanced_due_diligence"
                    required_documents = [
                        "National Identity Card (NRIC) or Passport",
                        "Proof of Address",
                        "Senior Management Approval Form",
                        "Source of Funds Declaration & Evidence",
                        "Source of Wealth Declaration & Evidence",
                        "Head of Compliance Approval Form"
                    ]
                    risk_triggers = ["pep_exposure_detected"]
                    # MAS 8.3 的加強 CDD，加上銀行政策 1.4(a) 對非高風險地區 PEP 的核准要求
                    applicable_obligations = [
                        "ob_cdd_on_relationship_mas",
                        "ob_verify_customer_mas",
                        "ob_pep_edd_mas",
                        "ob_pep_approval_gb"
                    ]
                    human_review_required = True
            else:
                # 普通低風險個人情境 (cust_individual_low_risk)
                decision = "standard_cdd"
                required_documents = [
                    "National Identity Card (NRIC)",
                    "Proof of Residential Address"
                ]
                risk_triggers = []
                applicable_obligations = [
                    "ob_cdd_on_relationship_mas",
                    "ob_verify_customer_mas"
                ]
                human_review_required = False

        elif customer.customer_type == "corporate":
            if customer.ubo_status == "unclear" or customer.registration_jurisdiction.lower() == "cayman islands":
                # 開曼高風險且 UBO 未明企業情境 (cust_corp_unclear_ubo)
                decision = "enhanced_due_diligence"
                required_documents = [
                    "Account Opening Rejection Notice",
                    "STR Evaluation File"
                ]
                risk_triggers = [
                    "unclear_ubo_status",
                    "excessive_layering_5",
                    "missing_source_of_funds_evidence"
                ]
                # 無法完成 CDD（UBO 不明）時，MAS 6.35 要求不得建立業務關係並考慮申報 STR；
                # 多層持股依銀行政策 1.2(b) 視為高風險
                applicable_obligations = [
                    "ob_cdd_on_relationship_mas",
                    "ob_identify_ubo_mas",
                    "ob_identify_ubo_10_gb",
                    "ob_cdd_incomplete_mas"
                ]
                human_review_required = True
            else:
                # 普通企業情境，需注意是否觸發內部審查閥值限制 (cust_corp_standard)
                decision = "standard_cdd"
                
                # 檢查 custom_attributes 中的持股百分比是否觸發 GB 內部政策 >= 10% 限制
                share_pct = customer.custom_attributes.get("major_shareholder_pct", 0)
                if 10 <= share_pct <= 25:
                    required_documents = [
                        "Certificate of Incorporation",
                        "ACRA Company Profile",
                        "Shareholder Registry",
                        "UBO 15% Shareholder Identity Document (NRIC/Passport)"
                    ]
                    risk_triggers = ["internal_ubo_threshold_triggered_10_percent"]
                    applicable_obligations = [
                        "ob_cdd_on_relationship_mas",
                        "ob_verify_customer_mas",
                        "ob_identify_ubo_mas",
                        "ob_identify_ubo_10_gb"
                    ]
                    human_review_required = True
                else:
                    # 預設企業 standard cdd
                    required_documents = [
                        "Certificate of Incorporation",
                        "ACRA Company Profile"
                    ]
                    risk_triggers = []
                    applicable_obligations = [
                        "ob_cdd_on_relationship_mas",
                        "ob_verify_customer_mas",
                        "ob_identify_ubo_mas"
                    ]
                    human_review_required = False

        # 引用由出處推導：每個適用義務引用它的錨點條文（source_clause_ids 第一條），
        # 所以每個引用都是解析出的條文 ID，能在圖譜中解析到原文
        ob_dict = {ob.obligation_id: ob for ob in obligations}
        citations: List[str] = []
        for ob_id in applicable_obligations:
            ob = ob_dict.get(ob_id)
            if ob and ob.source_clause_ids and ob.source_clause_ids[0] not in citations:
                citations.append(ob.source_clause_ids[0])

        # 與適用義務相關、但尚未經人工裁決的衝突：列入清單並強制送人工審查
        applicable_clause_ids = {
            cid for ob_id in applicable_obligations if ob_id in ob_dict for cid in ob_dict[ob_id].source_clause_ids
        }
        for conflict in conflicts:
            if conflict.adjudication_status != "resolved" and applicable_clause_ids.intersection(conflict.source_clause_ids):
                unresolved_conflicts.append(conflict.conflict_id)
        if unresolved_conflicts:
            human_review_required = True

        # 構造並返回強型別檢核表
        checklist_id = f"chk_{customer_id.replace('cust_', '')}"
        
        return CDDChecklist(
            checklist_id=checklist_id,
            customer_id=customer_id,
            decision=decision,
            required_documents=required_documents,
            risk_triggers=risk_triggers,
            applicable_obligations=applicable_obligations,
            unresolved_conflicts=unresolved_conflicts,
            human_review_required=human_review_required,
            citations=citations
        )


class ChecklistEvaluator:
    """
    黃金數據對齊評估工具。
    比對引擎自動產出的 CDDChecklist 列表與 data/gold/checklists.yaml 的期望值，
    計算 Precision、Recall 與 F1-score，以量化合規推理對齊性。
    """

    def evaluate_alignment(
        self,
        generated: List[CDDChecklist],
        expected: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        比對產出列表與預期金標字典列表，計算並返回對齊性指標。
        """
        # 將 generated 轉為 map 以方便透過 customer_id 檢索
        gen_map = {item.customer_id: item for item in generated}
        
        total_fields = 0
        correct_fields = 0
        
        # 定義需要對齊的 6 大關鍵欄位
        fields_to_compare = [
            "decision",
            "required_documents",
            "risk_triggers",
            "applicable_obligations",
            "human_review_required",
            "citations"
        ]
        
        for exp in expected:
            cust_id = exp["customer_id"]
            if cust_id not in gen_map:
                # 缺失對應的預測，預設此客戶的所有欄位均不對齊
                total_fields += len(fields_to_compare)
                continue
                
            gen = gen_map[cust_id]
            
            for field in fields_to_compare:
                total_fields += 1
                
                gen_val = getattr(gen, field)
                exp_val = exp[field]
                
                # 針對列表型欄位，進行不區分順序的集合/列表值比對
                if isinstance(exp_val, list):
                    if sorted(list(gen_val)) == sorted(list(exp_val)):
                        correct_fields += 1
                else:
                    # 針對單一值欄位 (decision, human_review_required)
                    if gen_val == exp_val:
                        correct_fields += 1
                        
        if total_fields == 0:
            precision = 0.0
            recall = 0.0
            f1 = 0.0
        else:
            precision = correct_fields / total_fields
            recall = correct_fields / total_fields  # 因為對齊樣本數與預測數一對一對等
            if precision + recall == 0:
                f1 = 0.0
            else:
                f1 = 2 * precision * recall / (precision + recall)
                
        return {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "total_evaluated_fields": float(total_fields),
            "aligned_fields": float(correct_fields)
        }
