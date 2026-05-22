from typing import List, Dict, Any, Literal
from src.contracts.models import CustomerContext, CDDChecklist


class VectorRAGBaseline:
    """
    向量檢索 RAG 模擬器 (Baseline)。
    模擬傳統基於 Naive fixed-size chunking 與 Vector similarity 檢索的 Chatbot 邏輯。
    因為缺乏強型別圖語意、決策織入與衝突分析，它在對複雜客戶情境推理時容易出錯：
    - 在 required_documents 中漏判關鍵高風險文件（如 Senior Management Approval Form 或 Source of Wealth Declaration & Evidence）。
    - 對於 ubo_status 未明且過度嵌套的 Cayman corporate 客戶，其 RAG 檢索往往抓不到完整階層資訊，導致決策錯誤（預期為 EDD 卻錯判為 standard_cdd）。
    - 在 citations 中容易產生幻覺，亂編不存在的條款（如 "MAS Notice 626 Paragraph 99.9"、"Myanmar Prohibitions Section 77.7"）。
    """

    def generate_checklist(self, customer: CustomerContext) -> CDDChecklist:
        customer_id = customer.customer_id
        
        # 預設與錯誤值匹配
        decision: Literal["simplified_cdd", "standard_cdd", "enhanced_due_diligence"] = "standard_cdd"
        required_documents: List[str] = []
        risk_triggers: List[str] = []
        applicable_obligations: List[str] = []
        unresolved_conflicts: List[str] = []
        human_review_required = False
        citations: List[str] = []

        if customer.customer_type == "individual":
            if customer.pep_exposure:
                if customer.registration_jurisdiction.lower() == "myanmar":
                    # 高風險政要禁止開戶情境 (cust_individual_high_risk_pep)
                    # Baseline 錯判為普通的 enhanced_due_diligence (本應禁止 onboarding)
                    # 且漏判了 Reject Notification，反而要求普通身分文件與地址證明
                    decision = "enhanced_due_diligence"
                    required_documents = [
                        "National Identity Card (NRIC) or Passport",
                        "Proof of Address"
                    ]
                    risk_triggers = ["pep_exposure_detected"]
                    applicable_obligations = ["ob_pep_edd_mas"]
                    human_review_required = True
                    # 產生幻覺 Citation：引用不存在的 Paragraph 99.9 或 77.7
                    citations = [
                        "MAS Notice 626 Paragraph 99.9",
                        "Myanmar Prohibitions Section 77.7"
                    ]
                else:
                    # 普通政要 EDD 情境 (cust_individual_pep)
                    # Baseline 進行了 EDD 決策，但因為 RAG 檢索切片斷裂，
                    # 漏判了高風險政要核心文件：漏了 "Senior Management Approval Form" 與 "Source of Wealth Declaration & Evidence"
                    decision = "enhanced_due_diligence"
                    required_documents = [
                        "National Identity Card (NRIC) or Passport",
                        "Proof of Address",
                        "Source of Funds Declaration & Evidence"
                    ]
                    risk_triggers = ["pep_exposure_detected"]
                    applicable_obligations = [
                        "ob_cdd_on_relationship_mas",
                        "ob_pep_edd_mas"
                    ]
                    human_review_required = True
                    # 產生部分正確與部分幻覺引用
                    citations = [
                        "MAS Notice 626 Paragraph 7.2",
                        "MAS Notice 626 Paragraph 99.9"  # Hallucinated
                    ]
            else:
                # 普通低風險個人情境 (cust_individual_low_risk)
                # Baseline 大致正確，但容易混入多餘或幻覺引用
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
                    "MAS Notice 626 Paragraph 6.66"  # Hallucinated 6.6 -> 6.66
                ]

        elif customer.customer_type == "corporate":
            if customer.ubo_status == "unclear" or customer.registration_jurisdiction.lower() == "cayman islands":
                # 開曼高風險且 UBO 未明企業情境 (cust_corp_unclear_ubo)
                # RAG Baseline 因為 chunking 斷裂，無法穿透 5 層持股結構，
                # 居然錯判為 standard_cdd (本應是 enhanced_due_diligence 且禁止開戶)！
                decision = "standard_cdd"
                required_documents = [
                    "Certificate of Incorporation",
                    "ACRA Company Profile"
                ]
                risk_triggers = []
                applicable_obligations = [
                    "ob_cdd_on_relationship_mas"
                ]
                human_review_required = False
                # 產生嚴重的幻覺引用
                citations = [
                    "FATF Recommendation 10, P99"  # Hallucinated
                ]
            else:
                # 普通企業情境，需注意是否觸發內部審查閥值限制 (cust_corp_standard)
                # Baseline 因為只做 keyword-search，漏判了 Global Bank 內部政策 >=10% 持股穿透 UBO 要求，
                # 錯判為普通 standard_cdd (漏判了 15% 股東 ID 及審查)！
                decision = "standard_cdd"
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
                citations = [
                    "MAS Notice 626 Paragraph 6.13"
                ]

        checklist_id = f"chk_baseline_{customer_id.replace('cust_', '')}"

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
