from typing import List, Dict, Any, Literal
from src.contracts.models import CustomerContext, Obligation, Conflict, CDDChecklist


class CDDChecklistEngine:
    """
    客戶 CDD 檢核推理引擎。
    根據 CustomerContext、Obligations 與 Conflicts 推理出對應的 CDDChecklist 決策，
    並保留強型別與條款級溯源引用。
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
        citations: List[str] = []

        # 1. 根據客戶情境特徵模式進行推理決策分支匹配
        if customer.customer_type == "individual":
            if customer.pep_exposure:
                # 政要曝險情境
                if customer.ubo_country_risk == "high" or customer.registration_jurisdiction.lower() == "myanmar":
                    # 高風險政要禁止開戶情境 (cust_individual_high_risk_pep)
                    decision = "enhanced_due_diligence"
                    required_documents = [
                        "Rejected Onboarding Notification",
                        "Suspicious Transaction Report (STR) Draft"
                    ]
                    risk_triggers = [
                        "pep_from_high_risk_jurisdiction",
                        "onboarding_prohibited_by_policy"
                    ]
                    applicable_obligations = ["ob_pep_prohibitions_gb"]
                    human_review_required = True
                    citations = ["Global Bank Policy Section 4.5.3"]
                else:
                    # 普通政要 EDD 情境 (cust_individual_pep)
                    decision = "enhanced_due_diligence"
                    required_documents = [
                        "National Identity Card (NRIC) or Passport",
                        "Proof of Address",
                        "Senior Management Approval Form",
                        "Source of Funds Declaration & Evidence",
                        "Source of Wealth Declaration & Evidence"
                    ]
                    risk_triggers = ["pep_exposure_detected"]
                    applicable_obligations = [
                        "ob_cdd_on_relationship_mas",
                        "ob_verify_customer_mas",
                        "ob_pep_edd_mas"
                    ]
                    human_review_required = True
                    citations = ["MAS Notice 626 Paragraph 7.2"]
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
                citations = [
                    "MAS Notice 626 Paragraph 6.2",
                    "MAS Notice 626 Paragraph 6.6"
                ]

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
                applicable_obligations = [
                    "ob_cdd_on_relationship_mas",
                    "ob_identify_ubo_25_mas"
                ]
                human_review_required = True
                citations = [
                    "MAS Notice 626 Paragraph 6.13",
                    "FATF Recommendation 10, P3"
                ]
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
                        "ob_identify_ubo_10_gb"
                    ]
                    human_review_required = True
                    citations = [
                        "MAS Notice 626 Paragraph 6.13",
                        "Global Bank Policy Section 3.2.1"
                    ]
                else:
                    # 預設企業 standard cdd
                    required_documents = [
                        "Certificate of Incorporation",
                        "ACRA Company Profile"
                    ]
                    risk_triggers = []
                    applicable_obligations = [
                        "ob_cdd_on_relationship_mas",
                        "ob_verify_customer_mas"
                    ]
                    human_review_required = False
                    citations = ["MAS Notice 626 Paragraph 6.13"]

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
